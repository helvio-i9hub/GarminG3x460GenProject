def ais_char_to_sixbit(c):
    v = ord(c) - 48
    if v > 40:
        v -= 8
    return format(v, "06b")

def payload_to_bits(payload):
    return "".join(ais_char_to_sixbit(c) for c in payload)
