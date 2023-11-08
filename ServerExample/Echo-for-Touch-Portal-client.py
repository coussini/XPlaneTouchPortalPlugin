import socket
import json

PORT = 65432
hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)

#Action1 = python object dictionnary
Action1 = {"action":"WRITE","dataref":"AirbusFBW/OHPLightSwitches[7]","value":1,"type":"int"} # Strobe
Action2 = {"action":"SHUTDOWN"} # Strobe

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("Touch Portal Client For X-Plane Connected")
    
    print("Sending data to server")
    #dic = json.dumps({"dataref":"AirbusFBW/OHPLightSwitches[7]","value":1})
    s.send(json.dumps(Action1).encode('utf-8'))
    data = s.recv(1024)
    s.send(json.dumps(Action2).encode('utf-8'))
    data = s.recv(1024)
    #s.send(b'shutdown')
    #print("Receiving data from server")
    #data = s.recv(1024)
    #print('Echoing: ', repr(data))
    s.close()