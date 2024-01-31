import select
import socket
import json
import time
import random
import threading

def handle_client(client, address):
    request_bytes = b"" + client.recv(1024)

    if not request_bytes:
        print("Connection closed")
        client.close()
    request_str = request_bytes.decode()
    print(request_str)

def run(sel):
    # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
    for key, mask in sel.select(timeout=0.1):
        if key.data is None:
            accept_wrapper()
        else:
            service_connection(key, mask)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = socket.gethostbyname(socket.gethostname())
port = 65432
server_socket.bind((host, port))
server_socket.listen(6)

inputs = [server_socket]
outputs = []

    except KeyboardInterrupt:
        ser_xp.keep_running.clear()
        print("Caught keyboard interrupt, exiting")

while True:
    readable, writable, exceptional = select.select(inputs, outputs, inputs, 0.1)
    for s in readable:
        if s is server_socket:
            connection, client_address = s.accept()
            connection.setblocking(0)
            inputs.append(connection)
            threading.Thread(target=handle_client, args=(connection, client_address)).start()