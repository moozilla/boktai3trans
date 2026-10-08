#!/usr/bin/env python3
"""Make the generated disassembly shiftable.

Reads build/asm/code.s (gbadisasm output) and the base ROM, and writes:

  build/asm/code_sym.s   code with every ROM-pointer literal and every
                         pointer inside embedded data blocks replaced by a
                         symbol expression
  build/asm/data.s       the data region (after the code) as labeled
                         .incbin slices with symbolic pointer words

A word is treated as a ROM pointer when it is 4-byte aligned, points inside
the used ROM, and either sits in a run of at least two pointer-like words,
or points at an address that something else already references.  Pointer
detection is heuristic: the emulator shift test (tools/shift_test.sh) is the
check that it found all of them.

Labels: names from symbols/data.csv and symbols/functions.csv win; otherwise
gbadisasm's sub_XXXXXXXX / _XXXXXXXX code labels; otherwise data labels are
named gUnk_XXXXXXXX (address in the original ROM).
"""
import bisect
import csv
import os
import re
import sys

from romlib import ROOT, load_rom, u32

ROM_BASE = 0x08000000
THUMB_FUNCS = set()
ALIASES = set()
USED_END = 0x08E88144 + 1   # last non-zero byte + 1
CODE_END = 0x0824DAFA

LABEL_RE = re.compile(r"^(sub_|_)([0-9A-F]{8}):")
FUNC_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*): @ 0x([0-9A-F]{8})")
POOL_RE = re.compile(r"^(\S+:\s*)?\.4byte 0x(08[0-9A-F]{6})\b")


def is_ptr(v):
    return ROM_BASE <= v < USED_END


def parse_code(path):
    """Return (lines, code_labels{addr:name}, byte_blocks[(line_start, line_end, addr)])."""
    lines = open(path).read().split("\n")
    labels = {}
    global THUMB_FUNCS
    THUMB_FUNCS = set(re.findall(r"thumb_func_start (\S+)", "\n".join(lines)))
    blocks = []
    cur_addr = None
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = FUNC_RE.match(ln)
        if m:
            labels[int(m.group(2), 16)] = m.group(1)
            cur_addr = int(m.group(2), 16)
        else:
            m = LABEL_RE.match(ln)
            if m:
                a = int(m.group(2), 16)
                labels.setdefault(a, m.group(1) + m.group(2))
                cur_addr = a
                # data block directly following a label?
                rest = ln[m.end():].strip()
                j = i + 1
                if rest.startswith(".byte") or (not rest and j < len(lines) and lines[j].strip().startswith(".byte")):
                    start = i
                    n = 0
                    k = i
                    if rest.startswith(".byte"):
                        n += rest.count(",") + 1
                        k = i + 1
                    else:
                        k = j
                    while k < len(lines) and lines[k].strip().startswith(".byte"):
                        n += lines[k].count(",") + 1
                        k += 1
                    blocks.append((start, k, a, n))
                    i = k
                    continue
        i += 1
    return lines, labels, blocks


