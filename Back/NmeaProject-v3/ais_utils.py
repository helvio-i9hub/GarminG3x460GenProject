def get_int(bits, start, length, signed=False):
    val = int(bits[start:start+length], 2)
    if signed and bits[start] == "1":
        val -= 1 << length
    return val

def get_str(bits, start, length):
    chars = []
    for i in range(0, length, 6):
        c = int(bits[start+i:start+i+6], 2)
        chars.append(chr(c + 64) if c > 0 else "@")
    return "".join(chars).strip("@ ")
