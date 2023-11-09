import selectors
import socket

mysel = selectors.DefaultSelector()
keep_running = True
list_connections = []

def read(connection, mask):
    #Callback for read events
    global keep_running

    client_address = connection.getpeername()
    print('read({})'.format(client_address))
    data = connection.recv(1024)
    if not data:
        print("No data")
        keep_running = False
    else:
        print('  received {!r}'.format(data))
        connection.sendall(data)

def accept(sock, mask):
    #Callback for new connections
    new_connection, addr = sock.accept()
    list_connections.append(new_connection) 
    print('accept({})'.format(addr))
    new_connection.setblocking(False)
    mysel.register(new_connection, selectors.EVENT_READ, read)


server_address = ('localhost', 65432)
print('starting up on {} port {}'.format(*server_address))
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(False)
server.bind(server_address)
server.listen(5)

mysel.register(server, selectors.EVENT_READ, accept)

while keep_running:
    print('waiting for I/O')
    for key, mask in mysel.select(timeout=1):
        callback = key.data
        callback(key.fileobj, mask)

for connection in list_connections:
    mysel.unregister(connection)
    connection.close()

print('shutting down')
mysel.close()