import sys, struct

def depack(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        tag = data[i]; i += 1
        if tag == 0:
            if i >= n: break
            cnt = data[i]; i += 1
            out += b"\x00" * (cnt * 8)
        elif tag == 0xFF:
            if i >= n: break
            cnt = data[i]; i += 1
            nb = cnt * 8
            out += data[i:i+nb]; i += nb
        else:
            for b in range(8):
                if tag & (1 << b):
                    out.append(data[i]); i += 1
                else:
                    out.append(0)
    return bytes(out)

if __name__ == "__main__":
    raw = open(sys.argv[1], 'rb').read()
    d = depack(raw)
    print("depacked:", len(d), "from", len(raw))
    print("first 64 bytes:", d[:64].hex(' '))
    # segment table: u32 nsegs-1, then u32 words per segment
    nsegs = struct.unpack_from('<I', d, 0)[0] + 1
    sizes = struct.unpack_from(f'<{nsegs}I', d, 4)
    print("segments:", nsegs, "sizes(words):", sizes[:10])
    off = 4 + 4 * nsegs
    if nsegs % 2 == 0:  # padding to 8-byte boundary
        off += 4
    print("seg0 starts at", off, "root ptr:", d[off:off+8].hex(' '))
    open(sys.argv[1] + '.capnp', 'wb').write(d)
