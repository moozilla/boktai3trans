# Ghidra headless analysis

Produces a Ghidra project plus `functions.tsv` and decompiler output for every
function (`decomp.c`, ~13 MB). That output is a starting point for writing C;
it isn't matching code.

```
GHIDRA=/path/to/ghidra_11.3.2_PUBLIC
$GHIDRA/support/analyzeHeadless build/ghidra shinbok -import baserom.gba \
    -loader BinaryLoader -loader-baseAddr 0x08000000 -processor ARM:LE:32:v4t \
    -scriptPath tools/ghidra -preScript GBASetup.java -postScript SeedThumb.java 8260000
$GHIDRA/support/analyzeHeadless build/ghidra shinbok -process baserom.gba -noanalysis \
    -readOnly -scriptPath tools/ghidra -postScript ExportAll.java build/ghidra/out
```

* `GBASetup.java`: GBA memory map (BIOS/EWRAM/IWRAM/IO/PAL/VRAM/OAM/SRAM), ARM entry
* `SeedThumb.java`: seeds Thumb functions at `push {..., lr}` sites Ghidra missed
* `ExportAll.java`: function table + decompiled C

First analysis takes about 25 minutes on 4 cores. Ghidra finds 10,686
functions in the code region and gbadisasm finds 7,868. The difference is
mostly unreferenced or indirectly called code that Ghidra's aggressive seeding
picks up; some of it is false. Cross-checking the two lists is a good way to
find the remaining function-pointer tables.
