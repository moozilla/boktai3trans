# ROM map — Boktai 3 (U33J)

16 MiB ROM; the last used byte is `0x08E88144`, leaving **1.47 MiB of zero
padding** (`0x08E88145`–`0x08FFFFFF`) — free space for the translation, and the
ROM can also grow to 32 MiB.

Confidence: **high** = verified by rebuild, emulator, or rendering;
**medium** = consistent evidence (coverage/reader functions) but not decoded.

| Range | Size | Contents | Conf. | Evidence |
|---|---|---|---|---|
| `08000000–080000BF` | 192 B | GBA header (`BOKTAI3`, `U33J`, maker `A4`) | high | spec |
| `080000C0–0800034F` | | crt0 (ARM): stacks, `IntrMain` install, `AgbMain` call; `IntrMain` at `080001F0` is copied to IWRAM `03003A60` | high | disasm |
| `08000350–0800145B` | 4.3 KB | ARM code linked at **IWRAM `03000000`** (copy/blit/OAM helpers; bulk `ldm`/`stm` loops) | high | IWRAM dump matches ROM |
| `0800145C–0824DAF9` | 2.3 MB | **Thumb code** (agbcc), 7,868 functions; includes Nintendo `libagbsyscall` at `08248590` | high | bit-identical reassembly |
| `0822F248–0822F647` | 1 KB | MP2K `SoundMainRAM` (mixer), linked at **IWRAM `030035F0`** | high | IWRAM dump; 0x630 stereo-buffer offset |
| `0824DAFC–08250673` | 11 KB | misc constant tables after code | medium | |
| `08250674–082638FF` | 77 KB | MP2K **voicegroups** (81) | high | `tools/m4a.py` |
| `0826456C–08267423` | 11.6 KB | MP2K **song table** — 1,483 entries `{song*, u16 ms, u16 me}`, entry 0 = 0-track dummy | high | walk + shift test |
| `082641EC–0857D8D7` | 3.2 MB | MP2K **PCM samples** (415 wave headers + 8-bit signed data) | high | walk; mixer coverage |
| `0857D8D8–08602C8B` | 0.5 MB | MP2K **track streams** (5,525) and song headers; 5,611 unaligned GOTO/PATT/REPT pointers | high | walk + shift test |
| `0860xxxx–0861xxxx` | | pointer tables incl. Thumb function-pointer tables (`086056EC`, `086121C8`, `0861256C`, `08613E18`) — likely actor/state dispatch | medium | scan, readers `0822580C` |
| `0865xxxx–0875xxxx` | | **BG graphics**: tiles + 0x200-byte tilemaps (`BgGfx_LoadTiles` / `BgGfx_LoadTilemap`), some LZ77 (`LZ77UnCompWram` reads `0870–0881`) | medium | coverage |
| `0870A230–0870C217` | 8 KB | pause-menu / HUD BG tiles | high | VRAM→ROM map, 2007 notes |
| `0870C238–…` | | pause-menu tilemaps, one per screen every `0x200` (items `0870D578`, status `0870DD78`, config `0870DF78`) | high | coverage per screen |
| `0882xxxx–088Bxxxx` | | data copied with CpuSet/CpuFastSet; read by `sub_08215D40` | medium | coverage |
| `089F8F00–089FAEFF` | 8 KB | **8×16 font**, chars `0x20–0x9F` (+ accented Latin at the top) | high | rendered |
| `089FAF00–08A2AEFF` | 192 KB | **16×16 kana/kanji font**, glyph = code − `0x8000` | high | rendered |
| `08A2xxxx–08B1xxxx` | | graphics (portraits e.g. `08B154B4`) | medium | VRAM→ROM map |
| `08BE2F04–08CDxxxx` | | **sprite (OBJ) graphics**: button labels (`08BE2F04`), menu titles (`08C11880`, `08C15880`), bike/course menus | high (spots) | VRAM→ROM map, `ObjGfx_LoadTiles` |
| `08D5xxxx–08D6B1F7` | | tables read by `Script_ReadProcTable` (`0821ACB4`) + palettes (`08D5943C` …) | medium | coverage |
| `08D6B1F8–08D74DDB` | 39 KB | **script text pointer table**: 9,976 × u32, bit 31 = text, offset from `08D74DDC` | high | dump round-trips |
| `08D74DDC–08DD6B94` | 400 KB | **script text bank** (ASCII + 2-byte codes `0x80xx–0x85xx`, inline `<TAG=…>` markup) | high | `text/script.jsonl` |
| `08DD6B95–08E8755B` | 0.7 MB | **event bytecode** (keyword VM, `Script_*` functions; embeds EUC-JP debug labels like `★★★ゲームスタート画面★★★`), with interleaved pointer tables (`08E785CC`, `08E83890`) | high (region) | VM coverage; shift test |
| `08E8755C–08E88144` | | pointer table into the bytecode (≥ 240 entries) | medium | scan, `0821AC44` |
| `08E88145–08FFFFFF` | 1.47 MB | **free** (zero padding) | high | |

## RAM

| Address | What |
|---|---|
| `03000000` | ARM helpers copied from `08000350` |
| `030035F0` | MP2K `SoundMainRAM` (from `0822F248`) |
| `03003A60` | `IntrMain` copy; interrupt table at `03003A10` |
| `030053F8` | pointer to global save data (raphaelr) |
| `03005E60…` | MP2K PCM mixing buffer |
| `02036FDC…` | palette fade work buffer (written by `08217xxx`) |

## Free-space / repointing notes for the translation

* The text bank is addressed only through the pointer table (offsets from a
  base), so it can be rebuilt anywhere and grow into the free space.
* Because the build is shiftable, assets can also simply grow in place: the
  linker moves everything after them and fixes every pointer.
