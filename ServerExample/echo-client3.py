import socket

PORT = 65432
hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("Client Connected")
    s.close()