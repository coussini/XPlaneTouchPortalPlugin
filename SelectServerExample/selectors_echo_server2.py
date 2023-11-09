import selectors
import socket

# Set up the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("localhost", 10000))
server.listen()

# Set up the selectors "bag of sockets"
selector = selectors.DefaultSelector()
selector.register(server, selectors.EVENT_READ)

boucle = True
while boucle:
    events = selector.select()
    for key, _ in events:
        sock = key.fileobj
        print("About to accept.")
        client, _ = sock.accept()
        print("Accepted.")
        data = client.recv(1024)
        if not data:
            selector.unregister(server)
            client.close()
            boucle = False
        else:
            print(f"data = {data}")
            client.sendall(data)
