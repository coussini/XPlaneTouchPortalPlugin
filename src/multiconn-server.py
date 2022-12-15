import socket
import selectors
import types

sel = selectors.DefaultSelector()

def accept_wrapper(sock):
    conn, addr = sock.accept()  # devrait accepter sans attendre
    conn.setblocking(False) # les appels vers de socket seront non bloquant
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"") # crée un object data avec les attribus addr, inb et outb
    events = selectors.EVENT_READ | selectors.EVENT_WRITE # pour savoir si la connection client est prêt en lecture ou écriture
    sel.register(conn, events, data=data)

def service_connection(key, mask): # lorsque la connection est prête, on la gère ici
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb: # toute les données recu d'une connection client sont envoye au client en echo
            print(f"Echoing {data.outb!r} to {data.addr}")
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:] # enlève le byte "sent" de outb

host = socket.gethostbyname(socket.gethostname())
port = 65432  # initiate port no above 1024
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print(f"Listening on {(host, port)}")
lsock.setblocking(False) # les appels vers de socket seront non bloquant
sel.register(lsock, selectors.EVENT_READ, data=None) # prépare un object d'écoute "bag of multiple sockets"

try:
    while True:
        #Ce qui suit est <<BLOQUANT>> et attend tous les sockets clients. Retourne une liste de tupple, ici 3 sockets [(key, mask), (key, mask), (key, mask)]
        events = sel.select(timeout=None) 
        for key, mask in events: # chaque socket client 
            if key.data is None:
                accept_wrapper(key.fileobj) # accepte la connection client et lui affecte un socket
            else:
                service_connection(key, mask) # ici se sont les connections accepté et on les traites
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()