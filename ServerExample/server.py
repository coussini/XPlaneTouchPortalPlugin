import socket

'''
##### EXEMPLE DE SERVEUR BLOQUANT #####

===================================================
Liste des méthodes socket bloquante du côté serveur
===================================================
.accept() 
.send()
.recv()

===================
Socket non bloquant
===================
.setblocking(False)
'''


def server_program():
    host = socket.gethostbyname(socket.gethostname())  # get the host ip adress
    port = 65432  # initiate port include and between 49152 & 65535
    server_socket = socket.socket()  # create a socket object
    server_socket.bind((host, port))
    # Server creating listening socket. Bind host address and port together (takes a tuple as argument)
    server_socket.listen(1)  # configure how many client the server can listen simultaneously
    # ce qui suit fourni l'object socket du client
    client_connection, client_address = server_socket.accept()
    # (<<BLOCKS>> execution and waits for an incoming connection)
    while True:
        data = client_connection.recv(1024).decode()
        # (waiting until a client send a data packet to the server. Won't accept data packet greater than 1024 bytes)
        if not data:
            break  # the client close the server socket
        print(f"les données reçu du client sont: " + str(data))
        client_connection.send(data.encode())  # send data to the client
    client_connection.close()  # close the connection to the client


if __name__ == '__main__':
    server_program()
