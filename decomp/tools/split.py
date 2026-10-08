#!/usr/bin/env python3
"""Splice decompiled C into the build.

Scans src/**/*.c for function definitions.  Every C file is a "unit" that must
cover a contiguous run of functions in ROM order.  The generated code
(build/asm/code_sym.s) is cut around those functions into asm segments, and a
linker script places asm segments and C objects in ROM order:

  build/asm/seg_NNN.s        asm between C units (all labels made global)
  build/link.ld              link order + RAM/ROM symbol definitions
  build/units.txt            "asm build/asm/seg_000.s" / "c src/foo.c" lines

Function names resolve to addresses through gbadisasm's sub_XXXXXXXX naming or
symbols/functions.csv.
"""
import csv
import glob
import os
import re
import sys

from romlib import ROOT

FUNC_START = re.compile(r"^\t(?:thumb|arm|non_word_aligned_thumb)_func_start (\S+)")
FUNC_LABEL = re.compile(r"^(\w+): @ 0x([0-9A-F]{8})")
LABEL = re.compile(r"^(\w+):")
SET_LABEL = re.compile(r"^\t\.set (\w+),")
C_FUNC = re.compile(r"^(?!static\b)[A-Za-z_][\w \*]*?\b(\w+)\s*\([^;]*\)\s*$|^(?!static\b)[A-Za-z_][\w \*]*?\b(\w+)\s*\([^;]*\)\s*\{", re.M)


def c_functions(path):
    src = open(path).read()
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r"^#.*$", "", src, flags=re.M)
    names = []
    # a definition: identifier( ... ) followed (possibly after newline) by {
    for m in re.finditer(r"\b(\w+)\s*\(([^;{}()]|\([^()]*\))*\)\s*\{", src):
        name = m.group(1)
        if name in ("if", "for", "while", "switch", "return", "sizeof"):
            continue
        names.append(name)
    return names


def main():
    code = open(os.path.join(ROOT, "build", "asm", "code_sym.s")).read().split("\n")
    # function blocks: [start_line, end_line) per function, in order
    starts = [i for i, ln in enumerate(code) if FUNC_START.match(ln)]
    funcs = []
    for k, i in enumerate(starts):
        name = FUNC_START.match(code[i]).group(1)
        j = starts[k + 1] if k + 1 < len(starts) else len(code)
        addr = None
        m = FUNC_LABEL.match(code[i + 1]) if i + 1 < len(code) else None
        if m:
            addr = int(m.group(2), 16)
        nonword = "non_word_aligned" in code[i]
        funcs.append((name, addr, i, j, nonword))
    index = {f[0]: n for n, f in enumerate(funcs)}

    units = []  # (first_func_idx, last_func_idx, path)
    for path in sorted(glob.glob(os.path.join(ROOT, "src", "**", "*.c"), recursive=True)):
        rel = os.path.relpath(path, ROOT)
        names = c_functions(path)
        if not names:
            continue
        idx = []
        for n in names:
            if n not in index:
                sys.exit(f"{rel}: function {n} is not a known function start")
            idx.append(index[n])
        if idx != sorted(idx) or idx != list(range(idx[0], idx[0] + len(idx))):
            sys.exit(f"{rel}: functions must be contiguous and in ROM order "
                     f"(got {[funcs[i][0] for i in idx]})")
        if funcs[idx[0]][4]:
            sys.exit(f"{rel}: unit cannot start at a non-word-aligned function")
        units.append((idx[0], idx[-1], rel))
    units.sort()
    for a, b in zip(units, units[1:]):
        if a[1] >= b[0]:
            sys.exit(f"{a[2]} and {b[2]} overlap")

    header = ['\t.include "asm/macros.inc"', "\t.syntax unified", "\t.text"]
    out_units = []
    seg_no = 0
    line = 0

    def emit_seg(lo, hi):
        nonlocal seg_no
        body = code[lo:hi]
        if not any(l.strip() for l in body):
            return
        globs = set()
        for ln in body:
            m = LABEL.match(ln) or SET_LABEL.match(ln)
            if m:
                globs.add(m.group(1))
        path = os.path.join(ROOT, "build", "asm", f"seg_{seg_no:03d}.s")
        with open(path, "w") as f:
            f.write("\n".join(header) + "\n")
            f.write("".join(f"\t.global {g}\n" for g in sorted(globs)))
            f.write("\n".join(body) + "\n")
        out_units.append(("asm", os.path.relpath(path, ROOT)))
        seg_no += 1

    for first, last, rel in units:
        emit_seg(line, funcs[first][2])
        out_units.append(("c", rel))
        line = funcs[last][3]
    emit_seg(line, len(code))

    with open(os.path.join(ROOT, "build", "units.txt"), "w") as f:
        for kind, p in out_units:
            f.write(f"{kind} {p}\n")
    ndec = sum(b - a + 1 for a, b, _ in units)
    print(f"{len(units)} C units ({ndec} functions), {seg_no} asm segments", file=sys.stderr)


if __name__ == "__main__":
    main()
