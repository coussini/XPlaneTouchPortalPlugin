#selClient
import socket
import time

HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432

i = 0
print("Trying to connect to the server")
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect((HOST,PORT))
# several connection and close
while i < 15:
    clientSocket.send(bytes(str(i), 'utf-8'))
    receiving = True
    while receiving:
        data = clientSocket.recv(1024)
        if data == "":
            pass 
        else:
            receiving = False    
    print(f"Echoing: {data}")
    i += 1
clientSocket.close()