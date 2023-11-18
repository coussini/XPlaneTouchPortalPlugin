#selClient
import socket
import time
import threading

def run(stop):
    HOST = socket.gethostbyname(socket.gethostname())
    PORT = 65432
    print("Trying to connect to the server")
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        clientSocket.connect((HOST,PORT))
    except Exception as e:        
        print("Server is not running")
        clientSocket.close()
    else:
        while True:
            if stop():
                break
            try:
                clientSocket.send(bytes('Salut le serveur', 'utf-8'))
            except Exception as e:        
                print("Cannot send data, Server is not running")
                stop_threads = True
                break
            else:
                receiving = True
                while receiving:
                    try:
                        data = clientSocket.recv(1024)
                    except Exception as e:        
                        print("Server is not running")
                        stop_threads = True
                        break
                    else:
                        if data == "":
                            pass 
                        else:
                            receiving = False
                    print(f"Echoing: {data}")
        clientSocket.close()

def main():
        stop_threads = False
        t1 = threading.Thread(target = run, args =(lambda : stop_threads, ))
        t1.start()
        t1.join()
        print('thread killed')
main()
