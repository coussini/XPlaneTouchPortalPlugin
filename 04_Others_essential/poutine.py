import types
import socket
import selectors
from threading import Thread


clients = []

# helper function to remove client from the list by name


def remove_client(name):
    global clients
    clients = list(filter(lambda c: c.name != name, clients))


# thread to accept new connections
class Conductor(Thread):
    def __init__(self, selector):
        super().__init__(daemon=True)
        self.selector = selector
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        next_name = 1

        self.sock.bind(('', 8800))
        self.sock.listen()
        while True:
            con, addr = self.sock.accept()
            # right after we accept new connection, make it not blocking
            con.setblocking(False)
            name = 'u' + str(next_name)
            next_name += 1
            # create buffer of data 'to be sent to this client', smth like mailbox
            client = types.SimpleNamespace(name=name, outb=b'')
            clients.append(client)
            # EVENT_READ – there is smth to read from client
            # EVENT_WRITE – client is ready to recive data
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
            # register this socket to selector for both READ and WRITE events
            self.selector.register(con, events, data=client)
            print(str(addr) + ' connected as ' + name)


# single thread which deals with all clients
# the selector allows the thread to switch between sockets (clients)
class MultiClientServer(Thread):
    def __init__(self, selector):
        super().__init__(daemon=True)
        self.selector = selector

    # LOOK! instead of actually sending the message
    # we put it in buffer/mailbox and it'll be sent later
    def _clear_echo(self, client, data):
        client.outb += '\033[F\033[K'.encode()
        client.outb += 'me> '.encode() + data

    # the same here, we don't send data to clients
    # we just plan to do it
    def _broadcast(self, client, data):
        data = (client.name + '> ').encode() + data
        for c in clients:
            if c.name == client.name:
                continue
            c.outb += data

    # clean up
    def _close(self, sock, client):
        remove_client(client.name)
        # don't forget to unregister this socket
        self.selector.unregister(sock)
        sock.close()
        print(client.name + ' disconnected')

    def _read(self, sock, client):
        data = sock.recv(1024)
        if not data:
            self._close(sock, client)
            return
        self._clear_echo(client, data)
        self._broadcast(client, data)

    def _write(self, sock, client):
        # is there anything in client mailbox?
        if not client.outb:
            return
        # try to send as much as possible
        sent = sock.send(client.outb)
        # if smth doesn't fit to package, postpone for next iteration
        client.outb = client.outb[sent:]

    def run(self):
        while True:
            # get sockets which are ready for smth (READ or WRITE)
            events = self.selector.select(timeout=None)
            for key, mask in events:
                sock = key.fileobj
                client = key.data
                # if there is smth to READ
                if mask & selectors.EVENT_READ:
                    self._read(sock, client)
                # if the client ready to recive some data
                if mask & selectors.EVENT_WRITE:
                    self._write(sock, client)


def main():
    sel = selectors.DefaultSelector()
    MultiClientServer(sel).start()
    conductor = Conductor(sel)
    conductor.start()
    # don't forget to join one of threads
    # otherwise, the program exits immediately
    conductor.join()


if __name__ == "__main__":
    main()