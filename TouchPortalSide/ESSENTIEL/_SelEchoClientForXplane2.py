import socket
import tcp_client

class TCPClientNonBlocking(tcp_client.TCPClient):
    ''' Non-Blocking TCP Client '''

    def __init__(self, host, port):
        super().__init__(host, port)

    def interact_with_server(self):
        ''' Try to send a large amount of data to the server '''

        # make the socket non-blocking
        self.conn_sock.setblocking(0)

        try:

            # take a very large amount of data
            # b'0' is 1 byte (approx)
            # x 1024 = 1 KB (approx)
            # x 1024 = 1 MB (approx)
            # x 1024 = 1 GB (approx)
            data = b'0' * 1024 * 1024 * 1024

            # connect to server
            self.printwt(f'Connecting to server [{self.host}] on port [{self.port}] ...')
            self.conn_sock.connect((self.host, self.port))

            # try sending the data to the server
            send_info = self.conn_sock.send(data)

            # see how much data was actually sent
            self.printwt(f'Sent {send_info} bytes to the server')

        except OSError as err:
            print(err)

        finally:
            self.printwt('Closing connection socket...')
            self.conn_sock.close()
            self.printwt('Socket closed')

def main():
    ''' Create a non-blocking TCP Client and try to send a large amount of data'''

    tcp_client = TCPClientNonBlocking('192.168.0.108', 65432)
    tcp_client.create_socket()
    tcp_client.interact_with_server()

if __name__ == '__main__':
    main()
