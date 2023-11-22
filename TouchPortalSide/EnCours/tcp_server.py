import socket
from datetime import datetime

class TCPServer:
    ''' A simple TCP Server for handling a single client '''

    def __init__(self, host, port):
        self.host = host            # Host address
        self.port = port            # Host port
        self.sock = None            # Connection socket

    def printwt(self, msg):
        ''' Print message with current date and time '''

        current_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{current_date_time}] {msg}')

    def configure_server(self):
        ''' Configure the server '''

        # create TCP socket with IPv4 addressing
        self.printwt('Creating socket...')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.printwt('Socket created')

        # bind server to the address
        self.printwt(f'Binding server to {self.host}:{self.port}...')
        self.sock.bind((self.host, self.port))
        self.printwt(f'Server binded to {self.host}:{self.port}')

    def wait_for_client(self):
        ''' Wait for a client to connect '''

        # start listening for incoming connections
        self.printwt('Listening for incoming connection...')
        self.sock.listen(1)

        # accept a connection
        client_sock, client_address = self.sock.accept()
        self.printwt(f'Accepted connection from {client_address}')
        self.handle_client(client_sock, client_address)

    def get_phone_no(self, name):
        ''' Get phone no for a given name '''

        phonebook = {'Alex': '1234567890', 'Bob': '1234512345'}

        if name in phonebook.keys():
            return f"{name}'s phone number is {phonebook[name]}"
        else:
            return f"No records found for {name}"

    def handle_client(self, client_sock, client_address):
        """ Handle the accepted client's requests """

        try:
            data_enc = client_sock.recv(1024)
            while data_enc:
                # client's request
                name = data_enc.decode()
                resp = self.get_phone_no(name)
                self.printwt(f'[ REQUEST from {client_address} ]')
                print('\n', name, '\n')

                # send response
                self.printwt(f'[ RESPONSE to {client_address} ]')
                client_sock.sendall(resp.encode('utf-8'))
                print('\n', resp, '\n')

                # get more data and check if client closed the connection
                data_enc = client_sock.recv(1024)
            self.printwt(f'Connection closed by {client_address}')

        except OSError as err:
            self.printwt(err)

        finally:
            self.printwt(f'Closing client socket for {client_address}...')
            client_sock.close()
            self.printwt(f'Client socket closed for {client_address}')

    def shutdown_server(self):
        ''' Shutdown the server '''

        self.printwt('Shutting down server...')
        self.sock.close()
