import time
import random
import socket
from datetime import datetime

# =========================================================
# Utilidades NMEA
# =========================================================

def checksum(sentence: str) -> str:
    c = 0
    for ch in sentence:
        c ^= ord(ch)
    return f"{c:02X}"


def nmea(msg: str) -> str:
    return f"${msg}*{checksum(msg)}"


def dm(value: float, is_lat=True):
    deg = int(abs(value))
    minutes = (abs(value) - deg) * 60
    if is_lat:
        return f"{deg:02d}{minutes:07.4f}"
    return f"{deg:03d}{minutes:07.4f}"


# =========================================================
# NMEA 0183 PADRÃO
# =========================================================

def gen_gprmc(lat, lon, speed_kts, course):
    now = datetime.utcnow()
    return nmea(
        f"GPRMC,{now:%H%M%S},A,"
        f"{dm(lat,True)},{'N' if lat>=0 else 'S'},"
        f"{dm(lon,False)},{'E' if lon>=0 else 'W'},"
        f"{speed_kts:.1f},{course:.1f},"
        f"{now:%d%m%y},,,A"
    )


def gen_gpgga(lat, lon, alt_m):
    now = datetime.utcnow()
    return nmea(
        f"GPGGA,{now:%H%M%S},"
        f"{dm(lat,True)},{'N' if lat>=0 else 'S'},"
        f"{dm(lon,False)},{'E' if lon>=0 else 'W'},"
        f"1,08,0.9,{alt_m:.1f},M,0.0,M,,"
    )


def gen_gpvtg(course, speed_kts):
    speed_kmh = speed_kts * 1.852
    return nmea(
        f"GPVTG,{course:.1f},T,,M,"
        f"{speed_kts:.1f},N,{speed_kmh:.1f},K,A"
    )


def gen_gpgsa():
    return nmea(
        "GPGSA,A,3,"
        "01,02,03,04,05,06,07,08,,,,"
        "1.5,0.9,1.2"
    )


def gen_gpgsv():
    sats = []
    for prn in range(1, 5):
        sats.append(
            f"{prn:02d},{random.randint(10,80)},"
            f"{random.randint(0,359)},"
            f"{random.randint(20,50)}"
        )
    return nmea(f"GPGSV,1,1,04," + ",".join(sats))


# =========================================================
# GARMIN PROPRIETÁRIO
# =========================================================

def gen_pgrmf(lat, lon, speed_kmh, course):
    now = datetime.utcnow()
    gps_week = 2200
    gps_sec = int(time.time()) % 604800

    return nmea(
        f"PGRMF,{gps_week},{gps_sec},"
        f"{now:%d%m%y},{now:%H%M%S},18,"
        f"{dm(lat, True)},{'N' if lat >= 0 else 'S'},"
        f"{dm(lon, False)},{'E' if lon >= 0 else 'W'},"
        f"A,2,{speed_kmh:.1f},{course:.1f},1,1"
    )


def gen_pgrme():
    h = random.uniform(1, 10)
    v = random.uniform(2, 15)
    e = (h + v) / 2
    return nmea(f"PGRME,{h:.1f},M,{v:.1f},M,{e:.1f},M")


def gen_pgrmh():
    vs = random.randint(-500, 500)
    return nmea(
        f"PGRMH,A,{vs},{random.randint(-50,50)},"
        f"{vs},{vs},{random.randint(0,5000)},"
        f"{random.uniform(0,359):.1f},{random.uniform(0,359):.1f}"
    )


def gen_pgrmv():
    return nmea(
        f"PGRMV,"
        f"{random.uniform(-50,50):.2f},"
        f"{random.uniform(-50,50):.2f},"
        f"{random.uniform(-10,10):.2f}"
    )


def gen_pgrmz(alt_ft):
    return nmea(f"PGRMZ,{int(alt_ft)},f,3")


def gen_pgrmt():
    return nmea("PGRMT,GDU460 SW VER 9.12,P,P,R,R,P,,45.0,R")


def gen_pgrmm():
    return nmea("PGRMM,WGS 84")


# =========================================================
# GERADOR PRINCIPAL
# =========================================================

def generate_stream():
    lat = -23.0000
    lon = -46.0000
    alt_ft = 2500
    course = 90.0

    while True:
        speed_kts = random.uniform(95, 130)
        speed_kmh = speed_kts * 1.852

        lat += 0.00005
        lon += 0.00005
        alt_ft += random.randint(-20, 20)
        course = (course + random.uniform(-2, 2)) % 360

        alt_m = alt_ft * 0.3048

        # NMEA padrão
        yield gen_gprmc(lat, lon, speed_kts, course)
        yield gen_gpgga(lat, lon, alt_m)
        yield gen_gpvtg(course, speed_kts)
        yield gen_gpgsa()
        yield gen_gpgsv()

        # Garmin proprietário
        yield gen_pgrmf(lat, lon, speed_kmh, course)
        yield gen_pgrme()
        yield gen_pgrmh()
        yield gen_pgrmv()
        yield gen_pgrmz(alt_ft)
        yield gen_pgrmm()

        if int(time.time()) % 60 == 0:
            yield gen_pgrmt()

        time.sleep(1)


# =========================================================
# TCP SERVER
# =========================================================

def tcp_server(port=3100):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", port))
    srv.listen(1)

    print(f"[GARMIN G3X SIM] TCP server ativo na porta {port}")

    conn, addr = srv.accept()
    print(f"[GARMIN G3X SIM] Cliente conectado: {addr}")

    try:
        for msg in generate_stream():
            conn.sendall((msg + "\r\n").encode("ascii"))
    except (BrokenPipeError, ConnectionResetError):
        print("[GARMIN G3X SIM] Cliente desconectado")
    finally:
        conn.close()
        srv.close()


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    tcp_server(3100)
