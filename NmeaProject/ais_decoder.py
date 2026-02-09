from ais_fragments import collect_fragment
from ais_bits import sixbit_to_bits
from ais_utils import twos_complement


def decode_type_123(bits: str) -> dict:
    """
    AIS message types 1,2,3 – Position Report Class A
    """
    return {
        "message_type": int(bits[0:6], 2),
        "mmsi": int(bits[8:38], 2),

        "nav_status": int(bits[38:42], 2),

        "rot": twos_complement(int(bits[42:50], 2), 8),

        "sog": int(bits[50:60], 2) / 10.0,

        "position_accuracy": int(bits[60], 2),

        "longitude": twos_complement(int(bits[61:89], 2), 28) / 600000.0,
        "latitude": twos_complement(int(bits[89:116], 2), 27) / 600000.0,

        "cog": int(bits[116:128], 2) / 10.0,

        "heading": int(bits[128:137], 2),

        "timestamp": int(bits[137:143], 2),
    }


def decode_payload(payload: str) -> dict | None:
    """
    Decodes AIS 6-bit payload into a dict
    """
    bits = sixbit_to_bits(payload)

    msg_type = int(bits[0:6], 2)

    if msg_type in (1, 2, 3):
        return decode_type_123(bits)

    # Tipos não implementados ainda
    return None


def decode_ais(sentence: str) -> dict | None:
    """
    Main AIS decoder entry point.
    Handles fragmentation and decoding.
    """
    payload = collect_fragment(sentence)

    # ainda aguardando fragmentos
    if payload is None:
        return None

    try:
        return decode_payload(payload)
    except Exception:
        return None
