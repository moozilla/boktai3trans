#!/bin/sh
# Shiftability test: build with all data moved by SHIFT bytes, play the same
# input script on both ROMs in the harness, and compare screenshots.
#   tools/shift_test.sh SCRIPT [SHIFT]   (BOKTAI3_SAV may name a battery save)
set -e
cd "$(dirname "$0")/.."
SCRIPT=$1; SHIFT=${2:-0x100}
make -s build/shifted.gba SHIFT=$SHIFT
python3 - <<'PY'
b = open("build/shifted.gba", "rb").read()
# keep 16 MiB so EEPROM stays mapped at 0x0D000000 (data past the end is zero padding)
assert not any(b[0x1000000:]), "shifted ROM has data past 16 MiB"
open("build/shifted.gba", "wb").write(b[:0x1000000])
PY
OUT=build/shift_test/$(date +%s); mkdir -p $OUT/orig $OUT/shift
tools/emu/harness baserom.gba "$SCRIPT" $OUT/orig >/dev/null 2>&1
tools/emu/harness build/shifted.gba "$SCRIPT" $OUT/shift >/dev/null 2>&1
python3 - "$OUT" <<'PY'
import glob, sys
from PIL import Image, ImageChops
out = sys.argv[1]; bad = 0
for f in sorted(glob.glob(out + "/orig/*.ppm")):
    g = f.replace("/orig/", "/shift/")
    same = ImageChops.difference(Image.open(f), Image.open(g)).getbbox() is None
    bad += not same
    print(("same " if same else "DIFF ") + f.split("/")[-1])
sys.exit(1 if bad else 0)
PY
