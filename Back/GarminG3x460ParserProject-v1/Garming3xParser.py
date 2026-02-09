import re
import socket
import serial
import time
from typing import Dict, Any, Generator, Optional


# =========================================================
# Garmin Proprietary NMEA Parser (PGRM*)
# =========================================================

class GarminNMEAParser:
    nmea_re = re.compile(r'^\$(?P<body>[^*]+)(\*(?P<cs>[0-9A-F]{2}))?$')

    @staticmethod
    def checksum(data: str) -> int:
        c = 0
        for ch in data:
            c ^= ord(ch)
        return c

    def checksum_ok(self, sentence: str) -> bool:
        m = self.nmea_re.match(sentence.strip())
        if not m or not m.group("cs"):
            return True
        return int(m.group("cs"), 16) == self.checksum(m.group("body"))

    def parse(self, sentence: str) -> Optional[Dict[str, Any]]:
        print("parse")
        m = self.nmea_re.match(sentence.strip())
        if not m:
            return None

        body = m.group("body")
        fields = body.split(",")
        sid = fields[0]

        if not sid.startswith("PGRM"):
            return None

        base = {
            "sentence": sid,
            "checksum_ok": self.checksum_ok(sentence),
            "raw": sentence.strip(),
        }

        handlers = {
            "PGRME": self.pgrme,
            "PGRMF": self.pgrmf,
            "PGRMH": self.pgrmh,
            "PGRMM": self.pgrmm,
            "PGRMT": self.pgrmt,
            "PGRMV": self.pgrmv,
            "PGRMZ": self.pgrmz,
            "PGRMB": self.pgrmb,
        }

        if sid in handlers:
            base.update(handlers[sid](fields[1:]))

        return base

    # ---------------- Parsers ----------------

    def pgrme(self, f):
        return {
            "hpe_m": float(f[0]),
            "vpe_m": float(f[2]),
            "epe_m": float(f[4]),
        }

    def pgrmf(self, f):
        return {
            "gps_week": int(f[0]),
            "gps_seconds": int(f[1]),
            "utc_date": f[2],
            "utc_time": f[3],
            "leap_seconds": int(f[4]),
            "lat": self.dm(f[5], f[6]),
            "lon": self.dm(f[7], f[8]),
            "mode": f[9],
            "fix": int(f[10]),
            "speed_kmh": float(f[11]),
            "course_deg": float(f[12]),
            "pdop": int(f[13]),
            "tdop": int(f[14]),
        }

    def pgrmh(self, f):
        return {
            "valid": f[0] == "A",
            "vs_fpm": int(f[1]),
            "vnav_err_ft": int(f[2]),
            "vnav_vs_fpm": int(f[3]),
            "next_wp_vs_fpm": int(f[4]),
            "terrain_ft": int(f[5]),
            "desired_track": float(f[6]),
            "next_leg_course": float(f[7]),
        }

    def pgrmm(self, f):
        return {"datum": f[0]}

    def pgrmt(self, f):
        return {
            "product": f[0],
            "rom": f[1],
            "receiver": f[2],
            "stored_data": f[3],
            "rtc": f[4],
            "oscillator": f[5],
            "collecting": f[6] or None,
            "temp_c": float(f[7]),
            "config": f[8],
        }

    def pgrmv(self, f):
        return {
            "ve_mps": float(f[0]),
            "vn_mps": float(f[1]),
            "vu_mps": float(f[2]),
        }

    def pgrmz(self, f):
        return {
            "altitude_ft": int(f[0]),
            "fix_type": int(f[2]),
        }

    def pgrmb(self, f):
        return {
            "freq_khz": float(f[0]),
            "bitrate": int(f[1]),
            "snr": int(f[2]),
            "quality": int(f[3]),
            "dist_km": float(f[4]),
            "rx_status": int(f[6]),
            "dgps_src": f[7],
            "dgps_mode": f[8],
        }

    @staticmethod
    def dm(dm: str, hemi: str) -> Optional[float]:
        if not dm:
            return None
        deg = int(dm[:-7])
        minutes = float(dm[-7:])
        v = deg + minutes / 60.0
        return -v if hemi in ("S", "W") else v


# =========================================================
# Fontes de dados
# =========================================================

def source_log(path: str) -> Generator[str, None, None]:
    print("source_log")
    with open(path, "r", errors="ignore") as f:
        for line in f:
            yield line.strip()


def source_serial(port: str, baud: int = 4800) -> Generator[str, None, None]:
    ser = serial.Serial(port, baud, timeout=1)
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            yield line


def source_tcp(host: str, port: int) -> Generator[str, None, None]:
    sock = socket.create_connection((host, port))
    f = sock.makefile()
    while True:
        line = f.readline().strip()
        if line:
            yield line


# =========================================================
# Main
# =========================================================

def run(source: Generator[str, None, None]):
    print("run")
    parser = GarminNMEAParser()
    for line in source:
        msg = parser.parse(line)
        if msg:
            print(msg)


if __name__ == "__main__":

    MODE = "tcp"      # log | serial | tcp

    if MODE == "log":
        print("Mode log")
        run(source_log("/home/helvio/Downloads/putty.log.txt"))

    elif MODE == "serial":
        run(source_serial("/dev/ttyUSB0", 9600))

    elif MODE == "tcp":
        run(source_tcp("127.0.0.1", 3100))
