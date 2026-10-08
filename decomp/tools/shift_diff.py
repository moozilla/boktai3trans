#!/usr/bin/env python3
"""Compare harness coverage of the base ROM and a shifted build.

  shift_diff.py ORIG_DIR SHIFT_DIR SHIFT [CODE_END]

Reports code executed in only one of the runs, and data reads in the shifted
run that do not correspond (after subtracting SHIFT) to bytes read in the
original run -- both point at a missed or bogus pointer.
"""
import sys

import numpy as np

from coverage import runs

CODE_END = 0x24DAFA


def main():
    od, sd, sh = sys.argv[1], sys.argv[2], int(sys.argv[3], 0)
    o = np.fromfile(od + "/total.exec", dtype=np.uint8)
    s = np.fromfile(sd + "/total.exec", dtype=np.uint8)
    for name, arr in (("only in original", (o != 0) & (s == 0)), ("only in shifted", (s != 0) & (o == 0))):
        rs = runs(arr)
        print(f"code {name}: {len(rs)} runs", [(hex(0x08000000 + 2 * a), 2 * (b - a)) for a, b in rs[:10]])
    o = np.fromfile(od + "/total.read", dtype="<u4")
    s = np.fromfile(sd + "/total.read", dtype="<u4")
    sm = np.zeros_like(s)
    sm[:CODE_END] = s[:CODE_END]
    sm[CODE_END:len(s) - sh] = s[CODE_END + sh:]
    bad = (sm != 0) & (o == 0)
    bad[:CODE_END] = False
    rs = runs(bad)
    print(f"unexpected data reads in shifted run: {len(rs)} ranges")
    for a, b in rs[:20]:
        print(f"  orig {0x08000000 + a:08X}+{b - a:#x} reader {sm[a]:08X}")
    gap = np.flatnonzero(s[CODE_END:CODE_END + sh])
    if len(gap):
        print(f"reads inside the inserted gap: {len(gap)}, first reader {s[CODE_END + gap[0]]:08X}")


if __name__ == "__main__":
    main()
