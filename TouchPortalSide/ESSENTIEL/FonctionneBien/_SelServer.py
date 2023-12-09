#!/usr/bin/env python3
import selectors
import socket
import json
import threading
import types

class ServerXP:
    def __init__(cls, host, port):
        cls.server_selectors = selectors.DefaultSelector()
        cls.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        cls.host = host
        cls.port = port
        cls.keep_running = threading.Event()
        cls.outgoing_data = types.SimpleNamespace()
        cls.client_socket_list = []

    def preparing_running(cls):
        cls.server_socket.bind((cls.host, cls.port))
        print(f'Listening on {(cls.host, cls.port)}')
        # upto max 6 connection requests
        cls.server_socket.listen(6)
        # unblocking socket
        cls.server_socket.setblocking(False)
        # register a file object for selection, monitoring it for I/O events
        cls.server_selectors.register(cls.server_socket, selectors.EVENT_READ, data=None)

    def run(cls):
        # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in cls.server_selectors.select(timeout=0.1):
            if key.data is None:
                cls.accept_wrapper()
            else:
                cls.service_connection(key, mask)

    def accept_wrapper(cls):
        client_socket, client_address = cls.server_socket.accept()  # Should be ready to read
        cls.client_socket_list.append(client_socket)
        print(f'X-Plane client connected: connection {client_address}')
        #client_socket.setblocking(False)
        setattr(cls.outgoing_data,'outb',b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        cls.server_selectors.register(client_socket, events, data=cls.outgoing_data)

    def service_connection(cls, key, mask):
        client_socket = key.fileobj
        cls.outgoing_data = key.data # use the simple name spaces 'cls.outgoing_data', created in accept wrapper

        if mask & selectors.EVENT_READ:
            try:
                # Should be ready to read
                ingoing_data = client_socket.recv(1024)
            except BlockingIOError:
                pass  # Resource temporarily unavailable (errno EWOULDBLOCK)
            except ConnectionResetError:
                cls.socket_die(client_socket)
            except:
                raise  # No connection
            else:
                if ingoing_data:
                    cls.managing_received_data(client_socket, ingoing_data)
                else:
                    cls.socket_die(client_socket)

        if mask & selectors.EVENT_WRITE:
            if cls.outgoing_data.outb:
                print(f'send_data = {cls.outgoing_data.outb!r} to {client_socket.getpeername()}')
                # sent value is the length of the string that was sent
                sent = client_socket.send(cls.outgoing_data.outb)  
                # remove the sent string from the cls.outgoing_data.outb
                cls.outgoing_data.outb = cls.outgoing_data.outb[sent:]    

    def socket_die(cls, client_socket):
        print(f'Closing connection to {client_socket.getpeername()}')
        cls.server_selectors.unregister(client_socket)
        client_socket.close()
        cls.client_socket_list.remove(client_socket)

    def shutting_down(cls):
        # in case there are some unclosed client socket
        print('threat unclosed client socket')
        for client_socket in list(cls.client_socket_list):
            cls.server_selectors.unregister(client_socket)
            client_socket.close()
            cls.client_socket_list.remove(client_socket)

        cls.server_selectors.close()

    def managing_received_data(cls, client_socket, ingoing_data):
        print(f'ingoing_data = {ingoing_data} to {client_socket.getpeername()}')
        # echoing data
        cls.outgoing_data.outb += ingoing_data

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