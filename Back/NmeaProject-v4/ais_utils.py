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

"""
AIS utility functions
"""

def twos_complement(value: int, bit_width: int) -> int:
    """
    Converts an unsigned integer into signed integer
    using two's complement.

    Example:
      twos_complement(0b11111111, 8) -> -1
    """

    if value & (1 << (bit_width - 1)):
        value -= 1 << bit_width

    return value
