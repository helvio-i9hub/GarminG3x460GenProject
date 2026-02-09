def dm_to_degrees(dm, direction):
    """
    Converte NMEA ddmm.mmmm para graus decimais
    """
    if not dm or not direction:
        return None

    try:
        dm = float(dm)
        degrees = int(dm // 100)
        minutes = dm - (degrees * 100)
        decimal = degrees + minutes / 60

        if direction in ("S", "W"):
            decimal *= -1

        return decimal
    except:
        return None
