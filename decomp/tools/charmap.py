"""Boktai 3 text encoding.

Script text is a byte stream: 0x0A is newline, 0x20-0x7E are ASCII, and bytes
0x80-0x85 are lead bytes for a 2-byte code (0x8000-0x85FF) indexing the 16x16
kana/kanji font.  Strings are NUL-terminated.

The table comes from scriptEd/chartable.sjs.tbl (Shift-JIS encoded).  Codes
whose glyph is unknown or shared with another code are written as {XXXX} so
decoding always round-trips.
"""
import os
from collections import Counter

from romlib import ROOT

TBL = os.path.join(os.path.dirname(ROOT), "scriptEd", "chartable.sjs.tbl")


def _load():
    raw = open(TBL, "rb").read()
    ent = {}
    for line in raw.split(b"\r\n"):
        if not line:
            continue
        k, _, v = line.partition(b"=")
        code = int(k, 16)
        if code < 0x80:
            continue
        try:
            ent[code] = v.decode("cp932")
        except UnicodeDecodeError:
            pass
    dup = Counter(ent.values())
    dec = {c: s for c, s in ent.items()
           if len(s) == 1 and dup[s] == 1 and s not in "{}"}
    return dec


DECODE = _load()
ENCODE = {s: c for c, s in DECODE.items()}


def decode(bs):
    out = []
    i = 0
    while i < len(bs):
        x = bs[i]
        if 0x80 <= x <= 0x85 and i + 1 < len(bs):
            code = (x << 8) | bs[i + 1]
            out.append(DECODE.get(code, "{%04X}" % code))
            i += 2
        elif x == 0x0A or 0x20 <= x <= 0x7E and x not in (0x7B, 0x7D):
            out.append(chr(x))
            i += 1
        else:
            out.append("{%02X}" % x)
            i += 1
    return "".join(out)


def encode(s):
    out = bytearray()
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "{":
            j = s.index("}", i)
            h = s[i + 1:j]
            out += bytes.fromhex(h)
            i = j + 1
            continue
        if ch in ENCODE:
            c = ENCODE[ch]
            out += bytes([c >> 8, c & 0xFF])
        else:
            o = ord(ch)
            if not (o == 0x0A or 0x20 <= o <= 0x7E):
                raise ValueError(f"unencodable character {ch!r}")
            out.append(o)
        i += 1
    return bytes(out)
