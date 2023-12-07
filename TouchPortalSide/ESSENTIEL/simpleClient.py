import socket
import time

data = "Hello Server!";
i = 0
while i < 15:
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
    host = socket.gethostbyname(socket.gethostname())
    port = 65432
    clientSocket.connect((host, port));
    data_o = data + str(i)
    clientSocket.send(data_o.encode());
    time.sleep(0.15)
    i += 1
    clientSocket.close()
