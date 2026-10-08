"""GBA BIOS LZ77 (type 0x10) codec."""


def decompress(b, off, limit=0x200000):
    """Return (data, compressed_length) or None if the stream is invalid."""
    if b[off] != 0x10:
        return None
    size = b[off + 1] | b[off + 2] << 8 | b[off + 3] << 16
    if size == 0 or size > limit:
        return None
    out = bytearray()
    i = off + 4
    n = len(b)
    while len(out) < size:
        if i >= n:
            return None
        flags = b[i]
        i += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                if i + 1 >= n:
                    return None
                x = b[i] << 8 | b[i + 1]
                i += 2
                ln = (x >> 12) + 3
                disp = (x & 0xFFF) + 1
                if disp > len(out):
                    return None
                for _ in range(ln):
                    out.append(out[-disp])
            else:
                if i >= n:
                    return None
                out.append(b[i])
                i += 1
    return bytes(out[:size]), i - off


def compress(data):
    """Greedy LZ77 compressor (VRAM-safe: minimum displacement 2)."""
    out = bytearray([0x10, len(data) & 0xFF, len(data) >> 8 & 0xFF, len(data) >> 16 & 0xFF])
    i = 0
    n = len(data)
    while i < n:
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= n:
                break
            best_len = 0
            best_disp = 0
            start = max(0, i - 0x1000)
            for j in range(i - 2, start - 1, -1):
                ln = 0
                while ln < 18 and i + ln < n and data[j + ln] == data[i + ln]:
                    ln += 1
                if ln > best_len:
                    best_len, best_disp = ln, i - j
                    if ln == 18:
                        break
            if best_len >= 3:
                x = (best_len - 3) << 12 | (best_disp - 1)
                out += bytes([x >> 8, x & 0xFF])
                flags |= 0x80 >> bit
                i += best_len
            else:
                out.append(data[i])
                i += 1
        out[flag_pos] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)
