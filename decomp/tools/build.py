#!/usr/bin/env python3
"""Build the ROM from generated asm + decompiled C, and compare.

  build.py [--shift N] [--out build/boktai3.gba] [--no-compare]

Steps: split.py (cut asm around src/*.c units) -> compile C with agbcc ->
assemble segments + data -> link in ROM order -> objcopy -> SHA-1 check.
Unchanged inputs are not rebuilt (content hash).
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys

from romlib import BASEROM_SHA1, ROOT

TOOLS = os.path.join(ROOT, "build", "tools")
AGBCC = os.environ.get("AGBCC", os.path.join(TOOLS, "agbcc", "agbcc"))
AGBCC_INC = os.path.join(os.path.dirname(AGBCC), "ginclude")
AS = ["arm-none-eabi-as", "-mcpu=arm7tdmi", "-mthumb-interwork", "--no-warn"]
CFLAGS = ["-O2", "-mthumb-interwork", "-fhex-asm"]


def sh(cmd, **kw):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.stderr.write(r.stdout + r.stderr)
        sys.exit(f"failed: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    return r.stdout


def stamp_ok(obj, key):
    st = obj + ".hash"
    return os.path.exists(obj) and os.path.exists(st) and open(st).read() == key


def stamp(obj, key):
    open(obj + ".hash", "w").write(key)


def file_hash(*paths, extra=""):
    h = hashlib.sha1(extra.encode())
    for p in paths:
        h.update(open(os.path.join(ROOT, p), "rb").read())
    return h.hexdigest()


def build_asm(src, obj, defsym=None):
    key = file_hash(src, "asm/macros.inc", extra=str(defsym))
    if stamp_ok(os.path.join(ROOT, obj), key):
        return
    cmd = AS + ["-I", ".", "-o", obj, src]
    if defsym:
        cmd[1:1] = ["--defsym", defsym]
    sh(cmd)
    stamp(os.path.join(ROOT, obj), key)


def build_c(src, obj):
    deps = [src] + [os.path.join("include", f) for f in sorted(os.listdir(os.path.join(ROOT, "include")))
                    if f.endswith(".h")]
    key = file_hash(*deps, extra=" ".join(CFLAGS))
    if stamp_ok(os.path.join(ROOT, obj), key):
        return
    pre = sh(["cpp", "-P", "-nostdinc", "-undef", "-I", "include", "-iquote", ".", src])
    asm = subprocess.run([AGBCC] + CFLAGS + ["-o", "-"], input=pre, cwd=ROOT,
                         capture_output=True, text=True)
    if asm.returncode or "error" in asm.stderr:
        sys.stderr.write(asm.stderr)
        sys.exit(f"agbcc failed on {src}")
    s_path = os.path.join(ROOT, obj[:-2] + ".s")
    open(s_path, "w").write(asm.stdout + "\t.text\n\t.align\t2, 0\n")
    sh(AS + ["-o", obj, s_path])
    stamp(os.path.join(ROOT, obj), key)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shift", default=None)
    ap.add_argument("--out", default="build/boktai3.gba")
    ap.add_argument("--no-compare", action="store_true")
    a = ap.parse_args()
    sh([sys.executable, "tools/split.py"])
    units = [ln.split() for ln in open(os.path.join(ROOT, "build", "units.txt"))]
    objs = []
    for kind, path in units:
        if kind == "asm":
            obj = path[:-2] + ".o"
            build_asm(path, obj)
        else:
            obj = os.path.join("build", path[:-2] + ".o")
            os.makedirs(os.path.join(ROOT, os.path.dirname(obj)), exist_ok=True)
            build_c(path, obj)
        objs.append(obj)
    # data region: all labels global so code can reference them
    data_g = os.path.join(ROOT, "build", "asm", "data_g.s")
    data = open(os.path.join(ROOT, "build", "asm", "data.s")).read()
    labels = re.findall(r"^(\w+):", data, re.M) + re.findall(r"^\t\.set (\w+),", data, re.M)
    hdr = '\t.include "asm/macros.inc"\n\t.syntax unified\n\t.text\n'
    shift = "\t.ifdef SHIFT\n\t.space SHIFT\n\t.endif\n"
    new = hdr + "".join(f"\t.global {l}\n" for l in labels) + shift + data
    if not os.path.exists(data_g) or open(data_g).read() != new:
        open(data_g, "w").write(new)
    dobj = "build/asm/data_g.o" if not a.shift else "build/asm/data_shift.o"
    build_asm("build/asm/data_g.s", dobj, defsym=f"SHIFT={a.shift}" if a.shift else None)
    objs.append(dobj)

    # RAM symbols used by C (gUnk_02XXXXXX / gUnk_03XXXXXX style names)
    syms = set()
    for kind, path in units:
        if kind == "c":
            out = sh(["arm-none-eabi-nm", "-u", os.path.join("build", path[:-2] + ".o")])
            syms |= set(re.findall(r"\b(\w+_(0[23][0-9A-Fa-f]{6}))\b", out))
    ld = ["SECTIONS {", "  . = 0x08000000;", "  .text : {"]
    ld += [f"    {o}(.text)" for o in objs]
    ld += ["  }", "  /DISCARD/ : { *(.comment) *(.ARM.attributes) }", "}"]
    ld += [f"{name} = 0x{addr};" for name, addr in sorted(syms)]
    open(os.path.join(ROOT, "build", "link.ld"), "w").write("\n".join(ld) + "\n")
    elf = a.out[:-4] + ".elf"
    sh(["arm-none-eabi-ld", "-T", "build/link.ld", "-o", elf])
    sh(["arm-none-eabi-objcopy", "-O", "binary", "-j", ".text", elf, a.out])
    if a.shift:
        b = open(os.path.join(ROOT, a.out), "rb").read()
        if len(b) > 0x1000000 and not any(b[0x1000000:]):
            open(os.path.join(ROOT, a.out), "wb").write(b[:0x1000000])
    if a.no_compare or a.shift:
        return
    h = hashlib.sha1(open(os.path.join(ROOT, a.out), "rb").read()).hexdigest()
    if h != BASEROM_SHA1:
        base = open(os.path.join(ROOT, "baserom.gba"), "rb").read()
        new = open(os.path.join(ROOT, a.out), "rb").read()
        diff = next((i for i in range(min(len(base), len(new))) if base[i] != new[i]), None)
        sys.exit(f"{a.out}: MISMATCH (sha1 {h}); first difference at "
                 f"{0x08000000 + diff:#010x}" if diff is not None else f"{a.out}: MISMATCH (length)")
    print(f"{a.out}: OK")


if __name__ == "__main__":
    main()
