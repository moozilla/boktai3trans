#!/bin/sh
# Shiftability test: build with all data moved by SHIFT bytes, play the same
# input script on both ROMs in the harness, and compare screenshots.
#   tools/shift_test.sh SCRIPT [SHIFT]   (BOKTAI3_SAV may name a battery save)
set -e
cd "$(dirname "$0")/.."
SCRIPT=$1; SHIFT=${2:-0x100}
# (build.py trims trailing zero padding back to 16 MiB so EEPROM stays at 0x0D000000)
python3 tools/build.py --shift $SHIFT --out build/shifted.gba
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
