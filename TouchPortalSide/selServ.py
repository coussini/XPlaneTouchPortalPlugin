import socket
import select
import threading

def handle_client(client, address):
    request_bytes = client.recv(1024)
    if not request_bytes:
        print("Connection closed")
        client.close()
    request_str = request_bytes.decode()
    print(f"Donnee du client: {request_str}")
    client.sendall(request_bytes)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = socket.gethostbyname(socket.gethostname())  # as both code is running on same pc
port = 65432
server_address = (host,port)
server_socket.bind(server_address)
server_socket.listen(2)

inputs = [server_socket]
outputs = []

print("Start server")
while True:
    readable, writable, exceptional = select.select(
    inputs, outputs, inputs, 1)
    for s in readable:
        if s is server_socket:
            connection, client_address = s.accept()
            connection.setblocking(0)
            inputs.append(connection)
            threading.Thread(target=handle_client, args=(connection, client_address)).start()