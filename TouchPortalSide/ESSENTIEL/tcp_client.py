import socket
from datetime import datetime

class TCPClient:
    ''' A simple TCP Client that uses IPv4 '''

    def __init__(self, host, port):
        self.host = host        # host address
        self.port = port        # host port
        self.conn_sock = None   # connection socket

    def printwt(self, msg):
        ''' Print message with current date and time '''

        current_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{current_date_time}] {msg}')

    def create_socket(self):
        ''' Create a socket that uses IPv4 and TCP '''

        self.printwt('Creating connection socket ...')
        self.conn_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.printwt('Socket created')

    def interact_with_server(self):
        ''' Connect and interact with a TCP Server. '''

        try:
            # connect to server
            self.printwt(f'Connecting to server [{self.host}] on port [{self.port}] ...')
            self.conn_sock.connect((self.host, self.port))

            # send data
            self.printwt('Sending name to server to get phone number ...')
            name = 'Alex'
            self.conn_sock.sendall(name.encode('utf-8'))
            self.printwt('[ SENT ]')
            print('\n', name, '\n')

            # receive data
            resp = self.conn_sock.recv(1024)
            self.printwt('[ RECEIVED ]')
            print('\n', resp.decode(), '\n')

            self.printwt('Interaction completed successfully...')

        except OSError as err:
            self.printwt('Cannot connect to server')
            print(err)

        finally:
            # close socket
            self.printwt('Closing connection socket...')
            self.conn_sock.close()
            self.printwt('Socket closed')

def main():
    ''' Create a TCP Client and interact with the server at 127.0.0.1:4444'''

    tcp_client = TCPClient('192.168.0.108', 65432)
    tcp_client.create_socket()
    tcp_client.interact_with_server()

if __name__ == '__main__':
    main()
