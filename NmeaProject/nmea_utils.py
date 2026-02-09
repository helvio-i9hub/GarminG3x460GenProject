def dm_to_decimal(dm: str, direction: str) -> float | None:
    """
    Converte coordenada NMEA graus+minutos para decimal

    Ex:
      4807.038, N  ->  48.1173
      01131.000, E ->  11.5166667
    """
    if not dm or not direction:
        return None

    try:
        dm = float(dm)

        degrees = int(dm // 100)
        minutes = dm - (degrees * 100)

        decimal = degrees + minutes / 60.0

        if direction in ("S", "W"):
            decimal *= -1

        return round(decimal, 6)

    except ValueError:
        return None
