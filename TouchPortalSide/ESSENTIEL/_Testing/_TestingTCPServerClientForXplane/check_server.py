import socket

socket.setdefaulttimeout(.5)
print('\n'+'#'*50+'\nStarted Executing the script'+ '\n'+'#'*50 )

def port_check(ip,port):

    DEVICE_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result_of_check = DEVICE_SOCKET.connect_ex((ip,port))

    if result_of_check == 0:
       print(str(ip)+" is Listening on Port "+ str(port))
       DEVICE_SOCKET.close()
    else:
       print(str(ip)+" is not Listening on Port "+ str(port))
       DEVICE_SOCKET.close()
       
    print("")

HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432

port_check(HOST,PORT)