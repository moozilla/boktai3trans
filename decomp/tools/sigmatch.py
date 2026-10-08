#!/usr/bin/env python3
"""Find library functions from a compiled object in the ROM.

  sigmatch.py OBJ.o [--csv]

For every global function in OBJ, its bytes (with relocated fields masked) are
searched in the code region.  Unique hits are printed as `addr,name` -- these
are both names and proof that the object's C source matches as-is.
"""
import re
import subprocess
import sys

from romlib import load_rom

CODE_END = 0x24DAFA


def main():
    obj = sys.argv[1]
    rom = load_rom()
    code = rom[:CODE_END]
    subprocess.run(["arm-none-eabi-objcopy", "-O", "binary", "-j", ".text", obj, "/tmp/claude-0/sig.bin"], check=True)
    text = open("/tmp/claude-0/sig.bin", "rb").read()
    syms = []
    for ln in subprocess.run(["arm-none-eabi-nm", "-S", "--defined-only", obj], capture_output=True, text=True).stdout.splitlines():
        p = ln.split()
        if len(p) == 4 and p[2] in "Tt":
            syms.append((int(p[0], 16) & ~1, int(p[1], 16), p[3]))
    masked = set()
    rel = subprocess.run(["arm-none-eabi-readelf", "-rW", obj], capture_output=True, text=True).stdout
    in_text = False
    for ln in rel.splitlines():
        if ln.startswith("Relocation section"):
            in_text = "'.rel.text'" in ln
            continue
        m = re.match(r"^([0-9a-f]{8})\s+[0-9a-f]+\s+(\S+)", ln)
        if m and in_text:
            off = int(m.group(1), 16)
            for k in range(4):
                masked.add(off + k)
    found = 0
    for start, size, name in sorted(syms):
        body = text[start:start + size]
        if size < 8:
            continue
        pat = b"".join(b"." if (start + i) in masked else re.escape(bytes([body[i]])) for i in range(size))
        hits = [m.start() for m in re.finditer(pat, code, re.S) if m.start() % 2 == 0]
        if len(hits) == 1:
            print(f"{0x08000000 + hits[0]:08X},{name},{size}")
            found += 1
        elif hits:
            print(f"# {name}: {len(hits)} hits", file=sys.stderr)
        else:
            print(f"# {name}: no match", file=sys.stderr)
    print(f"# {found}/{len(syms)} functions matched uniquely", file=sys.stderr)


if __name__ == "__main__":
    main()
