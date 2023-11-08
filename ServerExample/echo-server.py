import socket

hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(0)
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server Listening on: {HOST} {PORT}")
    conn, addr = s.accept()
    s.settimeout(0)
    with conn:
        while True:
            data = conn.recv(1024)
            conn.settimeout(0)
            if not data:
                break
            else:
                print('Echoing: ', repr(data))
            conn.sendall(data)
            conn.settimeout(0)
        conn.close()
