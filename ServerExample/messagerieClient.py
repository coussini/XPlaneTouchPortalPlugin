import socket

# Création du socket (serveur client)
serveur_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Définition des infos sur le serveur
Host = socket.gethostbyname(socket.gethostname())
Port = 6390

# On se connecte au serveur
serveur_client.connect((Host, Port))

while True:
    msg = input('>>')
    msg = msg.encode("utf8")
    serveur_client.send(msg)
    requete_serveur = serveur_client.recv(255)
    requete_serveur = requete_serveur.decode('utf8')
    print(requete_serveur)
