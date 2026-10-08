# Engine findings

Notes from the first mapping pass. Addresses are ROM (`08xxxxxx`) unless
noted. "medium" means the name or role is inferred from coverage, not decoded.

## Toolchain

* Code is Thumb compiled with **agbcc**: returns via `pop {r0}; bx r0`
  (≈7,000 times) and `pop {r1}; bx r1` (≈3,700), very few `pop {pc}`. Leaf
  functions still push `lr`, which pret's `agbcc` reproduces and `old_agbcc`
  doesn't.
* Test functions matched instruction-for-instruction with `agbcc -O2 -mthumb-interwork`
  (`src/`). One switch (`sub_08032300`) didn't match on the first attempts,
  which is normal decomp work.
* Standard Nintendo SDK pieces: crt0 + `IntrMain` (ARM), `libagbsyscall`
  (`08248590`–`082485E8`), MP2K sound driver (`m4a`). These can be lifted
  from pret's existing decomps nearly verbatim.

## Text

* Script bank: 9,976 entries (`08D6B1F8` table → `08D74DDC` text). Bit 31
  of an entry marks text; entries without it are binary records (e.g. string
  9340 = region list used by the region-select screen).
* Encoding: `0x0A` newline, ASCII `0x20–0x7E`, lead bytes `0x80–0x85` + 1 byte
  for 1,536 kana/kanji glyphs (index = code − `0x8000`). NUL-terminated.
* Markup is inline ASCII parsed at runtime: `<PROC=n>`, `<LABEL=NAME>…</LABEL>`,
  `<END>`, `<WEIGHT>`, `<NAME>`, `<ALTER>…</ALTER>` (choices), `<EXTEND=n>`,
  `<VAR=n>`, `<LOCK=n>`, `<MOJISE=…>` (text sound), `<BIKE>`.
* Fonts are fixed-width tile fonts: 8×16 for ASCII, 16×16 for 2-byte codes.
  The 8×16 font already contains accented Latin glyphs past `0x9F`. Those
  byte values collide with the lead bytes, which is why the French translators
  use the `{1F}{xx}` escape. A variable-width font would be a code change in
  `Text_DrawGlyph` (`08218D1C`) and its callers.

## Event script VM

* Byte-coded, keyword-based VM: `Script_SeekToKeyword`, `Script_GetValue`,
  operand decoder `0821A6F0` (u8/u16/string-ref operands; string refs go
  through `Text_LookupString`).
* Bytecode at `08DD6B95`–`08E8755B`, ~0.7 MB. It embeds EUC-JP debug labels
  (`★★★ゲームスタート画面★★★` = "game start screen"), which will help name
  scenes.
* Absolute pointers occur only in pointer tables inside the region. Treating
  aligned words in the bytecode as pointers corrupts it, which was the first
  shift-test failure.

## Sound (MP2K / "Sappy")

* `SoundMainRAM` mixer copied to IWRAM `030035F0`. The song table at
  `0826456C` has 1,483 entries (BGM + SFX); there are 81 voicegroups and 415
  samples (3.2 MB).
* Track streams contain 5,611 **unaligned** absolute pointers
  (GOTO/PATT/REPT). A word-aligned scan can't find them, so `tools/m4a.py`
  walks the streams instead. Standard tools (agbplay, sappy2midi) should work
  on this data.

## Graphics

* Mostly uncompressed 4bpp tiles; LZ77 (BIOS `LZ77UnCompWram`) is used for
  some BG data in `0870`–`0881`.
* Pause menu: BG tiles at `0870A230`, one `0x200`-byte tilemap per screen from
  `0870C238`. Menu titles and button labels are **sprites** (OBJ) assembled
  from small tile pieces (`08BE2F04`, `08C11880`, `08C15880`). This is what the
  2007 `menu_titles.ips` work and the later status-screen work modify.
* `tools/vram_map.py` maps every tile on a captured screen back to its ROM
  source. That's the fastest way to find any graphic that needs translating.

## Hardware

* RTC (Boktai's clock) and the solar sensor via cartridge GPIO. The harness
  pins the RTC to a fixed time for deterministic runs; solar level is
  scriptable (`lux N`).
* Save: 8 KB EEPROM. **The ROM must stay ≤ 16 MiB** or emulators/hardware map
  EEPROM differently; `build.py` trims trailing padding for shifted builds.
* Region/time zones: raphaelr's patch (`region_select.asm` in Lan Hikari's PR)
  documents `Time_*` functions and the sunrise/sunset calculation; those names
  are in `symbols/functions.csv`.

## Method notes (what worked)

* **Coverage by screen**: the harness records, per marked segment, which ROM
  bytes each screen reads and which instruction read them. Diffing a menu
  against plain field play isolates that menu's tilemap, tiles and code.
* **Pointer evidence**: `LDR`/`LDM` word loads of ROM addresses confirm
  pointers. Words read only by DMA, BIOS copies or halfword loads are
  negative evidence, and bulk-copy loops are discounted. Palettes and PCM
  samples were the main sources of false positives.
* **Debugging a bad pointer**: dump RAM every N frames on both builds;
  `tools/ramdiff.py` finds the first word that differs by something other
  than the shift, and the `watch` command finds the instruction that wrote it.
