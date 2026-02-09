import psycopg2
from psycopg2.extras import Json
from config import *
from nmea_reader import tcp_reader, serial_reader
from nmea_parser import parse_nmea

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

def save_raw(sentence):
    cur.execute(
        "INSERT INTO nmea_raw (sentence) VALUES (%s) RETURNING id",
        (sentence,)
    )
    raw_id = cur.fetchone()[0]
    conn.commit()
    return raw_id

from psycopg2.extras import Json

def save_parsed(raw_id, parsed):
    sem = parsed["semantic"]

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
            sem.get("hdop")
        )
    )



if USE_SOURCE == "TCP":
    reader = tcp_reader(TCP_CONFIG["host"], TCP_CONFIG["port"])
else:
    reader = serial_reader(
        SERIAL_CONFIG["port"],
        SERIAL_CONFIG["baudrate"],
        SERIAL_CONFIG["timeout"]
    )

print("📡 Lendo mensagens NMEA 0183...\n")

import nmea_stream
from nmea_stream import extract_nmea_sentences
from nmea_checksum import validate_checksum

buffer = ""

for chunk in reader:
    print("CHUNK >>>", repr(chunk))

    buffer += chunk

    sentences = extract_nmea_sentences(buffer)

    for s in sentences:
        if not validate_checksum(s):
            print("❌ Invalid checksum:", s)
            continue

        print("NMEA >>>", s)

        raw_id = save_raw(s)
        parsed = parse_nmea(s)
        save_parsed(raw_id, parsed)

        buffer = buffer.replace(s, "", 1)
