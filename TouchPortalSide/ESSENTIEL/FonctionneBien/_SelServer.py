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
        cls.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        cls.host = host
        cls.port = port
        cls.outgoing = []
        cls.keep_running = threading.Event()
        cls.namespace_data = types.SimpleNamespace()

    def preparing_running(cls):
        cls.sock.bind((cls.host, cls.port))
        print(f'Listening on {(cls.host, cls.port)}')
        # upto max 6 connection requests
        cls.sock.listen(6)
        # unblocking socket
        cls.sock.setblocking(False)
        # register a file object for selection, monitoring it for I/O events
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
        print(f'X-Plane client connected: connection {addr}')
        conn.setblocking(False)
        setattr(cls.namespace_data,'addr',addr)
        setattr(cls.namespace_data,'inb',b'')
        setattr(cls.namespace_data,'outb',b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        cls.sel.register(conn, events, data=cls.namespace_data)

    def service_connection(cls, key, mask):
        sock = key.fileobj
        cls.namespace_data = key.data # use the simple name spaces 'cls.namespace_data', created in accept wrapper

        if mask & selectors.EVENT_READ:
            try:
                # Should be ready to read
                recv_data = sock.recv(1024)
            except BlockingIOError:
                pass  # Resource temporarily unavailable (errno EWOULDBLOCK)
            except ConnectionResetError:
                cls.socket_die(sock)
            except:
                raise  # No connection
            else:
                if recv_data:
                    cls.managing_received_data(sock, recv_data)
                else:
                    cls.socket_die(sock)

        if mask & selectors.EVENT_WRITE:
            if cls.namespace_data.outb:
                print(f'send_data = {cls.namespace_data.outb!r} to {sock.getpeername()}')
                # sent value is the length of the string that was sent
                sent = sock.send(cls.namespace_data.outb)  
                # remove the sent string from the cls.namespace_data.outb
                cls.namespace_data.outb = cls.namespace_data.outb[sent:]    

    def socket_die(cls, sock):
        print(f"Closing connection to {sock.getpeername()}")
        cls.sel.unregister(sock)
        sock.close()

    def shutting_down(cls):
        cls.sel.close()

    def managing_received_data(cls, sock, recv_data):
        print(f'recv_data = {recv_data} to {sock.getpeername()}')
        cls.namespace_data.outb += recv_data

def main(): 

    host = socket.gethostbyname(socket.gethostname())
    port = 65432
    server_xp = ServerXP(host,port)
    server_xp.keep_running.set()
    server_xp.preparing_running()

    try:
        while server_xp.keep_running.is_set():
            server_xp.run()
    except KeyboardInterrupt:
        server_xp.keep_running.clear()
        print('Caught keyboard interrupt, exiting')
    finally:
        print('shutting down')
        server_xp.shutting_down()

if __name__ == '__main__':
    main()