#!/usr/bin/env python3

import socket
import selectors
import types

sel = selectors.DefaultSelector()
messages = [b"Message 1 from client.", b"Message 2 from client."]

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            print(recv_data)
            print('  switching to read-only')
            sel.modify(sock, selectors.EVENT_READ)
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()

    if mask & selectors.EVENT_WRITE:
        if messages:
            for m in messages:
                print(f"Sending {m} to server")
        print('  switching to read-only')
        sel.modify(sock, selectors.EVENT_READ)


try:
    host = socket.gethostbyname(socket.gethostname())
    port = 65432
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host,port))
    print(f"Connecting on {(host, port)}")
    sock.setblocking(False)
    sel.register(sock, selectors.EVENT_WRITE, data=None)

    while True:
        #print('waiting for I/O')
        for key, mask in sel.select(timeout=0.1):
            service_connection(key, mask)
except socket.error:
        print(f"X-Plane server is not running")
        sys.exit(-1)
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    print('shutting down')
    sel.close()