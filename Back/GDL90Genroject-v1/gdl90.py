#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GDL90 Message Generator
Compatible with Stratux / ForeFlight / SkyDemon
"""

import struct
import socket
import time

# ===============================
# GDL90 CONSTANTS
# ===============================
FLAG = 0x7E
ESC = 0x7D

MSG_HEARTBEAT = 0x00
MSG_OWNHIP = 0x0A
MSG_TRAFFIC = 0x14

CRC_POLY = 0x8408
CRC_INIT = 0xFFFF


# ===============================
# CRC-16 CCITT (X.25)
# ===============================
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


# ===============================
# BYTE STUFFING
# ===============================
def escape_bytes(data: bytes) -> bytes:
    out = bytearray()
    for b in data:
        if b == FLAG:
            out.extend([ESC, 0x5E])
        elif b == ESC:
            out.extend([ESC, 0x5D])
        else:
            out.append(b)
    return bytes(out)


# ===============================
# FRAME BUILDER
# ===============================
def frame_gdl90(message: bytes) -> bytes:
    crc = crc16_ccitt(message)
    packet = message + struct.pack("<H", crc)
    return bytes([FLAG]) + escape_bytes(packet) + bytes([FLAG])


# ===============================
# GDL90 MESSAGES
# ===============================
def gdl90_heartbeat():
    """
    Heartbeat message (0x00)
    """
    status = 0x0000
    timestamp = 0
    msg = struct.pack("<BHH",
                      MSG_HEARTBEAT,
                      status,
                      timestamp)
    return frame_gdl90(msg)


def gdl90_ownship(lat_deg, lon_deg, alt_ft, gs_kt, track_deg):
    """
    Ownship Position (0x0A)
    """
    lat = int(lat_deg * 1e7)
    lon = int(lon_deg * 1e7)
    alt = int((alt_ft + 1000) / 25)  # pressure altitude
    gs = int(gs_kt)
    track = int(track_deg)
    flags = 0x00

    msg = struct.pack("<BiiHHHB",
                      MSG_OWNHIP,
                      lat,
                      lon,
                      alt,
                      gs,
                      track,
                      flags)
    return frame_gdl90(msg)


def gdl90_traffic(icao_addr, lat_deg, lon_deg, alt_ft, gs_kt, track_deg):
    """
    Traffic Report (0x14)
    """
    lat = int(lat_deg * 1e7)
    lon = int(lon_deg * 1e7)
    alt = int((alt_ft + 1000) / 25)

    airborne = 0x01

    msg = struct.pack("<BIiiHHHB",
                      MSG_TRAFFIC,
                      icao_addr,
                      lat,
                      lon,
                      alt,
                      int(gs_kt),
                      int(track_deg),
                      airborne)
    return frame_gdl90(msg)


# ===============================
# UDP SENDER
# ===============================
def main():
    UDP_IP = "127.0.0.1"
    UDP_PORT = 4000

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("GDL90 generator running...")
    print(f"Sending to {UDP_IP}:{UDP_PORT}")

    lat = -23.5505     # São Paulo (example)
    lon = -46.6333
    alt = 3500
    track = 270
    speed = 120

    while True:
        sock.sendto(gdl90_heartbeat(), (UDP_IP, UDP_PORT))
        sock.sendto(gdl90_ownship(lat, lon, alt, speed, track), (UDP_IP, UDP_PORT))
        sock.sendto(
            gdl90_traffic(
                0xABCDEF,
                lat + 0.02,
                lon + 0.01,
                alt + 300,
                110,
                90
            ),
            (UDP_IP, UDP_PORT)
        )

        lat += 0.00005
        time.sleep(1)


# ===============================
# ENTRY POINT
# ===============================
if __name__ == "__main__":
    main()
