#import xp
import threading
import socket
import select
import json
import sys # only for a slef test

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Set the socket to non-blocking mode
HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432  # The port used by the server

server_socket.setblocking(False)
server_socket.bind((HOST, PORT))

# List of sockets to be monitored by select
sockets_to_monitor = [server_socket]

print("Mediator PLugin Start")

def handle_connection():
    while True:
        # Use select to get the list of sockets ready for reading
        ready_to_read, _, _ = select.select(sockets_to_monitor, [], [])
        for sock in ready_to_read:
            print("")
            print(f">>>>>>>>>>>>> ready_to_read : {ready_to_read}")
            print("")
            if sock == server_socket:
                print("===============PARTIE SERVEUR===================")
                print(f"server_socket : {sock}")
                # A new client connection is ready to be accepted
                client_socket, client_address = server_socket.accept()
                print(f"Connected to client {client_address}")
                sockets_to_monitor.append(client_socket)
            else:
                print("")
                print("===============PARTIE CLIENT===================")
                print(f"client socket ? : {sock}")
                print(f"server_socket ? : {server_socket}")
                # An existing client sent data or closed the connection
                data = sock.recv(1024)
                print(f"received data ? : {data}")
                data_json = json.loads(data.decode())
                #if data == b'{"action":"SHUTDOWN"}':
                if data_json['action'] == "SHUTDOWN":
                    print(f"")
                    print(f"Closing server socket")
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()
                    sys.exit(-1)
                else:
                    print("")
                    print("===============DATA CLIENT===================")
                    print(f"client data dataref : {data_json['dataref']}")
                    print(f"client data type : {data_json['type']}")
                    #print(x.['dataref'])
                    #print(f"client dataref ? : {data_convert['dataref']}")
                    #print(f"client value ? : {data_convert['value']}")
                    if data:
                        print(f"Received data from client {client_address}: {data}")
                        # echo send data to client
                        sock.sendall(data)
                    else:
                        print(f"Connection closed by client {client_address}")
                        sock.close()
                        sockets_to_monitor.remove(sock)

def start():
    server_socket.listen()
    print(f"[LISTENING] Server is listening on {HOST}")
    thread = threading.Thread(target=handle_connection, args=())
    thread.start()
    print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


print("[STARTING] server is starting...")
start()