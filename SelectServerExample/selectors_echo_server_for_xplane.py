import selectors
import socket

mysel = selectors.DefaultSelector()
keep_running = True
list_connections = []

def read(connection, mask):
    #Callback for read events

    client_address = connection.getpeername()
    print('read({})'.format(client_address))
    data = connection.recv(1024)
    if not data:
        print("No data")
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


try:
    HOST = socket.gethostbyname(socket.gethostname())
    PORT = 65432
    print(f'starting X-Plane server on {HOST},{PORT}')
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(False)
    server.bind((HOST,PORT))
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
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    print('shutting down')
    mysel.close()