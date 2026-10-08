// Headless mGBA harness for Boktai 3 reverse engineering.
//
// Runs the ROM from a command script and records:
//   * screenshots (PPM) on demand
//   * code coverage: every executed ROM/IWRAM/EWRAM address, with ARM/Thumb mode
//   * data coverage: every ROM byte read by a load (including DMA), with the
//     PC of the first instruction that read it
//
// Usage: harness ROM SCRIPT OUTDIR
//
// Script commands (one per line, # comments):
//   wait N              run N frames with no keys held
//   hold KEYS N         hold keys (e.g. A, START, A+UP) for N frames
//   tap KEYS            hold for 2 frames, release for 8
//   shot NAME           write OUTDIR/NAME.ppm
//   save NAME / load NAME   savestate to/from OUTDIR/NAME.ss
//   dump NAME ADDR:LEN  raw memory dump (hex address and length)
//   lux N               solar sensor reading (0-255, game treats lower as brighter)
//   trace on|off        enable coverage recording (default on)
//   (env BOKTAI3_SAV=file.sav loads a battery save first)
//   mark NAME           start a new coverage segment: subsequent coverage is
//                       written to OUTDIR/cov-NAME.* in addition to the totals

#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <mgba/core/config.h>
#include <mgba/core/serialize.h>
#include <mgba/gba/interface.h>
#include <mgba/internal/arm/arm.h>
#include <mgba-util/vfs.h>

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <stdint.h>

#define ROM_SIZE 0x1000000

static struct mCore* core;
static struct ARMCore* cpu;
static struct ARMMemory orig;
static color_t* fb;
static unsigned W, H;
static const char* outdir;
static int tracing = 1;

// Per-byte ROM data read: PC of first reader (0 = never read)
static uint32_t* rom_reader;
// Per-halfword code execution: bit0 = executed in Thumb, bit1 = executed in ARM
static uint8_t* rom_exec;
static uint8_t iwram_exec[0x8000 / 2];
static uint8_t ewram_exec[0x40000 / 2];
// Segment (per "mark") copies
static uint32_t* seg_reader;
static uint8_t* seg_exec;
static char seg_name[256] = "";

static uint8_t lux = 0xE8;

static void quiet_log(struct mLogger* l, int cat, enum mLogLevel lvl, const char* fmt, va_list args) {
	(void) l; (void) cat;
	if (lvl & (mLOG_FATAL | mLOG_ERROR)) { vfprintf(stderr, fmt, args); fputc('\n', stderr); }
}
static struct mLogger quiet = { quiet_log, NULL };

static uint8_t readLux(struct GBALuminanceSource* s) { (void) s; return lux; }
static void sampleLux(struct GBALuminanceSource* s) { (void) s; }
static struct GBALuminanceSource luxsrc = { sampleLux, readLux };

static uint32_t cur_pc(void) {
	// gprs[15] is the prefetch address; subtract pipeline offset
	int thumb = cpu->executionMode == MODE_THUMB;
	return cpu->gprs[15] - (thumb ? 4 : 8);
}

static inline void note_read(uint32_t addr, int width) {
	if (!tracing) return;
	if (addr < 0x08000000 || addr >= 0x0E000000) return;
	uint32_t o = (addr - 0x08000000) & (ROM_SIZE - 1);
	uint32_t pc = cur_pc() | (cpu->executionMode == MODE_THUMB);
	for (int i = 0; i < width && o + i < ROM_SIZE; ++i) {
		if (!rom_reader[o + i]) rom_reader[o + i] = pc;
		if (seg_reader && !seg_reader[o + i]) seg_reader[o + i] = pc;
	}
}

static uint32_t h_load32(struct ARMCore* c, uint32_t a, int* cc) { note_read(a & ~3u, 4); return orig.load32(c, a, cc); }
static uint32_t h_load16(struct ARMCore* c, uint32_t a, int* cc) { note_read(a & ~1u, 2); return orig.load16(c, a, cc); }
static uint32_t h_load8(struct ARMCore* c, uint32_t a, int* cc) { note_read(a, 1); return orig.load8(c, a, cc); }
static uint32_t h_loadMultiple(struct ARMCore* c, uint32_t base, int mask, enum LSMDirection dir, int* cc) {
	int n = __builtin_popcount(mask & 0xFFFF);
	uint32_t start = base;
	if (dir & LSM_D) start = base - 4 * n + ((dir & LSM_B) ? 0 : 4);
	else if (dir & LSM_B) start = base + 4;
	note_read(start & ~3u, 4 * n);
	return orig.loadMultiple(c, base, mask, dir, cc);
}

