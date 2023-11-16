import socket
import sys

socket.setdefaulttimeout(3) # important 
print('\n'+'#'*50+'\nStarted Executing client for Xplane TCP Server'+ '\n'+'#'*50 )


HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
result_of_check = clientSocket.connect_ex((HOST,PORT))

# Check if Xplane TCP server is up and running
if result_of_check != 0:
    print(str(HOST)+" is not Listening on Port "+ str(PORT))
    clientSocket.close()
    sys.exit(f"Could not connect Xplane Client")

print("Starting client")
clientSocket.send(bytes(str("Hello TCP Server"), "utf-8"));
receiving = True
while receiving:
    data = clientSocket.recv(1024)
    if data == "":
        pass 
    else:
        receiving = False
print(f"Echoing: {data}")
clientSocket.close()