import socket
import json

'''
==================================================
Liste des méthodes socket bloquante du côté client
==================================================
.connect() 
.send()
.recv()
'''

def envoi_au_serveur(client_socket,message):
    client_socket.send(message.encode())  # send message
    print(f"Le client attend les données du serveur...")
    data = client_socket.recv(1024).decode()  # receive response
    print('les données reçu du serveur sont: ' + str(data))  # show in terminal
    return data

def client_program():
    host = socket.gethostbyname(socket.gethostname())  # as both code is running on same pc
    port = 65432  # socket server port number
    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    message1 = json.dumps({"dataref": "AirbusFBW/OHPLightSwitches[7]", "action": "write", "value": "1"}) # a real dict.
    data = envoi_au_serveur(client_socket,message1)
    print(str(data))
    message2 = json.dumps({"dataref": "AirbusFBW/APUMaster", "action": "read"}) # a real dict.
    data = envoi_au_serveur(client_socket,message2)
    print(str(data))
    print(f'Le client se déconnecte')  # show in terminal
    client_socket.close()  # Client sending close message. Close the connection

if __name__ == '__main__':
    client_program()