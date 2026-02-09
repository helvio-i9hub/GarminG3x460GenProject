import struct
import socket
import time

FLAG = 0x7E
ESC  = 0x7D

# Message IDs
MSG_HEARTBEAT = 0x00
MSG_OWNHIP    = 0x0A
MSG_TRAFFIC   = 0x14

CRC_POLY = 0x8408
CRC_INIT = 0xFFFF


# ---------------- CRC ----------------
def crc16_ccitt(data: bytes) -> int:
    crc = CRC_INIT
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ CRC_POLY
            else:
                crc >>= 1
    return (~crc) & 0xFFFF


# ---------------- Framing ----------------
def escape(data: bytes) -> bytes:
    out = bytearray()
    for b in data:
        if b == FLAG:
            out += bytes([ESC, 0x5E])
        elif b == ESC:
            out += bytes([ESC, 0x5D])
        else:
            out.append(b)
    return bytes(out)


def frame(msg: bytes) -> bytes:
    crc = crc16_ccitt(msg)
    packet = msg + struct.pack("<H", crc)
    return bytes([FLAG]) + escape(packet) + bytes([FLAG])


# ---------------- Messages ----------------
def heartbeat():
    # Status = 0x0000, Timestamp = 0
    payload = struct.pack("<BHH",
        MSG_HEARTBEAT,
        0x0000,
        0
    )
    return frame(payload)


def ownship(lat, lon, alt_ft, gs_kt, track_deg):
    lat_i = int(lat * 1e7)
    lon_i = int(lon * 1e7)
    alt_i = int((alt_ft + 1000) / 25)  # GDL90 pressure alt
    gs_i  = int(gs_kt)
    trk_i = int(track_deg)

    payload = struct.pack(
        "<BiiHHHB",
        MSG_OWNHIP,
        lat_i,
        lon_i,
        alt_i,
        gs_i,
        trk_i,
        0x00
    )
    return frame(payload)


def traffic(addr, lat, lon, alt_ft, gs, track):
    lat_i = int(lat * 1e7)
    lon_i = int(lon * 1e7)
    alt_i = int((alt_ft + 1000) / 25)

    payload = struct.pack(
        "<BIiiHHHB",
        MSG_TRAFFIC,
        addr,     # ICAO address
        lat_i,
        lon_i,
        alt_i,
        int(gs),
        int(track),
        0x01      # airborne
    )
    return frame(payload)


def main():
    UDP_IP = "127.0.0.1"
    UDP_PORT = 4000

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    lat, lon = -23.55, -46.63

    while True:
        sock.sendto(heartbeat(), (UDP_IP, UDP_PORT))
        sock.sendto(ownship(lat, lon, 3500, 120, 270), (UDP_IP, UDP_PORT))
        sock.sendto(
            traffic(0xABCDEF, lat + 0.02, lon + 0.01, 3800, 110, 90),
            (UDP_IP, UDP_PORT)
        )

        lat += 0.0001
        time.sleep(1)
