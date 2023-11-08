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
    readable, _, _ = select.select(sockets_to_read,sockets_to_write,sockets_to_read,0)

    for sock in readable:
        print("")
        print(f">>>>>>>>>>>>> ready_to_read : {readable}")
        print("")
        if sock == server_socket:
            print("===============PARTIE SERVEUR===================")
            print(f"server_socket : {sock}")
            # A new client connection is ready to be accepted
            client_socket = server_socket.accept()
            print(f"Connected to client {client_socket}")
            print("")
            sockets_to_read.append(client_socket)
        else:
            print("")
            print("===============PARTIE CLIENT===================")
            print(f"client socket ? : {sock}")
            print(f"server_socket ? : {server_socket}")
            # An existing client sent data or closed the connection
            data = sock.recv(1024)
            print("")
            print("===============DATA CLIENT===================")
            print(f"client data ? : {data}")
            print("")
            if data:
                print(f"Received data from client {client_socket}: {data}")
                print("")
                sock.sendall(data)
            else:
                print(f"Connection closed by client {client_socket}")
                print("")
                sock.close()
                sockets_to_read.remove(sock)

'''
    for sock in writable:
        print('Non Blocking - sending...')
        data = sock.send(b'hello\r\n')
        print(f'Non Blocking - sent: {data}')
        sockets_to_write.remove(sock)

    for sock in exceptional:
        print(f'Non Blocking - error')
        sockets_to_read.remove(sock)
        sockets_to_write.remove(sock)
        break
'''