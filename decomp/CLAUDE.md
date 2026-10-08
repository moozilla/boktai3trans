# Working on the Boktai 3 decomp (notes for agents and humans)

Read `README.md` first. The ROM (`baserom.gba`, SHA-1 `2651c5e6…`) is never
committed, and neither is anything generated from it (`build/`, `extracted/`).

## Ground rules

* `make` must print `build/boktai3.gba: OK` before anything is committed.
  If C changes data layout or touches pointers, also run `make shifttest`.
* Matching means byte-identical. No hand-written instructions inside `asm()`
  to force a match. `INCLUDE_ASM` is the placeholder for unfinished functions.
* One translation unit per change/PR. A unit is a `src/*.c` file covering a
  **contiguous** run of functions in ROM order.
* Don't edit generated files (`build/asm/*`). Names go in
  `symbols/functions.csv` / `symbols/data.csv`; pointer facts go in
  `symbols/pointers.txt` / `symbols/nonpointer_*.txt`.
* Names need evidence. Put it in the csv `source`/`notes` columns: a caller,
  a data reference, an emulator observation, or a matching library. Use
  `confidence=low` for guesses.

## Decompiling a function

1. Look at it: `python3 tools/asmat.py 0811D14C 60`. Ghidra's pseudo-C, if
   you have the export (`tools/ghidra/README.md`), is a starting draft only.
2. Write C in the unit's file. Unfinished neighbours stay as
   `INCLUDE_ASM("asm/nonmatching", sub_XXXXXXXX);` so the unit stays contiguous.
3. `make`. On a mismatch it prints the first differing address. Compare with
   `arm-none-eabi-objdump -d build/src/<unit>.o` against `tools/asmat.py`.
4. Compiler facts: `agbcc -O2 -mthumb-interwork` (pret's agbcc). Leaf
   functions push `lr`, which agbcc does and old_agbcc doesn't. Typical agbcc
   tricks apply: declaration order changes register allocation, `do {} while`
   vs `for` changes loop shape, a temporary variable affects the order of
   `if`/`else` blocks.
5. Library code exists already. MP2K (`m4a`) functions match pokeemerald's
   `src/m4a.c` byte-for-byte (43 identified, see `symbols/functions.csv`),
   and `libagbsyscall` is standard. Use `tools/sigmatch.py OBJ.o` to find more
   library code (agb_flash, siirtc, libgcc/libc pieces).

## Mapping data

* Run the game headless: `tools/emu/harness baserom.gba tests/X.txt OUTDIR`
  (with `BOKTAI3_SAV=../ShinBok2.sav` for a late-game save). Commands are
  listed at the top of `tools/emu/harness.c`. `mark NAME` records coverage per
  segment; `dump`, `watch ADDR:LEN` and `shot` are available.
* `tools/coverage.py diff A.read B.read` lists what one screen reads that
  another doesn't. `tools/vram_map.py PREFIX` maps on-screen tiles to ROM.
* After new emulator runs, fold the evidence in:
  `python3 tools/runtime_ptrs.py RUN_DIR...`, then `make` and `make shifttest`.

## When the shift test fails

1. Dump RAM periodically on both ROMs (see `tools/ramdiff.py` docstring) and
   find the first word that differs by something other than the shift.
2. `watch` that address to find the instruction that writes it, then work
   back to the ROM data it came from.
3. The fix is almost always one of two things: data misread as a pointer
   (add a `nonpointer_ranges.txt` range or an emulator run that reads it), or
   a pointer the scan can't see (unaligned or in a structure; add it to
   `pointers.txt` or teach a walker like `tools/m4a.py`).
