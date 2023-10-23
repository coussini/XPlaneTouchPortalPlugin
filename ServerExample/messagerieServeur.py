import socket

Host = socket.gethostbyname(socket.gethostname())
Port = 6390

# Création du socket (serveur)
serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# On bind le socket (on le met en mode écoute sur l'host et le port)
serveur.bind((Host, Port))

# On choisit le nombre max de connexion
serveur.listen(1)

# Le script s'arrete ici jusqu'a une connection
client, adresse = serveur.accept()  # Accept les connections extérieures (et ouvre une connection avec le client)
print("Client avec l'adresse : ", adresse, "C'est connecté")

while True:
    # On recoit les requetes (reste bloqué jusqu'a reception)
    requete_client = client.recv(255)  # 200 caractere max
    requete_client = requete_client.decode('utf8')
    print(requete_client)
    if not requete_client:  # Si on pert la connection
        print('CLOSE')
        break
    # Envoyer un message
    msg = input('>>')
    msg = msg.encode("utf8")
    client.send(msg)

client.close()  # Ferme la connection avec le client
serveur.close()  # Ferme le socket/serveur