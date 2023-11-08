import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(("localhost", 55555))
server.listen()

while True:
    client, address = server.accept()
    print("Connected to", address)
    while True:
        line = input("> ")
        try:
            client.send(line.encode("utf-8"))
        except ConnectionError as e:
            print(e)
            print("Disconnecting")
            client.close()
            break