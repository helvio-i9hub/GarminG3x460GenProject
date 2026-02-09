import re
import csv

INPUT_FILE = "putty.log.txt"
TRACK_CSV = "flight_track.csv"
ENGINE_CSV = "engine_data.csv"

sensor_map = {}      # ID -> sensor name
last_time = None     # HH:MM:SS vindo do GPS (@)

# -------------------------------------------------
# GPS
# -------------------------------------------------
def parse_gps(line):
    global last_time
    m = re.match(
        r"@(\d{2})(\d{2})(\d{2})"
        r"(\d{2})(\d{2})(\d{2})"
        r"([NS])(\d{2})(\d{5})"
        r"([EW])(\d{3})(\d{5}).*?([+-]\d{5})",
        line
    )
    if not m:
        return None

    day, month, year, hh, mm, ss = m.group(1,2,3,4,5,6)
    ns, lat_d, lat_m = m.group(7,8,9)
    ew, lon_d, lon_m = m.group(10,11,12)
    alt = int(m.group(13))

    last_time = f"{hh}:{mm}:{ss}"
    date = f"20{year}-{month}-{day}"

    lat = int(lat_d) + int(lat_m) / 1000 / 60
    lon = int(lon_d) + int(lon_m) / 1000 / 60
    if ns == "S": lat *= -1
    if ew == "W": lon *= -1

    return [date, last_time, lat, lon, alt]

# -------------------------------------------------
# Sensor map (=51i)
# -------------------------------------------------
def parse_sensor_map(line):
    # captura pares: ID + NOME
    for m in re.finditer(r"(\d{2})([A-Z0-9]+)", line):
        sensor_map[m.group(1)] = m.group(2)

# -------------------------------------------------
# Engine values (=51)
# -------------------------------------------------
def parse_engine(line):
    rows = []
    for m in re.finditer(r"(\d{2})([+-]\d\.\d+E[+-]\d{2})", line):
        sid = m.group(1)
        value = float(m.group(2))
        name = sensor_map.get(sid)

        if name and last_time:
            rows.append([last_time, name, value])
    return rows

# -------------------------------------------------
# MAIN
# -------------------------------------------------
with open(TRACK_CSV, "w", newline="") as f_track, \
     open(ENGINE_CSV, "w", newline="") as f_engine:

    track_writer = csv.writer(f_track)
    engine_writer = csv.writer(f_engine)

    track_writer.writerow(["date", "time", "lat", "lon", "alt_ft"])
    engine_writer.writerow(["time", "sensor", "value"])

    with open(INPUT_FILE) as f:
        for line in f:
            line = line.strip()

            if line.startswith("@"):
                row = parse_gps(line)
                if row:
                    track_writer.writerow(row)
                    print(row)

            elif line.startswith("=51i"):
                parse_sensor_map(line)

            elif line.startswith("=51") and not line.startswith("=51i"):
                for r in parse_engine(line):
                    print(r)
                    engine_writer.writerow(r)

print("----------------------------------------------------------------------")
print("✔ CSV gerados com EGT / CHT completos")
print(" - flight_track.csv")
print(" - engine_data.csv")
print("----------------------------------------------------------------------")
