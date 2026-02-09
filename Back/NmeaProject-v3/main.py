import psycopg2
from psycopg2.extras import Json

from config import DB_CONFIG, USE_SOURCE, TCP_CONFIG, SERIAL_CONFIG
from nmea_reader import tcp_reader, serial_reader
from nmea_stream import extract_nmea_sentences
from nmea_checksum import validate_checksum
from nmea_parser import parse_nmea
from ais_decoder import decode_ais


# =========================
# Database connection
# =========================
conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = True
cur = conn.cursor()


# =========================
# Database helpers
# =========================
def save_raw(sentence: str) -> int:
    cur.execute(
        "INSERT INTO nmea_raw (sentence) VALUES (%s) RETURNING id",
        (sentence,)
    )
    return cur.fetchone()[0]


def save_parsed(raw_id: int, parsed: dict):
    sem = parsed.get("semantic", {})

    cur.execute(
        """
        INSERT INTO nmea_parsed
        (raw_id, talker, sentence_type, fields,
         latitude, longitude, altitude,
         fix_quality, satellites, hdop)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            raw_id,
            parsed["talker"],
            parsed["sentence_type"],
            Json(parsed["fields"]),
            sem.get("latitude"),
            sem.get("longitude"),
            sem.get("altitude"),
            sem.get("fix_quality"),
            sem.get("satellites"),
            sem.get("hdop"),
        )
    )


def save_ais(raw_id: int, ais: dict):
    cur.execute(
        """
        INSERT INTO ais_messages
        (raw_id, message_type, mmsi, latitude, longitude,
         sog, cog, heading, nav_status, raw)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            raw_id,
            ais.get("message_type"),
            ais.get("mmsi"),
            ais.get("latitude"),
            ais.get("longitude"),
            ais.get("sog"),
            ais.get("cog"),
            ais.get("heading"),
            ais.get("nav_status"),
            Json(ais),
        )
    )


# =========================
# Select data source
# =========================
if USE_SOURCE == "TCP":
    reader = tcp_reader(TCP_CONFIG["host"], TCP_CONFIG["port"])
    print("📡 Fonte: TCP", TCP_CONFIG)
else:
    reader = serial_reader(
        SERIAL_CONFIG["port"],
        SERIAL_CONFIG["baudrate"],
        SERIAL_CONFIG["timeout"]
    )
    print("📡 Fonte: SERIAL", SERIAL_CONFIG)


# =========================
# Main loop (stream-safe)
# =========================
buffer = ""

print("🚀 NMEA + AIS receiver iniciado\n")

for chunk in reader:
    # chunk pode conter lixo + várias mensagens
    buffer += chunk

    sentences = extract_nmea_sentences(buffer)

    for sentence in sentences:
        buffer = buffer.replace(sentence, "", 1)

        if not validate_checksum(sentence):
            print("❌ Checksum inválido:", sentence)
            continue

        print("NMEA >>>", sentence)

        # 1) salva bruto
        raw_id = save_raw(sentence)

        # 2) AIS (VDM / VDO)
        if sentence.startswith("!AIVDM") or sentence.startswith("!AIVDO"):
            ais = decode_ais(sentence)
            if ais:
                save_ais(raw_id, ais)
                print("🚢 AIS:", ais)
            continue

        # 3) NMEA semântico
        parsed = parse_nmea(sentence)
        if parsed:
            save_parsed(raw_id, parsed)
