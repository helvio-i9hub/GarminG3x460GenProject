fragment_buffer = {}

def handle_fragment(fields):
    total = int(fields[1])
    num = int(fields[2])
    seq = fields[3] or "0"

    payload = fields[5]
    fill = fields[6]

    key = seq

    if total == 1:
        return payload, fill

    if key not in fragment_buffer:
        fragment_buffer[key] = {}

    fragment_buffer[key][num] = payload

    if len(fragment_buffer[key]) == total:
        full_payload = "".join(fragment_buffer[key][i] for i in range(1, total+1))
        del fragment_buffer[key]
        return full_payload, fill

    return None, None
