from ais_bits import payload_to_bits
from ais_type123 import decode_type123
from ais_fragments import handle_fragment

def decode_ais(sentence):
    fields = sentence.split(",")

    payload, fill = handle_fragment(fields)
    if not payload:
        return None

    bits = payload_to_bits(payload)
    msg_type = int(bits[0:6], 2)

    if msg_type in (1, 2, 3):
        return decode_type123(bits)

    return None  # outros tipos podem ser adicionados
