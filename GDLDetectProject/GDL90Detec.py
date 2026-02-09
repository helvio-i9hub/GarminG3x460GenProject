def crc16_ccitt(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def unescape_gdl90(data):
    """
    GDL90 byte unescaping:
      0x7D 0x5E -> 0x7E
      0x7D 0x5D -> 0x7D
    """
    out = bytearray()
    i = 0
    while i < len(data):
        if data[i] == 0x7D:
            if i + 1 < len(data):
                if data[i + 1] == 0x5E:
                    out.append(0x7E)
                elif data[i + 1] == 0x5D:
                    out.append(0x7D)
                else:
                    # Invalid escape, keep raw
                    out.append(data[i + 1])
                i += 2
            else:
                i += 1
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


def is_gdl90_file(filename):
    with open(filename, "rb") as f:
        data = f.read()

    raw_frames = data.split(b'\x7E')
    valid = 0
    total = 0

    for raw in raw_frames:
        if len(raw) < 4:
            continue

        frame = unescape_gdl90(raw)

        if len(frame) < 4:
            continue

        payload = frame[:-2]
        rx_crc = int.from_bytes(frame[-2:], "little")
        calc_crc = crc16_ccitt(payload)

        total += 1
        if rx_crc == calc_crc:
            valid += 1

    print(f"Total candidate frames: {total}")
    print(f"Valid GDL90 frames:     {valid}")

    return valid > 0


if __name__ == "__main__":
    fname = "/home/helvio/Downloads/log-aviao.dat"   # <-- change this
    if is_gdl90_file(fname):
        print("✔ This file IS very likely GDL90")
    else:
        print("✘ This file does NOT look like GDL90")
