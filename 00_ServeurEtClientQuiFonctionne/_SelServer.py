#!/usr/bin/env python3
import selectors
import socket
import json
import threading
import types

class ServerXP:
    def __init__(self, host, port):
        self.server_selectors = selectors.DefaultSelector()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = host
        self.port = port
        self.keep_running = threading.Event()
        self.outgoing_data = types.SimpleNamespace()
        self.client_socket_list = []

    def preparing_running(self):
        self.server_socket.bind((self.host, self.port))
        print(f'Listening on {(self.host, self.port)}')
        # upto max 6 connection requests
        self.server_socket.listen(6)
        # unblocking socket
        self.server_socket.setblocking(False)
        # register a file object for selection, monitoring it for I/O events
        self.server_selectors.register(self.server_socket, selectors.EVENT_READ, data=None)

    def run(self):
        # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in self.server_selectors.select(timeout=0.1):
            if key.data is None:
                self.accept_wrapper()
            else:
                self.service_connection(key, mask)

    def accept_wrapper(self):
        client_socket, client_address = self.server_socket.accept()  # Should be ready to read
        self.client_socket_list.append(client_socket)
        print(f'X-Plane client connected: connection {client_address}')
        #client_socket.setblocking(False)
        setattr(self.outgoing_data,'outb',b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.server_selectors.register(client_socket, events, data=self.outgoing_data)

    def service_connection(self, key, mask):
        client_socket = key.fileobj
        self.outgoing_data = key.data # use the simple name spaces 'self.outgoing_data', created in accept wrapper

        if mask & selectors.EVENT_READ:
            try:
                # Should be ready to read
                ingoing_data = client_socket.recv(1024)
            except BlockingIOError:
                pass  # Resource temporarily unavailable (errno EWOULDBLOCK)
            except ConnectionResetError:
                self.socket_die(client_socket)
            except:
                raise  # No connection
            else:
                if ingoing_data:
                    self.managing_received_data(client_socket, ingoing_data)
                else:
                    self.socket_die(client_socket)

        if mask & selectors.EVENT_WRITE:
            if self.outgoing_data.outb:
                print(f'outgoing_data = {self.outgoing_data.outb!r} to {client_socket.getpeername()}')
                print(f'')
                # sent value is the length of the string that was sent
                sent = client_socket.send(self.outgoing_data.outb)  
                # remove the sent string from the self.outgoing_data.outb
                self.outgoing_data.outb = self.outgoing_data.outb[sent:]    

    def socket_die(self, client_socket):
        print(f'Closing connection to {client_socket.getpeername()}')
        self.server_selectors.unregister(client_socket)
        client_socket.close()
        self.client_socket_list.remove(client_socket)

    def shutting_down(self):
        # in case there are some unclosed client socket
        print('threat unclosed client socket')
        for client_socket in list(self.client_socket_list):
            self.server_selectors.unregister(client_socket)
            client_socket.close()
            self.client_socket_list.remove(client_socket)

        self.server_selectors.close()

    def treat_ingoing_string(self, ingoing_str):

        new = ''
        ingoing_list = []

        for char in ingoing_str:
            if char == '{' and new != '':
                ingoing_list.append(new)
                new = ''
                new = new + char
            elif char == '{':
                new = new + char
            else:
                new = new + char

        ingoing_list.append(new)

        return ingoing_list

    def managing_received_data(self, client_socket, ingoing_data):

        ingoing_list = self.treat_ingoing_string(ingoing_data.decode())

        for one_ingoing in ingoing_list: 
            print(f'ingoing_data = {one_ingoing} to {client_socket.getpeername()}')
            print(f'')
            # echoing data
            self.outgoing_data.outb += one_ingoing.encode()

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