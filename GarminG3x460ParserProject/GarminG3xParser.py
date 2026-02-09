import re
import socket
import serial
from typing import Dict, Any, Optional, Generator


# ============================================================
# Parser NMEA Unificado
#  - Garmin Proprietary (PGRM*)
#  - NMEA 0183 padrão (GP / GN / GL)
# ============================================================

class NMEAParser:

    nmea_re = re.compile(r'^\$(?P<body>[^*]+)(\*(?P<cs>[0-9A-F]{2}))?$')

    # --------------------------------------------------------
    # Utilidades
    # --------------------------------------------------------

    @staticmethod
    def calc_checksum(data: str) -> int:
        c = 0
        for ch in data:
            c ^= ord(ch)
        return c

    def checksum_ok(self, sentence: str) -> bool:
        m = self.nmea_re.match(sentence.strip())
        if not m or not m.group("cs"):
            return True
        return int(m.group("cs"), 16) == self.calc_checksum(m.group("body"))

    @staticmethod
    def dm_to_deg(dm: str, hemi: str) -> Optional[float]:
        if not dm:
            return None
        deg = int(dm[:-7])
        minutes = float(dm[-7:])
        val = deg + minutes / 60.0
        return -val if hemi in ("S", "W") else val

    # --------------------------------------------------------
    # Dispatcher principal
    # --------------------------------------------------------

    def parse(self, sentence: str) -> Optional[Dict[str, Any]]:
        sentence = sentence.strip()
        m = self.nmea_re.match(sentence)
        if not m:
            return None

        body = m.group("body")
        fields = body.split(",")
        sid = fields[0]

        base = {
            "raw": sentence,
            "sentence": sid,
            "checksum_ok": self.checksum_ok(sentence),
        }

        # Garmin Proprietary
        if sid.startswith("PGRM"):
            base["protocol"] = "garmin"
            base.update(self.parse_garmin(sid, fields[1:]))
            return base

        # NMEA padrão
        talker = sid[:2]
        msg = sid[2:]

        if talker in ("GP", "GN", "GL"):
            base["protocol"] = "nmea0183"
            base["talker"] = talker
            base.update(self.parse_standard(msg, fields[1:]))
            return base

        return None

    # ========================================================
    # Garmin Proprietary (190-00684-00 Rev. C)
    # ========================================================

    def parse_garmin(self, sid: str, f):
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
        return handlers.get(sid, lambda _: {})(f)

    def pgrme(self, f):
        return {"hpe_m": float(f[0]), "vpe_m": float(f[2]), "epe_m": float(f[4])}

    def pgrmf(self, f):
        return {
            "gps_week": int(f[0]),
            "gps_seconds": int(f[1]),
            "utc_date": f[2],
            "utc_time": f[3],
            "leap_seconds": int(f[4]),
            "lat": self.dm_to_deg(f[5], f[6]),
            "lon": self.dm_to_deg(f[7], f[8]),
            "mode": f[9],
            "fix_type": int(f[10]),
            "speed_kmh": float(f[11]),
            "course_deg": float(f[12]),
            "pdop": int(f[13]),
            "tdop": int(f[14]),
        }

    def pgrmh(self, f):
        return {
            "valid": f[0] == "A",
            "vertical_speed_fpm": int(f[1]),
            "vnav_error_ft": int(f[2]),
            "vnav_vs_fpm": int(f[3]),
            "next_wp_vs_fpm": int(f[4]),
            "terrain_ft": int(f[5]),
            "desired_track_deg": float(f[6]),
            "next_leg_course_deg": float(f[7]),
        }

    def pgrmm(self, f):
        return {"map_datum": f[0]}

    def pgrmt(self, f):
        return {
            "product": f[0],
            "rom_test": f[1],
            "receiver_failure": f[2],
            "stored_data": f[3],
            "rtc": f[4],
            "oscillator": f[5],
            "collecting": f[6] or None,
            "temperature_c": float(f[7]),
            "config_data": f[8],
        }

    def pgrmv(self, f):
        return {
            "vel_e_mps": float(f[0]),
            "vel_n_mps": float(f[1]),
            "vel_up_mps": float(f[2]),
        }

    def pgrmz(self, f):
        return {"altitude_ft": int(f[0]), "fix_type": int(f[2])}

    def pgrmb(self, f):
        return {
            "beacon_freq_khz": float(f[0]),
            "bitrate_bps": int(f[1]),
            "snr": int(f[2]),
            "quality": int(f[3]),
            "distance_km": float(f[4]),
            "receiver_status": int(f[6]),
            "dgps_source": f[7],
            "dgps_mode": f[8],
        }

    # ========================================================
    # NMEA 0183 padrão
    # ========================================================

    def parse_standard(self, msg: str, f):
        return {
            "RMC": self.rmc,
            "GGA": self.gga,
            "VTG": self.vtg,
            "GSA": self.gsa,
            "GSV": self.gsv,
            "GLL": self.gll,
        }.get(msg, lambda _: {})(f)

    def rmc(self, f):
        return {
            "utc_time": f[0],
            "status": f[1],
            "lat": self.dm_to_deg(f[2], f[3]),
            "lon": self.dm_to_deg(f[4], f[5]),
            "speed_knots": float(f[6]) if f[6] else None,
            "course_deg": float(f[7]) if f[7] else None,
            "date": f[8],
        }

    def gga(self, f):
        return {
            "utc_time": f[0],
            "lat": self.dm_to_deg(f[1], f[2]),
            "lon": self.dm_to_deg(f[3], f[4]),
            "fix_quality": int(f[5]) if f[5] else None,
            "satellites": int(f[6]) if f[6] else None,
            "hdop": float(f[7]) if f[7] else None,
            "altitude_m": float(f[8]) if f[8] else None,
        }

    def vtg(self, f):
        return {
            "course_true": float(f[0]) if f[0] else None,
            "speed_knots": float(f[4]) if f[4] else None,
            "speed_kmh": float(f[6]) if f[6] else None,
        }

    def gsa(self, f):
        return {
            "mode": f[0],
            "fix_type": int(f[1]) if f[1] else None,
            "pdop": float(f[14]) if len(f) > 14 and f[14] else None,
            "hdop": float(f[15]) if len(f) > 15 and f[15] else None,
            "vdop": float(f[16]) if len(f) > 16 and f[16] else None,
        }

    def gsv(self, f):
        return {
            "total_msgs": int(f[0]),
            "msg_num": int(f[1]),
            "sats_in_view": int(f[2]),
        }

    def gll(self, f):
        return {
            "lat": self.dm_to_deg(f[0], f[1]),
            "lon": self.dm_to_deg(f[2], f[3]),
            "utc_time": f[4],
            "status": f[5],
        }


# ============================================================
# Fontes de dados (TCP / Serial / Log)
# ============================================================

def source_tcp(host: str, port: int) -> Generator[str, None, None]:
    sock = socket.create_connection((host, port))
    f = sock.makefile()
    while True:
        line = f.readline()
        if not line:
            break
        yield line.strip()


def source_serial(port: str, baud: int = 9600) -> Generator[str, None, None]:
    ser = serial.Serial(port, baudrate=baud, timeout=1)
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            yield line


def source_log(path: str) -> Generator[str, None, None]:
    with open(path, "r", errors="ignore") as f:
        for line in f:
            yield line.strip()


# ============================================================
# Main
# ============================================================

def run(source: Generator[str, None, None]):
    parser = NMEAParser()
    for line in source:
        msg = parser.parse(line)
        if msg:
            print(msg)


if __name__ == "__main__":

    MODE = "tcp"      # tcp | serial | log

    if MODE == "tcp":
        run(source_tcp("127.0.0.1", 3100))

    elif MODE == "serial":
        run(source_serial("/dev/ttyUSB0", 9600))

    elif MODE == "log":
        run(source_log("nmea.log"))
