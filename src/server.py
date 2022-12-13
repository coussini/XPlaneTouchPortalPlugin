import socket

def server_program():
    # get the hostname
    host = socket.gethostname()
    port = 65432  # initiate port no above 1024

    server_socket = socket.socket()  # get instance
    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many client the server can listen simultaneously
    server_socket.listen(1)
    
    # ici un client vient de se connecte
    print(f"Le serveur est en mode d'attente, rien ne se passe après cette ligne\n\nLe serveur attend...")
    conn, address = server_socket.accept()  # accept new connection
    print("Un client vient de se connecter: " + str(address))
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        print(f"Le serveur attend les données du client...")
        data = conn.recv(1024).decode()
        if not data:
            # if data is not received break
            print(f"Le client vient de se déconnecter !")
            break
        print(f"les données reçu du client sont: " + str(data))
        conn.send(data.encode())  # send data to the client

    conn.close()  # close the connection

if __name__ == '__main__':
    server_program()