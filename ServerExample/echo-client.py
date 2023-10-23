import socket

PORT = 65432
hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("Client Connected")
    while True:
        print("Sending data to server")
        s.sendall(b'Hello, world')
        print("Recieving data from server")
        data = s.recv(1024)
        print('Echoing: ', repr(data))
        #s.sendall(b'') ### Le client envloie rien pour signifier la fin des datas
    #    break
    #s.close()