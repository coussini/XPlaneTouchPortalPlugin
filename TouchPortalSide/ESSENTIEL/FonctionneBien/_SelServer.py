#!/usr/bin/env python3
import selectors
import socket
import json
import threading
import types

class ServerXP:
    def __init__(cls, host, port):
        cls.sel = selectors.DefaultSelector()
        cls.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.host = host
        cls.port = port
        cls.outgoing = []
        cls.keep_running = threading.Event()
        cls.namespace_data = types.SimpleNamespace()

    def setup(cls):
        cls.sock.bind((cls.host, cls.port))
        # queue upto max 6 connection requests
        cls.sock.listen(6)
        print(f"Listening on {(cls.host, cls.port)}")
        cls.sock.setblocking(False)
        cls.sel.register(cls.sock, selectors.EVENT_READ, data=None)

    def run(cls):
        # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in cls.sel.select(timeout=0.1):
            if key.data is None:
                cls.accept_wrapper()
            else:
                cls.service_connection(key, mask)

    def accept_wrapper(cls):
        conn, addr = cls.sock.accept()  # Should be ready to read
        print(f"Accepted connection from {addr}")
        conn.setblocking(False)
        setattr(cls.namespace_data,'addr',addr)
        setattr(cls.namespace_data,'inb',b'')
        setattr(cls.namespace_data,'outb',b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        cls.sel.register(conn, events, data=cls.namespace_data)

    def service_connection(cls, key, mask):
        sock = key.fileobj
        cls.namespace_data = key.data # use the simple name spaces "cls.namespace_data", created in accept wrapper
        if mask & selectors.EVENT_READ:
            if sock:
                recv_data = sock.recv(1024)  # Should be ready to read
                if recv_data:
                    cls.managing_received_data(recv_data)
                else:
                    print(f"Closing connection to {cls.namespace_data.addr}")
                    cls.sel.unregister(sock)
                    sock.close()
        if mask & selectors.EVENT_WRITE:
            if cls.namespace_data.outb:
                print(f"send_data = {cls.namespace_data.outb!r} to {cls.namespace_data.addr}")
                # sent value is the length of the string that was sent
                sent = sock.send(cls.namespace_data.outb)  
                # remove the sent string from the cls.namespace_data.outb
                cls.namespace_data.outb = cls.namespace_data.outb[sent:]    

    def shutting_down(cls):
        cls.sel.close()

    def managing_received_data(cls, recv_data):
        print(f"recv_data = {recv_data} to {cls.namespace_data.addr}")
        cls.namespace_data.outb += recv_data

def main(): 

    host = socket.gethostbyname(socket.gethostname())
    port = 65432
    ser_xp = ServerXP(host,port)
    ser_xp.keep_running.set()
    ser_xp.setup()

    try:
        while ser_xp.keep_running.is_set():
            ser_xp.run()
    except KeyboardInterrupt:
        ser_xp.keep_running.clear()
        print("Caught keyboard interrupt, exiting")
    finally:
        print('shutting down')
        ser_xp.shutting_down()

if __name__ == '__main__':
    main()