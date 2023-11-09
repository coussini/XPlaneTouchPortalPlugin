#selClient
import socket
import time

HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432

# several connection and close
print("Starting client")
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);

clientSocket.connect((HOST, PORT));
clientSocket.send(bytes(str("Hello UDP Server"), "utf-8"));
receiving = True
while receiving:
    data = clientSocket.recv(1024)
    if data == "":
        pass 
    else:
        receiving = False
print(f"Echoing: {data}")
clientSocket.close()