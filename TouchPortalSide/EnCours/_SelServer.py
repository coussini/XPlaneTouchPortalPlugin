#!/usr/bin/env python3
import socket
import selectors
import types

selectors_server = selectors.DefaultSelector()

def accept_wrapper(sock):
    try:
        conn, addr = sock.accept()  # Should be ready to read
        print(f"Accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        selectors_server.register(conn, events, data=data)
    except KeyboardInterrupt:
        print("[0] Caught keyboard interrupt, exiting")


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data # use the simple name spaces "data", created in accept wrapper
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data
        else:
            print(f"Closing connection to {data.addr}")
            selectors_server.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Echoing {data.outb!r} to {data.addr}")
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]

try:
    host = socket.gethostbyname(socket.gethostname())
    port = 65432
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    # queue upto max 6 connection requests
    server_socket.listen(6)
    print(f"Listening on {(host, port)}")
    server_socket.setblocking(False)
    selectors_server.register(server_socket, selectors.EVENT_READ, data=None)

    while True:
        #print('waiting for I/O')
        for key, mask in selectors_server.select(timeout=0.1):
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print("[2] Caught keyboard interrupt, exiting")
finally:
    print('shutting down')
    selectors_server.close()