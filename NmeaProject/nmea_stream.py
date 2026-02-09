import re

# Regex oficial NMEA 0183
NMEA_REGEX = re.compile(
    r'[\$!][A-Z0-9]{5,6}[^$!]*\*[0-9A-Fa-f]{2}'
)

def extract_nmea_sentences(data):
    """
    Recebe string arbitrária e retorna lista de sentenças NMEA válidas
    """
    if not data:
        return []

    return NMEA_REGEX.findall(data)
