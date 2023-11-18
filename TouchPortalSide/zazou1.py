# telnet program example
import socket, select, string, sys

def prompt() :
        sys.stdout.write('<You> ')
        sys.stdout.flush()

#main function
if __name__ == "__main__":
        
        HOST = socket.gethostbyname(socket.gethostname())
        PORT = 65432
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        
        # connect to remote host
        try :
                s.connect((HOST, PORT))
        except :
                print('Unable to connect')
                sys.exit()
        
        print('Connected to remote host. Start sending messages')
        prompt()
        
        while 1:
                socket_list = [sys.stdin, s]
                
                # Get the list sockets which are readable
                read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
                
                for sock in read_sockets:
                        #incoming message from remote server
                        if sock == s:
                                data = sock.recv(1024)
                                if not data :
                                        print(f"\nDisconnected from chat server")
                                        sys.exit()
                                else :
                                        #print data
                                        sys.stdout.write(data)
                                        prompt()
                        
                        #user entered a message
                        else :
                                msg = sys.stdin.readline()
                                s.send(msg)
                                prompt()