static void note_exec(void) {
	uint32_t pc = cur_pc();
	uint8_t bit = cpu->executionMode == MODE_THUMB ? 1 : 2;
	if (pc >= 0x08000000 && pc < 0x0A000000) {
		uint32_t o = (pc - 0x08000000) & (ROM_SIZE - 1);
		rom_exec[o >> 1] |= bit;
		if (seg_exec) seg_exec[o >> 1] |= bit;
	} else if (pc >= 0x03000000 && pc < 0x03008000) {
		iwram_exec[(pc - 0x03000000) >> 1] |= bit;
	} else if (pc >= 0x02000000 && pc < 0x02040000) {
		ewram_exec[(pc - 0x02000000) >> 1] |= bit;
	}
}

static void run_frames(int n) {
	for (int f = 0; f < n; ++f) {
		if (!tracing) { core->runFrame(core); continue; }
		uint32_t frame = core->frameCounter(core);
		while (core->frameCounter(core) == frame) {
			note_exec();
			core->step(core);
		}
	}
}

static uint32_t parse_keys(const char* s) {
	static const struct { const char* n; uint32_t k; } map[] = {
		{"A", 1}, {"B", 2}, {"SELECT", 4}, {"START", 8}, {"RIGHT", 16}, {"LEFT", 32},
		{"UP", 64}, {"DOWN", 128}, {"R", 256}, {"L", 512}, {NULL, 0}};
	uint32_t keys = 0;
	char buf[128];
	strncpy(buf, s, sizeof(buf) - 1);
	buf[sizeof(buf) - 1] = 0;
	for (char* t = strtok(buf, "+"); t; t = strtok(NULL, "+")) {
		int found = 0;
		for (int i = 0; map[i].n; ++i) if (!strcmp(map[i].n, t)) { keys |= map[i].k; found = 1; }
		if (!found) { fprintf(stderr, "unknown key %s\n", t); exit(1); }
	}
	return keys;
}

static void shot(const char* name) {
	char path[1024];
	snprintf(path, sizeof(path), "%s/%s.ppm", outdir, name);
	FILE* f = fopen(path, "wb");
	fprintf(f, "P6\n%u %u\n255\n", W, H);
	for (unsigned i = 0; i < W * H; ++i) {
		color_t c = fb[i];
		// mGBA default color_t is 32-bit XBGR8
		uint8_t px[3] = { c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF };
		fwrite(px, 1, 3, f);
	}
	fclose(f);
}

static void write_cov(const char* tag, uint32_t* reader, uint8_t* exec) {
	char path[1024];
	snprintf(path, sizeof(path), "%s/%s.read", outdir, tag);
	FILE* f = fopen(path, "wb"); fwrite(reader, 4, ROM_SIZE, f); fclose(f);
	snprintf(path, sizeof(path), "%s/%s.exec", outdir, tag);
	f = fopen(path, "wb"); fwrite(exec, 1, ROM_SIZE / 2, f); fclose(f);
}

static void end_segment(void) {
	if (!seg_name[0]) return;
	char tag[160];
	snprintf(tag, sizeof(tag), "cov-%s", seg_name);
	write_cov(tag, seg_reader, seg_exec);
	seg_name[0] = 0;
}

static void savestate(const char* name, int load) {
	char path[1024];
	snprintf(path, sizeof(path), "%s/%s.ss", outdir, name);
	size_t sz = core->stateSize(core);
	void* buf = malloc(sz);
	if (load) {
		FILE* f = fopen(path, "rb");
		if (!f) { fprintf(stderr, "no state %s\n", path); exit(1); }
		if (fread(buf, 1, sz, f) != sz) { fprintf(stderr, "short state\n"); exit(1); }
		fclose(f);
		core->loadState(core, buf);
	} else {
		core->saveState(core, buf);
		FILE* f = fopen(path, "wb"); fwrite(buf, 1, sz, f); fclose(f);
	}
	free(buf);
}

