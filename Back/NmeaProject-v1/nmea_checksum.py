def validate_checksum(sentence):
    try:
        sentence = sentence.strip()
        if "*" not in sentence:
            return False

        data, checksum = sentence.split("*")
        data = data[1:]  # remove $ ou !
        calc = 0
        for c in data:
            calc ^= ord(c)

        return int(checksum[:2], 16) == calc
    except:
        return False
