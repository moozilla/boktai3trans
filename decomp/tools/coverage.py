#!/usr/bin/env python3
"""Summarize harness coverage files.

  coverage.py ranges FILE.read [--min N]     ROM ranges read, grouped by reader PC
  coverage.py exec FILE.exec                 executed ROM code ranges (Thumb/ARM)
  coverage.py diff A.read B.read             ranges read in A but never in B
"""
import sys

import numpy as np

ROM_SIZE = 0x1000000


def load_read(p):
    return np.fromfile(p, dtype="<u4", count=ROM_SIZE)


def runs(mask):
    """Yield (start, end) of True runs."""
    m = np.concatenate(([False], mask, [False])).astype(np.int8)
    d = np.diff(m)
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1)
    return list(zip(starts, ends))


def read_ranges(reader, gap=16, mask=None):
    """Merge read bytes into ranges (allowing small gaps); report dominant readers."""
    hit = reader != 0
    if mask is not None:
        hit &= mask
    out = []
    for s, e in runs(hit):
        if out and s - out[-1][1] <= gap:
            out[-1][1] = e
        else:
            out.append([s, e])
    res = []
    for s, e in out:
        pcs = reader[s:e]
        pcs = pcs[pcs != 0]
        u, c = np.unique(pcs, return_counts=True)
        top = sorted(zip(c, u), reverse=True)[:3]
        res.append((s, e, [(int(p), int(n)) for n, p in top]))
    return res


def main():
    cmd = sys.argv[1]
    if cmd in ("ranges", "diff"):
        r = load_read(sys.argv[2])
        mask = None
        if cmd == "diff":
            mask = load_read(sys.argv[3]) == 0
        minlen = 0
        if "--min" in sys.argv:
            minlen = int(sys.argv[sys.argv.index("--min") + 1])
        for s, e, top in read_ranges(r, mask=mask):
            if e - s < minlen:
                continue
            readers = " ".join("%08X(%d)" % (p & ~1, n) for p, n in top)
            print("%08X-%08X %7d  %s" % (0x08000000 + s, 0x08000000 + e, e - s, readers))
    elif cmd == "exec":
        x = np.fromfile(sys.argv[2], dtype=np.uint8)
        for bit, name in ((1, "thumb"), (2, "arm")):
            rs = runs((x & bit) != 0)
            print(f"{name}: {len(rs)} runs, {sum(e - s for s, e in rs) * 2} bytes")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
