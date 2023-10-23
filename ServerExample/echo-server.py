import socket

hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server Listening on: {HOST} {PORT}")
    conn, addr = s.accept()
    with conn:
        while True:
            data = conn.recv(1024)
            conn.sendall(data)