from ais_utils import get_int

def decode_type123(bits):
    return {
        "message_type": get_int(bits, 0, 6),
        "mmsi": get_int(bits, 8, 30),
        "nav_status": get_int(bits, 38, 4),
        "sog": get_int(bits, 50, 10) / 10.0,
        "longitude": get_int(bits, 61, 28, signed=True) / 600000.0,
        "latitude": get_int(bits, 89, 27, signed=True) / 600000.0,
        "cog": get_int(bits, 116, 12) / 10.0,
        "heading": get_int(bits, 128, 9),
    }
