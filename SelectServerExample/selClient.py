#selClient
import socket
import time

i = 0
print("Trying to connect to the server")
# several connection and close
while i < 15:
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        clientSocket.connect(('localhost', 10000))
    except Exception as e:        
        print("Server is not running")
        clientSocket.close()
        break
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