#!/usr/bin/env python3
"""Print the generated disassembly around a ROM address: asmat.py ADDR [LINES]"""
import re
import sys

from romlib import ROOT

addr = int(sys.argv[1], 16)
n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
lines = open(ROOT + "/build/asm/code.s").read().split("\n")
best = None
for i, ln in enumerate(lines):
    m = re.match(r"^(?:\w+): @ 0x([0-9A-F]{8})|^_([0-9A-F]{8}):", ln)
    if m:
        a = int(m.group(1) or m.group(2), 16)
        if a <= addr:
            best = i
        else:
            break
# back up to the containing function start
i = best
while i > 0 and "func_start" not in lines[i]:
    i -= 1
print("\n".join(lines[i:max(best + n, i + n)]))
