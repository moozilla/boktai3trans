# Boktai 3 (Shin Bokura no Taiyou: Gyakushuu no Sabata) — decompilation workspace

A from-scratch reverse-engineering setup for the Japanese ROM (`BOKTAI3`,
game code `U33J`), aimed at a full matching decompilation that the English
translation can then be built on.

**Status (first session):**

| | |
|---|---|
| Disassembly | 7,868 functions, reassembles **bit-identical** (`make compare`) |
| Shiftable | every ROM pointer is a symbol; all 13.7 MB of data can move. Moving it by 64 KiB plays **pixel-identical** in every scripted test (`make shifttest`) |
| Compiler | identified as **agbcc** (pret's GCC 2.95 GBA compiler), `-O2 -mthumb-interwork` |
| C pipeline | `src/*.c` → agbcc → spliced into the ROM in place of the asm; 4 functions matched so far |
| Text | 9,976-string script bank decoded, round-trips byte-exact, merged with the 2007 English (`text/script.jsonl`) |
| Sound | MP2K engine; 1,483 songs, 5,525 track streams, 81 voicegroups, 415 samples walked |
| Symbols | `symbols/` — named functions (incl. raphaelr's), data map, confirmed pointers |

See [docs/ROM_MAP.md](docs/ROM_MAP.md) for what lives where, and
[docs/FINDINGS.md](docs/FINDINGS.md) for engine notes.

## Setup

You need your own copy of the ROM:

```
baserom.gba   SHA-1 2651c5e6875ac60abff734510d152166d211c87c
```

Put it (or a symlink) at `decomp/baserom.gba`, or set `BOKTAI3_ROM`.
Nothing derived byte-for-byte from the ROM is committed: generated assembly,
extracted data and graphics all live under `build/` / `extracted/`.

System packages (Debian/Ubuntu):

```
apt install build-essential cmake binutils-arm-none-eabi libmgba-dev python3-numpy python3-pil
pip install capstone
make setup          # fetches + builds pinned gbadisasm, agbcc, armips, and the mGBA harness
```

## Building

```
make disasm         # generate build/asm/code.s (gbadisasm, ~18 min) and symbolize it
make                # split around src/*.c, compile C with agbcc, link, verify SHA-1
make shifttest      # move all data by 64 KiB and compare emulator screenshots
make text           # re-dump text/script.jsonl
```

## Layout

```
asm/          hand-written asm (macros, top-level ROM for the pure-asm build)
include/      C headers
src/          decompiled C, one file per contiguous run of functions
symbols/      functions.csv, data.csv  -- names (source of truth for labels)
              pointers.txt             -- ROM words proven to be pointers (emulator)
              nonpointer_*.txt         -- ranges proven/declared not to hold pointers
text/         script.jsonl: id, address, Japanese, English, status
tests/        input scripts for the emulator harness
tools/        everything that generates or checks the above
  disasm.py       run gbadisasm with seeds (BL targets, pointer-derived), iterate
  symbolize.py    make every ROM pointer symbolic; split data into labeled slices
  split.py        cut asm around C units; build.py compiles/links/compares
  m4a.py          MP2K sound walker (songs, tracks incl. unaligned GOTO/PATT, voices, samples)
  emu/harness.c   headless mGBA: scripted input, screenshots, code/data coverage,
                  word-load pointer evidence, RAM dumps, write watchpoints, fixed RTC
  runtime_ptrs.py turn harness evidence into symbols/pointers.txt + nonpointer_runtime.txt
  shift_test.sh   shiftability regression; ramdiff.py / shift_diff.py to debug it
  vram_map.py     which ROM bytes the tiles on screen came from
  text_dump.py, charmap.py   script bank codec
  gfx.py, lz77.py, coverage.py, asmat.py
```

## Decompiling a function

1. `python3 tools/asmat.py 08033568` shows the asm.
2. Write C in `src/<name>.c` (functions in a file must be contiguous, in ROM order).
   RAM globals can be referenced as `gUnk_0200XXXX`; the linker defines them.
3. `make` — prints `OK` or the first mismatching address.

Matching notes so far: plain `agbcc -O2 -mthumb-interwork` reproduces leaf
functions including the always-pushed `lr`; `old_agbcc` does not (it omits the
push in leaf functions). Rename a function by adding it to
`symbols/functions.csv` — no re-disassembly needed.

## How shiftability was proven

Pointer detection is heuristic (aligned words in ROM range, table shapes,
MP2K structure walking) plus evidence from the emulator: the harness records
which ROM words the program loads with `LDR`/`LDM` (pointers) versus words it
only reads as plain data (halfword loads, DMA, BIOS copies). Bulk-copy loops are
discounted. The shift test then moves all data and diffs screenshots; RAM
snapshots (`tools/ramdiff.py`) pinpoint the first divergence when it fails.

The tests so far cover boot/setup, title, new game + intro cutscene, a
late-game save, every pause-menu tab and some field play — about 6% of the
code. Areas no test reaches may still hide a bad pointer guess; extending
`tests/` with more of the game is the way to find them.
