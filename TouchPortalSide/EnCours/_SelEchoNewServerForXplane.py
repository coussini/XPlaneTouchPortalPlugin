import selectors
import socket
import sys
import json

mysel = selectors.DefaultSelector()
keep_running = True
outgoing = []
list_connections = []

def accept(sock):
    print("accept data")
    new_connection, addr = sock.accept()
    list_connections.append(new_connection) 
    new_connection.setblocking(False)
    return new_connection

# Connecting is a blocking operation, so call setblocking()
# after it returns.
HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432
print(f'starting X-Plane server on {HOST},{PORT}')
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(False)
server.bind((HOST,PORT))
server.listen(5)

# Set up the selector to watch for when the socket is ready
# to send data as well as when there is data to read.
mysel.register(server, selectors.EVENT_READ)

while keep_running:
    print('waiting for I/O')
    for key, mask in mysel.select(timeout=1):
        if key.data is None:
            new_connection = accept(key.fileobj)
        else:
            if mask & selectors.EVENT_READ:
                connection = key.fileobj
                print('  ready to read')
                data = new_connection.recv(1024)
                if not data:
                    print("No data")
                    keep_running = False
                else:
                    # A readable client socket has data
                    print(f"  received {data}")
                    outgoing.append(data)
            if mask & selectors.EVENT_WRITE:
                print('  ready to write')
                if not outgoing:
                    # We are out of messages, so we no longer need to
                    # write anything. Change our registration to let
                    # us keep reading responses from the server.
                    print('  switching to read-only')
                    mysel.modify(server, selectors.EVENT_READ)
                else:
                    # Send the next message.
                    next_msg = outgoing.pop()
                    print('  sending {!r}'.format(next_msg))
                    server.sendall(next_msg)

for connection in list_connections:
    mysel.unregister(connection)
    connection.close()
print('shutting down')
mysel.close()