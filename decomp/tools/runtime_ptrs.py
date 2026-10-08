#!/usr/bin/env python3
"""Merge emulator evidence into symbols/pointers.txt.

  runtime_ptrs.py RUN_DIR [RUN_DIR...]

Each RUN_DIR is a harness output directory with total.word32 (ROM words the
program loaded with LDR/LDM) and total.read (every ROM byte read, including by
DMA and BIOS copies).

  * words loaded with LDR/LDM that hold a ROM address -> symbols/pointers.txt
  * pointer-looking words that were read, but never with LDR/LDM (only by
    halfword/byte loads, DMA, CpuSet...) -> symbols/nonpointer_runtime.txt
    as merged ranges; the symbolizer treats those as plain data.
"""
import os
import sys

import numpy as np

from romlib import ROOT, load_rom

USED_END = 0x08E88145


def main():
    rom = load_rom()
    words = np.frombuffer(rom, dtype="<u4")
    seen = np.zeros(len(words), dtype=bool)
    read = np.zeros(len(rom), dtype=bool)
    isp = (words >= 0x08000000) & (words < USED_END)
    runs = []
    stats = {}
    for d in sys.argv[1:]:
        pcs = np.fromfile(os.path.join(d, "total.word32"), dtype="<u4")
        read |= np.fromfile(os.path.join(d, "total.read"), dtype="<u4") != 0
        runs.append(pcs)
        nz = pcs != 0
        u, inv, cnt = np.unique(pcs[nz], return_inverse=True, return_counts=True)
        k = np.bincount(inv, weights=isp[nz].astype(float), minlength=len(u))
        for p, c, kk in zip(u, cnt, k):
            t = stats.setdefault(int(p), [0, 0])
            t[0] += int(c)
            t[1] += kk
    # A PC that loads many words of which few look like pointers is a bulk
    # copy/decompression loop: its loads are not pointer evidence.
    copiers = {p for p, (c, k) in stats.items()
               if (c >= 200 and k / c < 0.05) or (p >> 24 == 3 and c >= 32 and k / c < 0.2)}
    for pcs in runs:
        seen |= (pcs != 0) & ~np.isin(pcs, list(copiers))
    print(f"ignoring {len(copiers)} bulk-copy PCs:", " ".join("%08X" % p for p in sorted(copiers)[:12]))
    locs = {0x08000000 + 4 * int(i) for i in np.flatnonzero(seen & isp)}
    path = os.path.join(ROOT, "symbols", "pointers.txt")
    old = set()
    if os.path.exists(path):
        for ln in open(path):
            ln = ln.split("#")[0].strip()
            if ln:
                old.add(int(ln, 16))
    allp = old | locs
    with open(path, "w") as f:
        f.write("# ROM locations confirmed (by emulator word loads) to hold pointers.\n")
        f.write("# Maintained by tools/runtime_ptrs.py; hand additions welcome.\n")
        for a in sorted(allp):
            f.write("%08X\n" % a)
    print(f"{len(locs)} from runs, {len(allp - old)} new, {len(allp)} total")

    # Negative evidence, accumulated across invocations.
    wread = read.reshape(-1, 4).any(axis=1)
    neg = wread & ~seen & isp
    neg[[(a - 0x08000000) // 4 for a in allp]] = False
    npath = os.path.join(ROOT, "symbols", "nonpointer_runtime.txt")
    negset = {0x08000000 + 4 * int(i) for i in np.flatnonzero(neg)}
    if os.path.exists(npath):
        for ln in open(npath):
            ln = ln.split("#")[0].split()
            if len(ln) == 2:
                negset |= set(range(int(ln[0], 16), int(ln[1], 16), 4))
    negset -= allp
    ranges = []
    for a in sorted(negset):
        if ranges and a - ranges[-1][1] <= 0:
            ranges[-1][1] = a + 4
        else:
            ranges.append([a, a + 4])
    with open(npath, "w") as f:
        f.write("# Pointer-looking words the game read only as plain data (never via LDR/LDM).\n")
        f.write("# start end -- maintained by tools/runtime_ptrs.py\n")
        for s0, e0 in ranges:
            f.write("%08X %08X\n" % (s0, e0))
    print(f"{len(negset)} words of negative evidence in {len(ranges)} ranges")


if __name__ == "__main__":
    main()
