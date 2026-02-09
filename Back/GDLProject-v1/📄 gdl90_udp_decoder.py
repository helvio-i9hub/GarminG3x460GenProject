#!/usr/bin/env python3
import socket
import struct
from datetime import datetime

UDP_IP = "0.0.0.0"
UDP_PORT = 4000

FLAG = 0x7E
ESC  = 0x7D


# -------------------------------------------------
# GDL90 CRC-16 (X.25 / HDLC, reflected)
# poly=0x1021 -> reflected 0x8408
# init=0xFFFF, refin/refout=true
# -------------------------------------------------
def gdl90_crc(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return crc & 0xFFFF


# -------------------------------------------------
# Unescape HDLC-style bytes
# -------------------------------------------------
def unescape_gdl90(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        if data[i] == ESC:
            out.append(data[i + 1] ^ 0x20)
            i += 2
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


# -------------------------------------------------
# Message Decoders
# -------------------------------------------------
def decode_heartbeat(payload):
    status, ts = struct.unpack(">BH", payload[:3])
    return {
        "status": status,
        "timestamp": ts
    }


def decode_ident(payload):
    callsign = payload[2:22].decode("ascii", errors="ignore").strip()
    return {"callsign": callsign}


def decode_traffic(payload):
    # Latitude / Longitude (24-bit signed)
    lat_raw = struct.unpack(">i", b'\x00' + payload[1:4])[0] >> 8
    lon_raw = struct.unpack(">i", b'\x00' + payload[4:7])[0] >> 8

    lat = lat_raw * 180.0 / (1 << 23)
    lon = lon_raw * 180.0 / (1 << 23)

    # Altitude (25 ft resolution, offset -1000 ft)
    altitude = ((payload[7] << 4) | (payload[8] >> 4)) * 25 - 1000

    # Velocity / Heading
    heading = payload[9] * 360.0 / 256.0
    h_speed = payload[10]

    # Callsign
    callsign = payload[18:26].decode("ascii", errors="ignore").strip()

    return {
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "altitude_ft": altitude,
        "heading_deg": round(heading, 1),
        "ground_speed_kt": h_speed,
        "callsign": callsign
    }


# -------------------------------------------------
# Main UDP Receiver
# -------------------------------------------------
def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"Listening for GDL-90 on UDP/{UDP_PORT}...\n")

    buffer = bytearray()

    while True:
        pkt, addr = sock.recvfrom(2048)
        buffer.extend(pkt)

        while FLAG in buffer:
            start = buffer.find(FLAG)
            end = buffer.find(FLAG, start + 1)

            if end == -1:
                break

            raw_frame = buffer[start + 1:end]
            buffer = buffer[end + 1:]

            frame = unescape_gdl90(raw_frame)

            if len(frame) < 4:
                continue

            msg_id = frame[0]
            payload = frame[1:-2]
            rx_crc = struct.unpack("<H", frame[-2:])[0]
            calc_crc = gdl90_crc(frame[:-2])

            ts = datetime.utcnow().isoformat()

            print("-" * 70)
            print(f"[{ts}] FRAME: {frame.hex()}")
            print(f"  MSG ID: 0x{msg_id:02X}")
            print(f"  CRC: rx=0x{rx_crc:04X} calc=0x{calc_crc:04X} "
                  f"{'OK' if rx_crc == calc_crc else 'ERROR'}")

            try:
                if msg_id == 0x00:
                    print("  Type: Heartbeat")
                    print(" ", decode_heartbeat(payload))

                elif msg_id == 0x0A:
                    print("  Type: Ownship Report")
                    print(" ", decode_traffic(payload))

                elif msg_id == 0x14:
                    print("  Type: Traffic Report")
                    print(" ", decode_traffic(payload))

                elif msg_id == 0x65:
                    print("  Type: Identification")
                    print(" ", decode_ident(payload))

                else:
                    print("  Type: Unknown")

            except Exception as e:
                print("  Decode error:", e)


if __name__ == "__main__":
    main()
