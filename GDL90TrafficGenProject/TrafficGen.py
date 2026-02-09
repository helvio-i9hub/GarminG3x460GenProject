import socket
import struct
import time
import math
import random


UDP_IP = "127.0.0.1"
UDP_PORT = 4000


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


def escape_gdl90(data):
    out = bytearray()
    for b in data:
        if b == 0x7E:
            out += b'\x7D\x5E'
        elif b == 0x7D:
            out += b'\x7D\x5D'
        else:
            out.append(b)
    return bytes(out)


def encode_latlon(deg):
    return int(deg * (2**24 / 180))


def build_traffic_report(
    icao,
    lat,
    lon,
    alt_ft,
    track_deg,
    speed_kt,
    climb_fpm
):
    msg_id = 0x14

    lat_enc = encode_latlon(lat)
    lon_enc = encode_latlon(lon)
    alt_enc = int((alt_ft + 1000) / 25)

    payload = struct.pack(
        ">B I i i H H h B B",
        msg_id,
        icao & 0xFFFFFF,
        lat_enc,
        lon_enc,
        alt_enc & 0x0FFF,
        int(speed_kt),
        int(climb_fpm),
        int(track_deg / 360 * 256),
        0x01   # NIC/NAC placeholder
    )

    crc = crc16_ccitt(payload)
    frame = payload + struct.pack("<H", crc)

    return b'\x7E' + escape_gdl90(frame) + b'\x7E'


def generate_traffic():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Initial aircraft state
    lat = -23.5505     # São Paulo
    lon = -46.6333
    alt = 5500         # feet
    speed = 120        # knots
    track = 45         # degrees
    climb = 0
    icao = random.randint(0x100000, 0xFFFFFF)

    print(f"Generating traffic ICAO={icao:06X}")

    while True:
        # Move aircraft
        dt = 1.0
        dist_nm = speed * dt / 3600.0

        lat += dist_nm * math.cos(math.radians(track)) / 60
        lon += dist_nm * math.sin(math.radians(track)) / (60 * math.cos(math.radians(lat)))

        frame = build_traffic_report(
            icao,
            lat,
            lon,
            alt,
            track,
            speed,
            climb
        )

        sock.sendto(frame, (UDP_IP, UDP_PORT))
        time.sleep(dt)


if __name__ == "__main__":
    generate_traffic()
