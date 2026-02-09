
from gdl90

UDP_IP = "127.0.0.1"
UDP_PORT = 4000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

lat, lon = -23.55, -46.63

while True:
    sock.sendto(heartbeat(), (UDP_IP, UDP_PORT))
    sock.sendto(ownship(lat, lon, 3500, 120, 270), (UDP_IP, UDP_PORT))
    sock.sendto(
        traffic(0xABCDEF, lat+0.02, lon+0.01, 3800, 110, 90),
        (UDP_IP, UDP_PORT)
    )

    lat += 0.0001
    time.sleep(1)
