#!/usr/bin/env python3
"""First RAM divergence between two harness runs that dumped rNNN_ew/rNNN_iw.

  ramdiff.py ORIG_DIR SHIFT_DIR [SHIFT]
Words where both values are ROM addresses differing by exactly SHIFT are
ignored (correctly moved pointers); the stack top is ignored.
"""
import glob
import sys

import numpy as np

od, sd = sys.argv[1], sys.argv[2]
sh = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x100
isrom = lambda v: 0x08000000 <= v < 0x0E000000
ks = sorted(set(f.split("/")[-1][:4] for f in glob.glob(od + "/r*_ew.bin")))
shown = 0
for k in ks:
    for reg, base in (("ew", 0x02000000), ("iw", 0x03000000)):
        a = np.fromfile(f"{od}/{k}_{reg}.bin", dtype="<u4")
        b = np.fromfile(f"{sd}/{k}_{reg}.bin", dtype="<u4")
        d = np.flatnonzero(a != b)
        real = [i for i in d if not (isrom(a[i]) and isrom(b[i]) and int(b[i]) - int(a[i]) == sh)
                and not (reg == "iw" and 4 * i >= 0x7C00)]
        if real:
            print(k, reg, len(real), [(hex(base + 4 * i), hex(a[i]), hex(b[i])) for i in real[:10]])
            shown += 1
    if shown >= 3:
        break
if not shown:
    print("no divergence")
