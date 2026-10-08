# Boktai 3 (U33J) reverse-engineering build.
#   make setup     fetch/build pinned tools (gbadisasm, agbcc, armips, mGBA harness)
#   make disasm    regenerate build/asm/code.s from baserom.gba + symbols/
#   make           assemble build/boktai3.gba and verify it matches the base ROM
#   make text      re-dump text/script.jsonl
AS      := arm-none-eabi-as
LD      := arm-none-eabi-ld
OBJCOPY := arm-none-eabi-objcopy
ASFLAGS := -mcpu=arm7tdmi --no-warn
PY      := python3

ROM     := build/boktai3.gba
SHA1    := 2651c5e6875ac60abff734510d152166d211c87c

.PHONY: all compare setup disasm text clean shifttest
# Default: split asm around src/*.c, compile with agbcc, link, verify SHA-1
all: build/asm/code_sym.s build/asm/data.s
	$(PY) tools/build.py

setup:
	tools/setup.sh

build/asm/code.s: tools/disasm.py
	$(PY) tools/disasm.py

build/asm/code_sym.s build/asm/data.s: build/asm/code.s tools/symbolize.py tools/m4a.py symbols/*.csv symbols/*.txt
	$(PY) tools/symbolize.py

disasm: build/asm/code_sym.s

build/rom.o: asm/rom.s asm/macros.inc build/asm/code_sym.s build/asm/data.s baserom.gba
	$(AS) $(ASFLAGS) -o $@ asm/rom.s

# Shiftability test: move all data by SHIFT bytes and boot it in the emulator
build/shifted.gba: asm/rom.s asm/macros.inc build/asm/code_sym.s build/asm/data.s baserom.gba
	$(AS) $(ASFLAGS) --defsym SHIFT=$(or $(SHIFT),0x100) -o build/shifted.o asm/rom.s
	$(LD) -Ttext=0x08000000 -e 0x08000000 -o build/shifted.elf build/shifted.o
	$(OBJCOPY) -O binary build/shifted.elf $@

build/rom.elf: build/rom.o
	$(LD) -Ttext=0x08000000 -e 0x08000000 -o $@ $<

$(ROM): build/rom.elf
	$(OBJCOPY) -O binary $< $@

# Pure-asm build (no C), useful to check the generated asm alone
compare: $(ROM)
	@echo "$(SHA1)  $(ROM)" | sha1sum -c -

text:
	$(PY) tools/text_dump.py

clean:
	rm -f build/rom.o build/rom.elf $(ROM)

# Regression: data moved by SHIFT must play identically (needs the harness)
SAVE := ../ShinBok2.sav
shifttest: build/asm/code_sym.s build/asm/data.s
	tools/shift_test.sh tests/newgame_intro.txt $(or $(SHIFT),0x10000)
	BOKTAI3_SAV=$(SAVE) tools/shift_test.sh tests/save_boot.txt $(or $(SHIFT),0x10000)
	BOKTAI3_SAV=$(SAVE) tools/shift_test.sh tests/save_menus_field.txt $(or $(SHIFT),0x10000)