int main(int argc, char** argv) {
	if (argc != 4) { fprintf(stderr, "usage: %s ROM SCRIPT OUTDIR\n", argv[0]); return 1; }
	outdir = argv[3];
	mLogSetDefaultLogger(&quiet);
	core = mCoreFind(argv[1]);
	if (!core || !core->init(core)) { fprintf(stderr, "core init failed\n"); return 1; }
	mCoreInitConfig(core, NULL);
	core->desiredVideoDimensions(core, &W, &H);
	fb = calloc(W * H, sizeof(color_t));
	core->setVideoBuffer(core, fb, W);
	if (!mCoreLoadFile(core, argv[1])) { fprintf(stderr, "load failed\n"); return 1; }
	core->setPeripheral(core, mPERIPH_GBA_LUMINANCE, &luxsrc);
	// Optional battery save: BOKTAI3_SAV=path (copied, never modified)
	const char* sav = getenv("BOKTAI3_SAV");
	if (sav) {
		char path[1024];
		snprintf(path, sizeof(path), "%s/battery.sav", outdir);
		FILE* in = fopen(sav, "rb");
		FILE* out = fopen(path, "wb");
		if (!in || !out) { fprintf(stderr, "cannot copy save %s\n", sav); return 1; }
		char buf[4096]; size_t n;
		while ((n = fread(buf, 1, sizeof(buf), in)) > 0) fwrite(buf, 1, n, out);
		fclose(in); fclose(out);
		core->loadSave(core, VFileOpen(path, O_RDWR));
	}
	core->reset(core);

	cpu = core->cpu;
	orig = cpu->memory;
	cpu->memory.load32 = h_load32;
	cpu->memory.load16 = h_load16;
	cpu->memory.load8 = h_load8;
	cpu->memory.loadMultiple = h_loadMultiple;

	rom_reader = calloc(ROM_SIZE, 4);
	rom_exec = calloc(ROM_SIZE / 2, 1);
	seg_reader = NULL;
	seg_exec = NULL;

	FILE* s = fopen(argv[2], "r");
	if (!s) { perror("script"); return 1; }
	char line[512];
	while (fgets(line, sizeof(line), s)) {
		char cmd[64] = "", a1[256] = "", a2[64] = "";
		char* hash = strchr(line, '#');
		if (hash) *hash = 0;
		if (sscanf(line, "%63s %255s %63s", cmd, a1, a2) < 1) continue;
		if (!strcmp(cmd, "wait")) { core->setKeys(core, 0); run_frames(atoi(a1)); }
		else if (!strcmp(cmd, "hold")) { core->setKeys(core, parse_keys(a1)); run_frames(atoi(a2)); core->setKeys(core, 0); }
		else if (!strcmp(cmd, "tap")) { core->setKeys(core, parse_keys(a1)); run_frames(2); core->setKeys(core, 0); run_frames(8); }
		else if (!strcmp(cmd, "shot")) shot(a1);
		else if (!strcmp(cmd, "save")) savestate(a1, 0);
		else if (!strcmp(cmd, "load")) savestate(a1, 1);
		else if (!strcmp(cmd, "dump")) {
			// dump NAME ADDR:LEN  (hex) -> OUTDIR/NAME.bin
			unsigned addr = 0, len = 0;
			sscanf(a2, "%x:%x", &addr, &len);
			char path[1024];
			snprintf(path, sizeof(path), "%s/%s.bin", outdir, a1);
			FILE* f = fopen(path, "wb");
			for (unsigned i = 0; i < len; ++i) fputc(core->rawRead8(core, addr + i, -1), f);
			fclose(f);
		}
		else if (!strcmp(cmd, "lux")) lux = atoi(a1);
		else if (!strcmp(cmd, "trace")) tracing = !strcmp(a1, "on");
		else if (!strcmp(cmd, "mark")) {
			end_segment();
			if (!seg_reader) { seg_reader = calloc(ROM_SIZE, 4); seg_exec = calloc(ROM_SIZE / 2, 1); }
			memset(seg_reader, 0, ROM_SIZE * 4);
			memset(seg_exec, 0, ROM_SIZE / 2);
			strncpy(seg_name, a1, sizeof(seg_name) - 1);
		}
		else { fprintf(stderr, "unknown command %s\n", cmd); return 1; }
		fprintf(stderr, "[frame %u] %s %s %s\n", core->frameCounter(core), cmd, a1, a2);
	}
	end_segment();
	write_cov("total", rom_reader, rom_exec);
	char path[1024];
	snprintf(path, sizeof(path), "%s/total.iwram_exec", outdir);
	FILE* f = fopen(path, "wb"); fwrite(iwram_exec, 1, sizeof(iwram_exec), f); fclose(f);
	snprintf(path, sizeof(path), "%s/total.ewram_exec", outdir);
	f = fopen(path, "wb"); fwrite(ewram_exec, 1, sizeof(ewram_exec), f); fclose(f);
	core->deinit(core);
	return 0;
}
