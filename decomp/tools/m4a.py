#!/usr/bin/env python3
"""MP2K ("Sappy"/m4a) sound data walker.

Parses the song table, song headers, track bytecode and voicegroups to find
every absolute pointer inside sound data -- in particular the unaligned
GOTO/PATT/REPT operands inside track streams, which a word-aligned pointer
scan cannot find.

  m4a.py            summary: songs, tracks, voicegroups, pointer counts
  m4a.py --list     one line per song
"""
import sys

from romlib import load_rom, u32

ROM_BASE = 0x08000000
SONG_TABLE = 0x0826456C  # gSongTable; entry 0 (and others) is a 0-track dummy song

# command -> number of fixed argument bytes (pointers handled separately)
ARGS1 = set(range(0xBA, 0xCE)) - {0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCC}


def is_rom(v, n):
    return ROM_BASE <= v < ROM_BASE + n


class Walker:
    def __init__(self, rom):
        self.rom = rom
        self.ptr_locs = {}      # ROM address of pointer field -> target
        self.tracks = set()
        self.track_extent = {}  # start -> end (exclusive), merged per walk
        self.voicegroups = set()
        self.songs = []
        self.samples = {}       # wave header address -> end (exclusive)

    def u32(self, a):
        return u32(self.rom, a - ROM_BASE)

    def b(self, a):
        return self.rom[a - ROM_BASE]

    def walk_track(self, start):
        """Walk a track stream; follows PATT targets; stops at FINE/GOTO."""
        todo = [start]
        while todo:
            a = todo.pop()
            if a in self.tracks:
                continue
            self.tracks.add(a)
            pos = a
            for _ in range(200000):
                c = self.b(pos)
                if c < 0x80:          # running-status argument
                    pos += 1
                    continue
                if c <= 0xB0:         # wait
                    pos += 1
                elif c == 0xB1:       # FINE
                    pos += 1
                    break
                elif c in (0xB2, 0xB3):  # GOTO / PATT ptr
                    t = self.u32(pos + 1)
                    self.ptr_locs[pos + 1] = t
                    if c == 0xB3:
                        todo.append(t)
                        pos += 5
                    else:
                        if t >= a and t < pos:
                            pos += 5
                            break  # loop back: track ends
                        todo.append(t)
                        pos += 5
                        break
                elif c == 0xB4:       # PEND
                    pos += 1
                    if pos > a:
                        pass
                elif c == 0xB5:       # REPT count ptr
                    t = self.u32(pos + 2)
                    self.ptr_locs[pos + 2] = t
                    todo.append(t)
                    pos += 6
                elif c == 0xB9:       # MEMACC op addr data
                    pos += 4
                elif c == 0xCD:       # XCMD type param
                    pos += 3
                elif c in ARGS1:
                    pos += 2
                elif c >= 0xCE:       # EOT / TIE / notes: up to 3 args < 0x80
                    pos += 1
                    for _ in range(3):
                        if self.b(pos) < 0x80:
                            pos += 1
                        else:
                            break
                else:
                    pos += 1
            self.track_extent[a] = max(self.track_extent.get(a, 0), pos)

    def walk_voicegroup(self, vg, count=128):
        if vg in self.voicegroups:
            return
        self.voicegroups.add(vg)
        n = len(self.rom)
        for i in range(count):
            e = vg + 12 * i
            if e + 12 - ROM_BASE > n:
                break
            kind = self.b(e)
            if kind & 0x40:              # keysplit: +4 voicegroup*, +8 keysplit table*
                for off in (4, 8):
                    t = self.u32(e + off)
                    if is_rom(t, n):
                        self.ptr_locs[e + off] = t
                sub = self.u32(e + 4)
                if is_rom(sub, n):
                    self.walk_voicegroup(sub)
            elif kind & 0x80:            # rhythm: +4 voicegroup*
                t = self.u32(e + 4)
                if is_rom(t, n):
                    self.ptr_locs[e + 4] = t
                    self.walk_voicegroup(t)
            elif kind & 0x07 in (0, 3):  # DirectSound (+fixed-freq variants) or programmable wave
                t = self.u32(e + 4)
                if is_rom(t, n):
                    self.ptr_locs[e + 4] = t
                    if kind & 0x07 == 0:
                        size = self.u32(t + 12)       # wave header: type, flags, freq, loop, size
                        if size < 0x200000:
                            self.samples[t] = t + 16 + size + 1
                    else:
                        self.samples[t] = t + 16      # 4-bit programmable wave, 32 samples

    def walk(self):
        n = len(self.rom)
        i = 0
        while True:
            ent = SONG_TABLE + 8 * i
            song = self.u32(ent)
            if not is_rom(song, n):
                break
            self.ptr_locs[ent] = song
            ntracks = self.b(song)
            vg = self.u32(song + 4)
            if ntracks > 16 or (ntracks and not is_rom(vg, n)):
                del self.ptr_locs[ent]
                break
            if is_rom(vg, n):
                self.ptr_locs[song + 4] = vg
                self.walk_voicegroup(vg)
            for t in range(ntracks):
                tp = self.u32(song + 8 + 4 * t)
                self.ptr_locs[song + 8 + 4 * t] = tp
                self.walk_track(tp)
            self.songs.append((i, song, ntracks, vg))
            i += 1
        return self


def walk(rom):
    return Walker(rom).walk()


def main():
    rom = load_rom()
    w = walk(rom)
    if "--list" in sys.argv:
        for i, song, nt, vg in w.songs:
            print(f"song {i:3d} {song:08X} tracks {nt:2d} voicegroup {vg:08X}")
        return
    unaligned = sum(1 for a in w.ptr_locs if a & 3)
    print(f"{len(w.songs)} songs, {len(w.tracks)} track streams, {len(w.voicegroups)} voicegroups, "
          f"{len(w.ptr_locs)} pointer fields ({unaligned} unaligned), {len(w.samples)} samples "
          f"({sum(e - s for s, e in w.samples.items())} bytes)")


if __name__ == "__main__":
    main()
