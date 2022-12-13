import socket

def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 65432  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server

    message = input(" -> ")  # take input

    while message.lower().strip() != 'bye':
        client_socket.send(message.encode())  # send message
        print(f"Le client attend les données du serveur...")
        data = client_socket.recv(1024).decode()  # receive response

        print('les données reçu du serveur sont: ' + str(data))  # show in terminal

        message = input(" -> ")  # again take input

    print(f'Le client se déconnecte')  # show in terminal
    client_socket.close()  # close the connection

if __name__ == '__main__':
    client_program()