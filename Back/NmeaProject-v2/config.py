DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "nmea_db",
    "user": "postgres",
    "password": "s3gr3d0"
}

USE_SOURCE = "TCP"  # "TCP" ou "SERIAL"

TCP_CONFIG = {
    "host": "127.0.0.1",
    "port": 3100
}

SERIAL_CONFIG = {
    "port": "/dev/ttyUSB0",
    "baudrate": 4800,
    "timeout": 1
}
