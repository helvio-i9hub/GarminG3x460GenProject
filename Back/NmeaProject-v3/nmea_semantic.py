from nmea_utils import dm_to_degrees

def parse_gga(fields):
    """
    GGA - Global Positioning System Fix Data
    """
    return {
        "gps_time": fields.get("field_1"),
        "latitude": dm_to_degrees(fields.get("field_2"), fields.get("field_3")),
        "longitude": dm_to_degrees(fields.get("field_4"), fields.get("field_5")),
        "fix_quality": int(fields.get("field_6") or 0),
        "satellites": int(fields.get("field_7") or 0),
        "hdop": float(fields.get("field_8")) if fields.get("field_8") else None,
        "altitude": float(fields.get("field_9")) if fields.get("field_9") else None,
    }
