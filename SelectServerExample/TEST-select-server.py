import socket
import select

HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432

print('Non Blocking - creating socket')
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.setblocking(False)
server_socket.bind((HOST, PORT))
server_socket.listen()

# List of sockets to be monitored by select
sockets_to_read = [server_socket]
sockets_to_write = [server_socket]


while True:
    print('Non Blocking - waiting...')
    readable, wt, er = select.select(sockets_to_read,sockets_to_write,sockets_to_read,0)

    for sock in readable:
        print(f">>>>>>>>>>>>> ready_to_read : {readable}")
        if sock == server_socket:
            print(f"server_socket : {sock}")
            client_socket = server_socket.accept()
            print(f"Connected to client {client_socket}")
            sockets_to_read.append(client_socket)
        else:
            print(f"client socket ? : {sock}")
            print(f"server_socket ? : {server_socket}")
            data = sock.recv(1024)
            if data:
                print(f"Received data from client {client_socket}: {data}")
                sock.sendall(data)
            else:
                print(f"Connection closed by client {client_socket}")
                sock.close()
                sockets_to_read.remove(sock)