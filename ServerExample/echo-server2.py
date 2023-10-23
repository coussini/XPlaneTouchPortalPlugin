import selectors
import socket

sel = selectors.DefaultSelector()

def accept(sock, mask):
    conn, addr = sock.accept()  # Should be ready
    print('accepted', conn, 'from', addr)
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn, mask):
    data = conn.recv(1024)  # Should be ready
    if data:
        print('echoing', repr(data), 'to', conn)
        conn.send(data)  # Hope it won't block
    else:
        print('closing', conn)
        sel.unregister(conn)
        conn.close()

PORT = 65432
hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)

sock = socket.socket()
sock.bind((HOST, PORT))
sock.listen()
sock.setblocking(False)
sel.register(sock, selectors.EVENT_READ, accept)

while True:
    events = sel.select()
    print(f'events: {events}')
    for key, mask in events:
        callback = key.data
        print(f'key.data: {key.data}')
        callback(key.fileobj, mask)