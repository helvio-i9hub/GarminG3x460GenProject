def ais_char_to_sixbit(c):
    v = ord(c) - 48
    if v > 40:
        v -= 8
    return format(v, "06b")

def payload_to_bits(payload):
    return "".join(ais_char_to_sixbit(c) for c in payload)
"""
AIS 6-bit ASCII to bitstream conversion
"""

def sixbit_to_bits(payload: str) -> str:
    """
    Converts AIS 6-bit encoded payload into a bit string
    """

    bits = ""

    for char in payload:
        val = ord(char) - 48
        if val > 40:
            val -= 8

        bits += format(val, "06b")

    return bits
