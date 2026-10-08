#!/usr/bin/env python3
"""Find where on-screen graphics come from in the ROM.

Given VRAM/IO/OAM dumps taken by the harness (`dump NAME_vram 6000000:18000`
etc.), decode the active BG layers and sprites, and look every displayed 4bpp
tile up in the ROM.  Prints, per layer, the ROM ranges that supplied tiles and
the number of tiles that were not found verbatim (rendered text, decompressed
or generated graphics).

  vram_map.py DUMP_PREFIX       e.g. /tmp/out/06_status
"""
import struct
import sys
from collections import defaultdict

import numpy as np

from romlib import load_rom

_index = None


def _hash_words(w):
    h = np.zeros(len(w) - 7, dtype=np.uint64)
    for k in range(8):
        h = (h * np.uint64(0x100000001B3)) ^ w[k:len(w) - 7 + k].astype(np.uint64)
    return h


def rom_index(rom):
    global _index
    if _index is None:
        w = np.frombuffer(rom, dtype="<u4")
        h = _hash_words(w)
        order = np.argsort(h, kind="stable")
        _index = (h[order], order)
    return _index


def find_tile(rom, tile):
    hs, order = rom_index(rom)
    w = np.frombuffer(tile, dtype="<u4")
    h = _hash_words(np.concatenate([w, np.zeros(0, dtype="<u4")]))[0]
    i = np.searchsorted(hs, h)
    out = []
    while i < len(hs) and hs[i] == h:
        o = int(order[i]) * 4
        if rom[o:o + 32] == tile:
            out.append(o)
        i += 1
    return out


def summarize(rom, label, tiles):
    """tiles: list of 32-byte tile bytes (unique)."""
    found = defaultdict(int)
    missing = 0
    blank = 0
    all_locs = []
    weight = defaultdict(float)
    for t in tiles:
        if t == bytes(32):
            blank += 1
            continue
        locs = find_tile(rom, t)
        if not locs:
            missing += 1
            continue
        all_locs.append(locs)
        for o in locs:
            weight[o >> 12] += 1 / len(locs)
    # A tile can appear verbatim in several places; attribute it to the
    # location in the 4KB bucket that supplied the most tiles overall.
    for locs in all_locs:
        found[max(locs, key=lambda o: weight[o >> 12])] += 1
    # merge into ranges
    offs = sorted(found)
    ranges = []
    for o in offs:
        if ranges and o - ranges[-1][1] <= 0x400:
            ranges[-1][1] = o + 32
            ranges[-1][2] += 1
        else:
            ranges.append([o, o + 32, 1])
    print(f"  {label}: {len(tiles)} unique tiles, {blank} blank, {missing} not in ROM")
    for s, e, n in ranges:
        print(f"    ROM {0x08000000 + s:08X}-{0x08000000 + e:08X}  {n:4d} tiles")


def main():
    pre = sys.argv[1]
    rom = load_rom()
    vram = open(pre + "_vram.bin", "rb").read()
    io = open(pre + "_io.bin", "rb").read()
    oam = open(pre + "_oam.bin", "rb").read()
    dispcnt = struct.unpack_from("<H", io, 0)[0]
    mode = dispcnt & 7
    print(f"{pre}: DISPCNT={dispcnt:04X} mode {mode}")
    for bg in range(4):
        if not dispcnt & (0x100 << bg):
            continue
        cnt = struct.unpack_from("<H", io, 8 + 2 * bg)[0]
        charbase = ((cnt >> 2) & 3) * 0x4000
        screenbase = ((cnt >> 8) & 0x1F) * 0x800
        bpp8 = cnt & 0x80
        size = cnt >> 14
        if mode == 1 and bg == 2 or mode == 2 and bg >= 2:
            print(f"  BG{bg}: affine, skipped")
            continue
        nscreens = (1, 2, 2, 4)[size]
        entries = struct.unpack_from("<%dH" % (0x400 * nscreens), vram, screenbase)
        tsize = 64 if bpp8 else 32
        uniq = {}
        for e in entries:
            t = e & 0x3FF
            o = charbase + t * tsize
            if o + tsize <= 0x10000:
                uniq[t] = vram[o:o + tsize]
        if bpp8:
            tiles = list({v[:32] for v in uniq.values()} | {v[32:] for v in uniq.values()})
        else:
            tiles = list(set(uniq.values()))
        summarize(rom, f"BG{bg} char {charbase:04X} map {screenbase:04X} {'8bpp' if bpp8 else '4bpp'}", tiles)
    if dispcnt & 0x1000:
        tiles = set()
        sizes = [[(8, 8), (16, 16), (32, 32), (64, 64)], [(16, 8), (32, 8), (32, 16), (64, 32)],
                 [(8, 16), (8, 32), (16, 32), (32, 64)]]
        onedim = dispcnt & 0x40
        for i in range(128):
            a0, a1, a2 = struct.unpack_from("<3H", oam, i * 8)
            if a0 & 0x300 == 0x200:
                continue  # disabled
            shape = a0 >> 14
            if shape == 3:
                continue
            w, h = sizes[shape][a1 >> 14]
            bpp8 = a0 & 0x2000
            tile = a2 & 0x3FF
            n = (w // 8) * (h // 8)
            for k in range(n * (2 if bpp8 else 1)):
                if onedim:
                    idx = tile + k
                else:
                    tx, ty = k % (w // 8 * (2 if bpp8 else 1)), k // (w // 8 * (2 if bpp8 else 1))
                    idx = tile + ty * 32 + tx
                o = 0x10000 + (idx & 0x3FF) * 32
                tiles.add(vram[o:o + 32])
        summarize(rom, "OBJ", list(tiles))


if __name__ == "__main__":
    main()
