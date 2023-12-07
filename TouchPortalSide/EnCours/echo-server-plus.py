#!/usr/bin/python                                                                                                                                                                                                                                                    

import socket
import select

server = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432

server.bind( (HOST, PORT) )
server.listen( 5 )
server.setblocking(False)

print(f"The server listening on {(HOST, PORT)}")

toread = [server]

running = True

print("Start server")
# we will shut down when all clients disconenct                                                                                                                                                                                                                      
while running:
    rready,wready,err = select.select( toread, [], [] )
    for s in rready:
        try:
            if s == server:
                # accepting the socket, which the OS passes off to another                                                                                                                                                                                               
                # socket so we can go back to selecting.  We'll append this                                                                                                                                                                                              
                # new socket to the read list we select on next pass                                                                                                                                                                                                     

                print("Preparing accepting client")
                client, address = server.accept()
                toread.append( client )  # select on this socket next time                                                                                                                                                                                               
            else:
                # Not the server's socket, so we'll read                                                                                                                                                                                                                 
                data = s.recv( 1024 )
                if data:
                    print(f"Data received from the client is: {data}")
                    s.sendall(data)
                else:
                    print("Client disconnected")
                    s.close()

                    # remove socket so we don't watch an invalid 
                    # descriptor, decrement client count                                                                                                                                                                      
                    toread.remove( s )
                    #running = len(toread) - 1
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
            running = False
            server.close()