def main():
    rom = load_rom()
    code_path = os.path.join(ROOT, "build", "asm", "code.s")
    lines, code_labels, blocks = parse_code(code_path)

    # ---- collect referenced addresses ------------------------------------
    refs = set()
    for ln in lines:
        m = POOL_RE.match(ln.strip())
        if m:
            refs.add(int(m.group(2), 16))
    named = {}
    for fn in ("data.csv", "functions.csv"):
        p = os.path.join(ROOT, "symbols", fn)
        if os.path.exists(p):
            for r in csv.DictReader(open(p)):
                named[int(r["addr"], 16)] = r["name"]
                if fn == "data.csv":
                    refs.add(int(r["addr"], 16))

    # Candidate pointer words: in the data region, and in code-region data blocks.
    scan_ranges = [((CODE_END + 3) & ~3, USED_END)]
    for (_, _, a, n) in blocks:
        scan_ranges.append((a, a + n))
    cand = {}
    for s, e in scan_ranges:
        o = (s + 3) & ~3
        while o + 4 <= e:
            v = u32(rom, o - ROM_BASE)
            if is_ptr(v):
                cand[o] = v
            o += 4
    accepted = {}
    for o, v in cand.items():
        if (o - 4) in cand or (o + 4) in cand:
            accepted[o] = v
    # Pointer locations confirmed at runtime (word loads seen by the emulator
    # harness, see tools/runtime_ptrs.py) are always accepted.
    forced = set()
    p = os.path.join(ROOT, "symbols", "pointers.txt")
    if os.path.exists(p):
        for ln in open(p):
            ln = ln.split("#")[0].strip()
            if ln:
                o = int(ln, 16)
                accepted[o] = u32(rom, o - ROM_BASE)
                forced.add(o)
    # Words inside data blocks embedded in the code region are mostly literal
    # pools and jump tables: accept them.  Anywhere: accept odd values that
    # point exactly at a known Thumb function.
    in_code_block = set()
    for (_, _, a, n) in blocks:
        for o in range((a + 3) & ~3, a + n - 3, 4):
            in_code_block.add(o)
    for o, v in cand.items():
        if o in in_code_block or (v & 1 and (v & ~1) in code_labels and v < CODE_END):
            accepted[o] = v
    rejected = set()
    if os.environ.get("ACCEPT_ALL", "1") == "1":
        # Default: every aligned pointer-like word in data is a pointer, except
        # inside ranges listed in symbols/nonpointer_ranges.txt (graphics, PCM,
        # text...).  False positives only matter when data moves, and the
        # shift test catches them.
        excl = []
        for p in (os.path.join(ROOT, "symbols", "nonpointer_ranges.txt"),
                  os.path.join(ROOT, "symbols", "nonpointer_runtime.txt")):
            if not os.path.exists(p):
                continue
            for ln in open(p):
                ln = ln.split("#")[0].split()
                if len(ln) >= 2:
                    excl.append((int(ln[0], 16), int(ln[1], 16), ln[2] if len(ln) > 2 else "never"))

        excl.sort()
        excl_starts = [e[0] for e in excl]

        def range_mode(o):
            i = bisect.bisect_right(excl_starts, o) - 1
            # ranges may nest (manual + runtime); check a few predecessors
            for j in range(i, max(i - 4, -1), -1):
                s0, e0, m = excl[j]
                if s0 <= o < e0:
                    return m
            return None

        def word(o):
            return u32(rom, o - ROM_BASE)

        def table_shaped(o):
            for d in (4, -4):
                n = o + d
                if n in cand:
                    return True
                if word(n) == 0 and (n + d) in cand:
                    return True
            return False

        rejected = set()
        for o, v in cand.items():
            mode = range_mode(o)
            if mode is not None and not (mode == "tables" and table_shaped(o)) and o not in forced:
                rejected.add(o)
            if mode is None or (mode == "tables" and table_shaped(o)):
                accepted[o] = v
            elif o in accepted and mode is not None and o not in forced:
                del accepted[o]
    # isolated words: accept if they point at something already referenced
    changed = True
    while changed:
        changed = False
        targets = refs | {v & ~1 for v in accepted.values()}
        for o, v in cand.items():
            if o not in accepted and o not in rejected and (v & ~1) in targets:
                accepted[o] = v
                changed = True
    # Sound data: pointers found by walking MP2K songs (some are unaligned).
    import m4a
    snd = m4a.walk(rom)
    for t0, t1 in list(snd.track_extent.items()) + list(snd.samples.items()):
        for k in range(t0 & ~3, t1, 4):
            if k in accepted and k not in forced and k not in snd.ptr_locs:
                del accepted[k]
                rejected.add(k)
    for o, v in snd.ptr_locs.items():
        if is_ptr(v):
            for k in range(o - 3, o + 4):   # drop overlapping aligned guesses
                if k != o and k in accepted and k not in forced and abs(k - o) < 4:
                    del accepted[k]
            accepted[o] = v
    for v in accepted.values():
        refs.add(v & ~1 if v < CODE_END and v & 1 else v)

    # ---- label set ---------------------------------------------------------
    data_labels = {}
    for a in refs:
        if a >= CODE_END or a not in code_labels:
            if a < CODE_END and not any(b[2] <= a < b[2] + b[3] for b in blocks):
                continue  # inside instructions: leave as offset from a code label
            data_labels[a] = named.get(a, "gUnk_%08X" % a)
    all_labels = dict(code_labels)
    for a, n in named.items():
        if a in all_labels or a >= CODE_END:
            all_labels[a] = n if a >= CODE_END else all_labels[a]
    all_labels.update(data_labels)
    addrs = sorted(all_labels)

    def sym(v):
        """Symbol expression evaluating to ROM address v.

        A .thumb_func symbol already carries the Thumb bit when used as data,
        so offsets are computed against base|1 for those."""
        i = bisect.bisect_right(addrs, v & ~1) - 1
        if i < 0:
            return "0x%08X" % v
        base = addrs[i]
        expr = all_labels[base]
        if expr in THUMB_FUNCS:
            # R_ARM_ABS32 against a Thumb function ORs in bit 0, even with an
            # addend.  Odd targets: offset from the function; even targets:
            # use a plain (non-Thumb) alias label at the same address.
            if v & 1:
                d = (v & ~1) - base
            else:
                ALIASES.add(expr)
                expr = expr + "__addr"
                d = v - base
        else:
            d = v - base
        if d == 0:
            return expr
        return f"{expr}+{d:#x}" if d > 0 else f"{expr}-{-d:#x}"

    # ---- rewrite code ------------------------------------------------------
    out = []
    block_at = {b[0]: b for b in blocks}
    i = 0
    n_pool = 0
    while i < len(lines):
        if i in block_at:
            start, end, a, n = block_at[i]
            m = LABEL_RE.match(lines[i])
            out.append(lines[i][:m.end()])
            SKIP_FIRST.add(a)
            out += emit_bytes(rom, a, a + n, accepted, sym, data_labels)
            i = end
            continue
        ln = lines[i]
        m = POOL_RE.match(ln.strip())
        if m:
            v = int(m.group(2), 16)
            ln = ln.replace("0x" + m.group(2), sym(v), 1)
            n_pool += 1
        out.append(ln)
        i += 1
    # ---- data region -------------------------------------------------------
    data = ["@ generated by tools/symbolize.py"]
    data += emit_bytes(rom, CODE_END, len(rom) + ROM_BASE, accepted, sym, data_labels)
    open(os.path.join(ROOT, "build", "asm", "data.s"), "w").write("\n".join(data) + "\n")
    final = []
    for ln in out:
        final.append(ln)
        m = FUNC_RE.match(ln)
        if m and m.group(1) in ALIASES:
            final.append(f"{m.group(1)}__addr:")
    open(os.path.join(ROOT, "build", "asm", "code_sym.s"), "w").write("\n".join(final) + "\n")

    open(os.path.join(ROOT, "build", "asm", "pointers.txt"), "w").write(
        "".join("%08X\n" % o for o in sorted(accepted)))
    print(f"code pool pointers symbolized: {n_pool}; data pointers: {len(accepted)}; "
          f"data labels: {len(data_labels)}; code data blocks: {len(blocks)}", file=sys.stderr)


def emit_bytes(rom, s, e, accepted, sym, labels):
    """Emit [s, e) as labels + incbin slices + symbolic .4byte words."""
    out = []
    points = sorted({a for a in labels if s <= a < e} | {o for o in accepted if s <= o < e})
    pos = s
    for p in points:
        if p < pos:  # label inside a pointer word just emitted
            if p in labels:
                out.append(f"\t.set {labels[p]}, . - {pos - p}")
            continue
        if p > pos:
            out.append(f'\t.incbin "baserom.gba", {pos - ROM_BASE:#x}, {p - pos:#x}')
            pos = p
        if p in labels and not (p == s and labels is not None and out == [] and p in SKIP_FIRST):
            out.append(f"{labels[p]}:")
        if p in accepted:
            out.append(f"\t.4byte {sym(accepted[p])}")
            pos = p + 4
    if pos < e:
        out.append(f'\t.incbin "baserom.gba", {pos - ROM_BASE:#x}, {e - pos:#x}')
    return out


SKIP_FIRST = set()


if __name__ == "__main__":
    main()
