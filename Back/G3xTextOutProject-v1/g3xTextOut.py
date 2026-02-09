#!/usr/bin/env python3
"""
Garmin G3X 460 - TEXT OUT decoder
Input : putty.log
Output: flight.csv, flight.gpx, flight.json

Autor: uso experimental / engenharia reversa
"""

from dataclasses import dataclass, asdict
from datetime import datetime
import json
import re

# ============================================================
# Data model
# ============================================================

@dataclass
class FlightSample:
    time_utc: datetime
    lat: float
    lon: float
    alt_gps_ft: int
    alt_baro_ft: int | None = None
    ias_kt: int | None = None
    heading_deg: float | None = None
    rpm: int | None = None


# ============================================================
# Parsers
# ============================================================

def parse_gps(line: str):
    """
    Example:
    @260204200004S2251518W04706678G003+00630E0000N0000U0000
    """
    print("parse_gps")
    try:
        day   = int(line[1:3])
        month = int(line[3:5])
        year  = 2000 + int(line[5:7])
        hour  = int(line[7:9])
        minute= int(line[9:11])
        sec   = int(line[11:13])

        lat_hem = line[13]
        lat_deg = int(line[14:16])
        lat_min = int(line[16:18])
        lat_sec = int(line[18:21])
        lat = lat_deg + lat_min / 60 + (lat_sec / 1000) / 60
        if lat_hem == 'S':
            lat = -lat

        lon_hem = line[21]
        lon_deg = int(line[22:25])
        lon_min = int(line[25:27])
        lon_sec = int(line[27:30])
        lon = lon_deg + lon_min / 60 + (lon_sec / 1000) / 60
        if lon_hem == 'W':
            lon = -lon

        alt_gps = int(line[34:39])

        t = datetime(year, month, day, hour, minute, sec)
        return t, lat, lon, alt_gps

    except Exception:
        return None


def parse_main_frame(line: str):
    """
    Frame starting with '1' or '3'
    Extracts baro altitude, heading, IAS, RPM (best effort)
    """
    print("parse_main_frame")
    alt_baro = heading = ias = rpm = None

    try:
        # Barometric altitude (offset-based)
        if line[10:17].strip():
            alt_baro = int(line[10:17])

        # Heading (hundredths of degree)
        if line[21:27].strip():
            heading = int(line[21:27]) / 100.0

        # IAS (look for +NNNNT)
        m = re.search(r"\+(\d{3,4})T", line)
        if m:
            ias = int(m.group(1))

        # RPM (heuristic: +02xxx or +03xxx)
        m = re.search(r"\+0([12]\d{3})", line)
        if m:
            rpm = int(m.group(1))

    except Exception:
        pass

    return alt_baro, heading, ias, rpm


# ============================================================
# Exporters
# ============================================================

def export_csv(samples, filename="flight.csv"):
    with open(filename, "w") as f:
        f.write("time_utc,lat,lon,alt_gps_ft,alt_baro_ft,ias_kt,heading_deg,rpm\n")
        for s in samples:
            f.write(
                f"{s.time_utc.isoformat()},"
                f"{s.lat:.6f},{s.lon:.6f},"
                f"{s.alt_gps_ft},"
                f"{s.alt_baro_ft or ''},"
                f"{s.ias_kt or ''},"
                f"{s.heading_deg or ''},"
                f"{s.rpm or ''}\n"
            )


def export_gpx(samples, filename="flight.gpx"):
    with open(filename, "w") as f:
        f.write('<?xml version="1.0"?>\n')
        f.write('<gpx version="1.1" creator="G3X TEXT OUT Decoder">\n')
        f.write('<trk><name>Garmin G3X Flight</name><trkseg>\n')

        for s in samples:
            f.write(
                f'<trkpt lat="{s.lat}" lon="{s.lon}">'
                f'<ele>{s.alt_gps_ft * 0.3048:.1f}</ele>'
                f'<time>{s.time_utc.isoformat()}Z</time>'
                '</trkpt>\n'
            )

        f.write('</trkseg></trk>\n</gpx>')


def export_json(samples, filename="flight.json"):
    with open(filename, "w") as f:
        json.dump(
            [
                {**asdict(s), "time_utc": s.time_utc.isoformat()}
                for s in samples
            ],
            f,
            indent=2
        )


# ============================================================
# Main
# ============================================================

def main():
    samples = []
    last_main = {}

    with open("/home/helvio/Downloads/putty.log.txt", "r", errors="ignore") as f:
        for line in f:
            line = line.rstrip()

            if not line:
                continue

            # Main frame
            if line[0] in ("1", "3"):
                alt_baro, heading, ias, rpm = parse_main_frame(line)
                last_main = {
                    "alt_baro": alt_baro,
                    "heading": heading,
                    "ias": ias,
                    "rpm": rpm,
                }

            # GPS frame
            elif line.startswith("@"):
                gps = parse_gps(line)
                if not gps:
                    continue

                t, lat, lon, alt_gps = gps

                sample = FlightSample(
                    time_utc=t,
                    lat=lat,
                    lon=lon,
                    alt_gps_ft=alt_gps,
                    alt_baro_ft=last_main.get("alt_baro"),
                    ias_kt=last_main.get("ias"),
                    heading_deg=last_main.get("heading"),
                    rpm=last_main.get("rpm"),
                )

                samples.append(sample)

    if not samples:
        print("Nenhuma amostra válida encontrada.")
        return

    export_csv(samples)
    export_gpx(samples)
    export_json(samples)

    print(f"OK - {len(samples)} pontos exportados")
    print("Arquivos gerados: flight.csv, flight.gpx, flight.json")


if __name__ == "__main__":
    main()
