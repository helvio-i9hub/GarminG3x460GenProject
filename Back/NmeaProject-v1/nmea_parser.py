def parse_nmea(sentence):
    sentence = sentence.strip()

    if "*" in sentence:
        sentence = sentence.split("*")[0]

    parts = sentence.split(",")

    header = parts[0][1:]
    talker = header[:2]
    sentence_type = header[2:]

    fields = {}
    for i, v in enumerate(parts[1:], start=1):
        fields[f"field_{i}"] = v

    return {
        "talker": talker,
        "sentence_type": sentence_type,
        "fields": fields
    }
