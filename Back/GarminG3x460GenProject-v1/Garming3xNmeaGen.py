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
# Geradores de sentenças Garmin
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
    return nmea(
        "PGRMT,GDU460 SW VER 9.12,P,P,R,R,P,,45.0,R"
    )


def gen_pgrmm():
    return nmea("PGRMM,WGS 84")


# =========================================================
# Loop de geração
# =========================================================

def generate_stream():
    lat = -23.0000
    lon = -46.0000
    alt = 2500
    course = 90.0

    while True:
        speed = random.uniform(180, 240)
        lat += 0.00005
        lon += 0.00005
        alt += random.randint(-20, 20)
        course = (course + random.uniform(-2, 2)) % 360

        yield gen_pgrmf(lat, lon, speed, course)
        yield gen_pgrme()
        yield gen_pgrmh()
        yield gen_pgrmv()
        yield gen_pgrmz(alt)
        yield gen_pgrmm()

        if int(time.time()) % 60 == 0:
            yield gen_pgrmt()

        time.sleep(1)


# =========================================================
# TCP Server fixo na porta 3100
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
# Main
# =========================================================

if __name__ == "__main__":
    tcp_server(3100)
