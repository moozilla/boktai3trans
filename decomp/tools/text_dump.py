#!/usr/bin/env python3
"""Dump the main script bank to text/script.jsonl.

The bank is a table of 9976 u32 offsets at 0x08D6B1F8, relative to the
text base 0x08D74DDC.  Bit 31 set = NUL-terminated text string; clear = a
binary record (script-engine data, e.g. region tables), whose extent runs to
the next entry.

Each output line is one JSON object:
  id      string number (what the game passes to Text_LookupString)
  addr    ROM address of the original string
  kind    "text" or "data"
  ja      original Japanese (decoded; see charmap.py), or hex for data
  en      English from the 2007-2015 translation (scriptEd/script.sjs)
  status  status letter from script.sjs (E=translated, C=check, H=hold, X=data, U=?)
"""
import argparse
import json
import os

from charmap import decode
from romlib import ROOT, load_rom, u32

PTR_TABLE = 0xD6B1F8
TEXT_BASE = 0xD74DDC
COUNT = 9976


def parse_sjs(path):
    raw = open(path, "rb").read().decode("cp932", errors="replace").replace("\r\n", "\n")
    out = {}
    cur = None
    for line in raw.split("\n"):
        if line.startswith("$") and "=====" in line:
            status = line[1]
            idx = int(line.split("=====")[1])
            cur = out[idx] = {"status": status, "lines": []}
        elif cur is not None and not line.startswith("//"):
            cur["lines"].append(line)
    for v in out.values():
        while v["lines"] and v["lines"][-1] == "":
            v["lines"].pop()
        v["en"] = "\n".join(v.pop("lines"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sjs", default=os.path.join(os.path.dirname(ROOT), "scriptEd", "script.sjs"))
    ap.add_argument("-o", "--out", default=os.path.join(ROOT, "text", "script.jsonl"))
    a = ap.parse_args()
    rom = load_rom()
    sjs = parse_sjs(a.sjs)
    ptrs = [u32(rom, PTR_TABLE + 4 * i) for i in range(COUNT)]
    offs = [TEXT_BASE + (p & 0x7FFFFFFF) for p in ptrs]
    with open(a.out, "w", encoding="utf-8") as f:
        for i, p in enumerate(ptrs):
            o = offs[i]
            rec = {"id": i, "addr": "%08X" % (0x08000000 + o)}
            if p >> 31:
                end = rom.index(b"\0", o)
                rec["kind"] = "text"
                rec["ja"] = decode(rom[o:end])
            else:
                end = offs[i + 1] if i + 1 < COUNT else rom.index(b"\0", o)
                rec["kind"] = "data"
                rec["ja"] = rom[o:end].hex()
            s = sjs.get(i)
            if s and rec["kind"] == "text":
                rec["en"] = s["en"]
            rec["status"] = s["status"] if s else None
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"wrote {COUNT} records to {a.out}")


if __name__ == "__main__":
    main()
