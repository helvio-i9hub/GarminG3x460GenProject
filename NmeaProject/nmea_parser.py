from nmea_semantic import parse_gga, parse_rmc, parse_vtg, parse_gsa


def parse_nmea(sentence: str) -> dict | None:
    body = sentence.strip()[1:].split("*")[0]
    parts = body.split(",")

    talker = parts[0][:2]
    sentence_type = parts[0][2:]
    fields = parts[1:]

    semantic = {}

    if sentence_type == "GGA":
        semantic = parse_gga(fields)
    elif sentence_type == "RMC":
        semantic = parse_rmc(fields)
    elif sentence_type == "VTG":
        semantic = parse_vtg(fields)
    elif sentence_type == "GSA":
        semantic = parse_gsa(fields)

    return {
        "talker": talker,
        "sentence_type": sentence_type,
        "fields": fields,
        "semantic": semantic,
    }
