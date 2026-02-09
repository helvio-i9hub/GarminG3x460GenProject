#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import struct
import time
import threading

# ===============================
# GDL90 CONSTANTS
# ===============================
FLAG = 0x7E
ESC = 0x7D

MSG_HEARTBEAT = 0x00
MSG_TRAFFIC = 0x14

CRC_POLY = 0x8408
CRC_INIT = 0xFFFF


# ===============================
# CRC
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


def frame_gdl90(msg: bytes) -> bytes:
    crc = crc16_ccitt(msg)
    packet = msg + struct.pack("<H", crc)
    return bytes([FLAG]) + escape_bytes(packet) + bytes([FLAG])


# ===============================
# GDL90 MESSAGES
# ===============================
def gdl90_heartbeat():
    msg = struct.pack("<BHH", MSG_HEARTBEAT, 0x0000, 0)
    return frame_gdl90(msg)


def gdl90_traffic(icao, lat, lon, alt_ft, gs, track):
    lat_i = int(lat * 1e7)
    lon_i = int(lon * 1e7)
    alt_i = int((alt_ft + 1000) / 25)

    airborne = 0x01

    msg = struct.pack(
        "<BIiiHHHB",
        MSG_TRAFFIC,
        icao,
        lat_i,
        lon_i,
        alt_i,
        int(gs),
        int(track),
        airborne
    )
    return frame_gdl90(msg)


# ===============================
# ADS-B (SBS-1)
# ===============================
class ADSBReceiver(threading.Thread):
    def __init__(self, host, port):
        super().__init__(daemon=True)
        self.sock = socket.create_connection((host, port))
        self.aircraft = {}

    def run(self):
        buffer = ""
        while True:
            buffer += self.sock.recv(4096).decode(errors="ignore")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                self.parse_sbs(line.strip())

    def parse_sbs(self, line):
        fields = line.split(",")
        if len(fields) < 22 or fields[0] != "MSG":
            return

        icao = fields[4]
        lat = fields[14]
        lon = fields[15]
        alt = fields[11]
        gs = fields[12]
        track = fields[13]

        if not lat or not lon or not alt:
            return

        try:
            self.aircraft[int(icao, 16)] = {
                "lat": float(lat),
                "lon": float(lon),
                "alt": float(alt),
                "gs": float(gs) if gs else 0,
                "track": float(track) if track else 0,
                "time": time.time()
            }
        except ValueError:
            pass


# ===============================
# MAIN
# ===============================
def main():
    ADSB_HOST = "127.0.0.1"
    ADSB_PORT = 30003

    UDP_IP = "127.0.0.1"
    UDP_PORT = 4000

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    adsb = ADSBReceiver(ADSB_HOST, ADSB_PORT)
    adsb.start()

    print("ADS-B SDR → GDL90 Traffic")
    print("Listening ADS-B on TCP 30003")
    print("Sending GDL90 to UDP 4000")

    while True:
        udp.sendto(gdl90_heartbeat(), (UDP_IP, UDP_PORT))

        now = time.time()
        for icao, ac in list(adsb.aircraft.items()):
            if now - ac["time"] > 10:
                del adsb.aircraft[icao]
                continue

            pkt = gdl90_traffic(
                icao,
                ac["lat"],
                ac["lon"],
                ac["alt"],
                ac["gs"],
                ac["track"]
            )
            udp.sendto(pkt, (UDP_IP, UDP_PORT))

        time.sleep(1)


if __name__ == "__main__":
    main()
