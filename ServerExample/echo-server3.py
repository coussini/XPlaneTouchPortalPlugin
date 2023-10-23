import socket
from threading import Thread

PORT = 65432
hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket = socket.setblocking(False)


socket.bind((HOST,PORT))

def acceptConnexion():
    print("running in thread")
    while True:
        socket.listen(10)
        address = socket.accept()
        print("{} connected".format( address ))    

if __name__ == "__main__":
    thread = Thread(target = acceptConnexion)
    thread.start()
    print("you can here do bla bla")
    x = 1
    print("x", x)
    print("Main thread will wait here for thread to exit")
    thread.join()
    print("thread finished...exiting")