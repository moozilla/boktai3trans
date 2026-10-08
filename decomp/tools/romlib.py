"""Shared helpers: locate and verify the base ROM, read primitives."""
import hashlib
import os
import struct
import sys

BASEROM_SHA1 = "2651c5e6875ac60abff734510d152166d211c87c"  # BOKTAI3 / U33J (Japan)
ROM_BASE = 0x08000000

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def baserom_path():
    p = os.environ.get("BOKTAI3_ROM", os.path.join(ROOT, "baserom.gba"))
    if not os.path.exists(p):
        sys.exit(f"Base ROM not found at {p}. Put the Japanese ROM there or set BOKTAI3_ROM.")
    return p


def load_rom(verify=True):
    data = open(baserom_path(), "rb").read()
    if verify:
        h = hashlib.sha1(data).hexdigest()
        if h != BASEROM_SHA1:
            sys.exit(f"Base ROM SHA-1 mismatch: {h} (expected {BASEROM_SHA1})")
    return data


def u8(b, o): return b[o]
def u16(b, o): return struct.unpack_from("<H", b, o)[0]
def u32(b, o): return struct.unpack_from("<I", b, o)[0]


def is_rom_ptr(v, rom_len=0x1000000):
    return ROM_BASE <= v < ROM_BASE + rom_len


def off(addr):
    """GBA bus address -> ROM file offset."""
    return addr - ROM_BASE if addr >= ROM_BASE else addr
