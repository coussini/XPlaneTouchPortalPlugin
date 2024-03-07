def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Devrait être prêt à lire
        if recv_data:
            data.inb += recv_data
            while "#" in data.inb:
                pos = data.inb.index("#")
                msg = data.inb[:pos]
                data.inb = data.inb[pos+1:]  # Retire le message traité + délimiteur
                
                # Traiter le message JSON (msg)
                print(f"Message reçu : {msg}")
                # Ici, ajoutez votre logique pour traiter le message JSON
                
        else:
            print(f"Fermeture de la connexion à {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Envoi {data.outb} à {data.addr}")
            sent = sock.send(data.outb)  # Devrait être prêt à écrire
            data.outb = data.outb[sent:]
