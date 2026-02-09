#!/usr/bin/env python3
import socket
import serial

FRAME_DELIM = 0x7E
ESCAPE = 0x7D
ESC_XOR = 0x20



def clean_callsign(raw: bytes) -> str:
    return "".join(
        chr(b) for b in raw
        if 32 <= b <= 126
    ).strip()


# ============================================================
# CRC-16 X25 (GDL90) – COMPUTED BUT NOT ENFORCED
# ============================================================

def crc16_x25(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return (~crc) & 0xFFFF


# ============================================================
# Framing helpers
# ============================================================

def unescape(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        if data[i] == ESCAPE:
            i += 1
            if i < len(data):
                out.append(data[i] ^ ESC_XOR)
        else:
            out.append(data[i])
        i += 1
    return bytes(out)


def extract_frames(buf: bytearray):
    frames = []
    while True:
        try:
            s = buf.index(FRAME_DELIM)
            e = buf.index(FRAME_DELIM, s + 1)
        except ValueError:
            break

        raw = buf[s + 1:e]
        del buf[:e + 1]
        frames.append(unescape(raw))

    return frames


def s24(b):
    v = (b[0] << 16) | (b[1] << 8) | b[2]
    if v & 0x800000:
        v -= 1 << 24
    return v


# ============================================================
# GDL90 Decoders
# ============================================================

def decode_heartbeat(p):
    return {
        "uptime_s": (p[1] << 8) | p[2],
        "gps_valid": bool(p[3] & 0x01),
        "traffic_valid": bool(p[3] & 0x02),
    }


def decode_geo_altitude(p):
    alt = ((p[1] << 8) | p[2]) & 0x0FFF
    return {
        "geo_altitude_ft": alt * 25 - 1000
    }


def decode_ownship(p):
    lat = s24(p[1:4]) * (180 / (1 << 23))
    lon = s24(p[4:7]) * (180 / (1 << 23))
    alt = (((p[7] << 8) | p[8]) & 0x0FFF) * 25 - 1000
    heading = p[9] * (360 / 256)
    gs = p[10]

    return {
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "altitude_ft": alt,
        "heading_deg": round(heading, 1),
        "ground_speed_kt": gs,
    }

def decode_traffic(p):
    addr = (p[1] << 16) | (p[2] << 8) | p[3]

    lat = s24(p[4:7]) * (180 / (1 << 23))
    lon = s24(p[7:10]) * (180 / (1 << 23))

    alt_raw = ((p[10] << 8) | p[11]) & 0x0FFF
    altitude = alt_raw * 25 - 1000

    ground_speed = p[12]
    heading = p[13] * (360 / 256)

    callsign = p[18:26].decode("ascii", errors="ignore").strip()
    callsign = clean_callsign(p[18:26])

    return {
        "address": f"{addr:06X}",
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "altitude_ft": altitude,
        "heading_deg": round(heading, 1),
        "ground_speed_kt": ground_speed,
        "callsign": callsign,
    }


# ============================================================
# Frame Decoder (CRC IGNORED)
# ============================================================

def decode_frame(frame: bytes):
    if len(frame) < 4:
        return

    payload = frame[:-2]
    rx_crc = frame[-2] | (frame[-1] << 8)
    calc_crc = crc16_x25(payload)

    msg_id = payload[0]

    print(f"FRAME: {payload.hex()}")
    print(f"  MSG ID: 0x{msg_id:02X}")
    print(
        f"  CRC: rx=0x{rx_crc:04X} calc=0x{calc_crc:04X}",
        "OK" if rx_crc == calc_crc else "ERROR",
    )

    # 🚨 CRC IS NOT USED TO BLOCK DECODING 🚨

    if msg_id == 0x00:
        print("  Type: Heartbeat")
        print(" ", decode_heartbeat(payload))

    elif msg_id == 0x0B:
        print("  Type: Geo Altitude")
        print(" ", decode_geo_altitude(payload))

    elif msg_id == 0x0A:
        print("  Type: Ownship Report")
        print(" ", decode_ownship(payload))

    elif msg_id == 0x14:
        print("  Type: Traffic Report")
        print(" ", decode_traffic(payload))

    else:
        print("  Type: Unknown")

    print("-" * 70)


# ============================================================
# Input sources
# ============================================================

def from_udp(port=4000):
    print(f"Listening for GDL90 UDP on 0.0.0.0:{port}")
    buf = bytearray()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))

    while True:
        data, _ = sock.recvfrom(8192)
        buf.extend(data)
        for f in extract_frames(buf):
            decode_frame(f)


def from_tcp(host="127.0.0.1", port=3100):
    buf = bytearray()
    with socket.create_connection((host, port)) as s:
        while True:
            data = s.recv(4096)
            if not data:
                break
            buf.extend(data)
            for f in extract_frames(buf):
                decode_frame(f)


def from_serial(dev="/dev/ttyUSB0", baud=115200):
    buf = bytearray()
    with serial.Serial(dev, baud, timeout=1) as ser:
        while True:
            data = ser.read(512)
            if not data:
                continue
            buf.extend(data)
            for f in extract_frames(buf):
                decode_frame(f)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    # Select ONE input method
    from_udp(4000)
    # from_tcp()
    # from_serial()
