import socket
import serial

def tcp_reader(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    file = sock.makefile('r')

    while True:
        line = file.readline()
        if not line:
            break
        yield line.strip()

def serial_reader(port, baudrate, timeout):
    ser = serial.Serial(port, baudrate, timeout=timeout)

    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            yield line
