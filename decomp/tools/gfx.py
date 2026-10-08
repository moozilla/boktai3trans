#!/usr/bin/env python3
"""Render ROM graphics to PNG for inspection.

  gfx.py tiles ADDR COUNT OUT.png [--cols N] [--pal ADDR | --palfile F --palidx N] [--8bpp]
  gfx.py glyphs ADDR COUNT W H OUT.png      fonts stored as consecutive WxH glyphs
                                            (each glyph = column-major 8x8 tiles? see --order)
Defaults to a grayscale palette.  Output goes wherever you say; keep it out
of git (extracted/ is ignored).
"""
import argparse
import struct

from PIL import Image

from romlib import load_rom, off


def gray16():
    return [(i * 17, i * 17, i * 17) for i in range(16)]


def bgr555(v):
    return ((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31)


def read_pal(data, o, n=16):
    return [bgr555(struct.unpack_from("<H", data, o + 2 * i)[0]) for i in range(n)]


def tile4(data, o):
    px = []
    for y in range(8):
        row = []
        for x in range(4):
            v = data[o + y * 4 + x]
            row += [v & 15, v >> 4]
        px.append(row)
    return px


def tile8(data, o):
    return [[data[o + y * 8 + x] for x in range(8)] for y in range(8)]


def render_tiles(data, o, count, cols, pal, bpp8=False):
    rows = (count + cols - 1) // cols
    img = Image.new("RGB", (cols * 8, rows * 8))
    tsz = 64 if bpp8 else 32
    for t in range(count):
        px = (tile8 if bpp8 else tile4)(data, o + t * tsz)
        for y in range(8):
            for x in range(8):
                img.putpixel((t % cols * 8 + x, t // cols * 8 + y), pal[px[y][x] % len(pal)])
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["tiles", "glyphs"])
    ap.add_argument("addr", type=lambda s: int(s, 16))
    ap.add_argument("count", type=int)
    ap.add_argument("rest", nargs="+")
    ap.add_argument("--cols", type=int, default=16)
    ap.add_argument("--pal", type=lambda s: int(s, 16))
    ap.add_argument("--palfile")
    ap.add_argument("--palidx", type=int, default=0)
    ap.add_argument("--8bpp", dest="bpp8", action="store_true")
    a = ap.parse_args()
    rom = load_rom()
    if a.pal is not None:
        pal = read_pal(rom, off(a.pal), 256 if a.bpp8 else 16)
    elif a.palfile:
        pal = read_pal(open(a.palfile, "rb").read(), a.palidx * 32, 256 if a.bpp8 else 16)
    else:
        pal = gray16() if not a.bpp8 else [(i, i, i) for i in range(256)]
    o = off(a.addr)
    if a.mode == "tiles":
        render_tiles(rom, o, a.count, a.cols, pal, a.bpp8).save(a.rest[0])
    else:
        w, h, out = int(a.rest[0]), int(a.rest[1]), a.rest[2]
        tw, th = w // 8, h // 8
        per = tw * th
        cols = a.cols
        rows = (a.count + cols - 1) // cols
        img = Image.new("RGB", (cols * w, rows * h))
        for g in range(a.count):
            for t in range(per):
                # glyph tiles are stored row-major within the glyph
                tx, ty = t % tw, t // tw
                px = tile4(rom, o + (g * per + t) * 32)
                for y in range(8):
                    for x in range(8):
                        img.putpixel((g % cols * w + tx * 8 + x, g // cols * h + ty * 8 + y), pal[px[y][x]])
        img.save(out)


if __name__ == "__main__":
    main()
