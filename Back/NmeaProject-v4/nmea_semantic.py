from nmea_utils import dm_to_decimal


def parse_gga(fields):
    try:
        return {
            "latitude": dm_to_decimal(fields[1], fields[2]),
            "longitude": dm_to_decimal(fields[3], fields[4]),
            "fix_quality": int(fields[5]) if fields[5] else None,
            "satellites_count": int(fields[6]) if fields[6] else None,
            "hdop": float(fields[7]) if fields[7] else None,
            "altitude": float(fields[8]) if fields[8] else None,
        }
    except Exception:
        return {}


def parse_rmc(fields):
    try:
        return {
            "status": fields[1],  # A = válido, V = inválido
            "latitude": dm_to_decimal(fields[2], fields[3]),
            "longitude": dm_to_decimal(fields[4], fields[5]),
            "speed_knots": float(fields[6]) if fields[6] else None,
            "course": float(fields[7]) if fields[7] else None,
            "date": fields[8],  # DDMMYY
            "mode": fields[11] if len(fields) > 11 else None,
        }
    except Exception:
        return {}

def parse_vtg(fields):
    try:
        return {
            "course_true": float(fields[0]) if fields[0] else None,
            "course_magnetic": float(fields[2]) if fields[2] else None,
            "speed_knots": float(fields[4]) if fields[4] else None,
            "speed_kmh": float(fields[6]) if fields[6] else None,
        }
    except Exception:
        return {}

def parse_gsa(fields):
    try:
        sats = [s for s in fields[2:14] if s]

        return {
            "mode": fields[0],
            "fix_type": int(fields[1]) if fields[1] else None,
            "satellites_used": sats,
            "pdop": float(fields[14]) if fields[14] else None,
            "hdop": float(fields[15]) if fields[15] else None,
            "vdop": float(fields[16]) if fields[16] else None,
        }
    except Exception:
        return {}
