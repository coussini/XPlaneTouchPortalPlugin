'''

{"command": "action1", "autre":"valeur1"}#{"command": "action2", "autre":"valeur2"}#{"command": "action3", "autre":"valeur3"}#

'''

def read_from_server(sock):
    data_inb = b""
    while True:
        try:
            # Recevoir des données du serveur
            recv_data = sock.recv(4096)  # Taille du buffer ajustable selon les besoins
            if recv_data:
                data_inb += recv_data
                # Traiter chaque message délimité par #
                while "#" in data_inb.decode():
                    pos = data_inb.decode().index("#")
                    msg = data_inb[:pos].decode()
                    data_inb = data_inb[pos+1:]  # Retire le message traité + délimiteur
                    print(f"Message reçu : {msg}")
                    # Convertir le message JSON en objet Python et le traiter
                    try:
                        message_obj = json.loads(msg)
                        # Traiter l'objet message_obj ici
                    except json.JSONDecodeError:
                        print("Erreur lors de la conversion du message JSON")
            else:
                print("Connexion fermée par le serveur")
                break
        except Exception as e:
            print(f"Erreur lors de la réception des données : {e}")
            break
