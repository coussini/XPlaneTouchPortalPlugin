# echo-client.py

import socket

HOST = socket.gethostbyname(socket.gethostname())
HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"Hello, world")
    data = s.recv(1024)

print(f"Received {data!r}")