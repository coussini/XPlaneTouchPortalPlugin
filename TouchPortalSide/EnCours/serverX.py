import socket
import select
import threading
import errno
import time 

HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432

def handle_client(client, address):
    while True:
        try:
            client.setblocking(0)
            request_bytes = client.recv(1024)
            if not request_bytes:
                print("Connection closed")
                client.close()
                break
            else:
                request_str = request_bytes.decode()
                print(f"Donnee du client: {request_str}")
                client.sendall(request_bytes)
        except socket.error as e:
            if e.args[0] == errno.EWOULDBLOCK: 
                #print('EWOULDBLOCK')
                time.sleep(0.1)           # short delay, no tight loops
            else:
                print("ici")
                print(e)
                break

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST,PORT))
server_socket.listen(2)
#server_socket.setblocking(False)

inputs = [server_socket]
outputs = []

print("Start server")
try:
    while True:
        for sock in inputs:
            if sock.fileno() == -1:
                inputs.remove(sock)
        readable, writable, exceptional = select.select(inputs, outputs, inputs, 1)
        for s in readable:
            if s == server_socket:
                connection, client_address = s.accept()
                print(f"new connection: {client_address}")
                inputs.append(connection)
            else:
                threading.Thread(target=handle_client, args=(connection, client_address)).start()
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
    server_socket.close()
#finally:
#    print('shutting down')
#    server_socket.close()
