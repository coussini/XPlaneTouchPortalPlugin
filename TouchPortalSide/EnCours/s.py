import select
import socket
import sys
import queue

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)
HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432

print (f"starting up on {HOST} port {PORT}")
server.bind((HOST, PORT))
server.listen(5)

inputs = [ server ]
outputs = [ ]
message_queues = {}

try:
    while inputs:
        print ("\nwaiting for the next event")
        readable, writable, exceptional = select.select(inputs, outputs, inputs)
        for s in readable:
            if s is server:
                # C'est un nouveau client a accepter
                connection, client_address = s.accept()
                print ("new connection from", client_address)
                connection.setblocking(0)
                inputs.append(connection)

                # Give the connection a queue for data we want to send
                message_queues[connection] = queue.Queue()
            else:
                data = s.recv(1024)
                if data:
                    # A readable client socket has data
                    print ('received "%s" from %s' % (data, s.getpeername()))
                    # Add output channel for response
                    #message_queues[s].put(data)
                    #if s not in outputs:
                    #    outputs.append(s)
                    for aQueue in message_queues:
                        message_queues[aQueue].put(data)
                        if aQueue not in outputs:       # enqueue the msg
                            outputs.append(aQueue)      # and ask select to warn when it can be sent                    
                        # AQueue.send ("Test".encode())
                else:
                    # Interpret empty result as closed connection
                    print ("closing", client_address, "after reading no data")
                    # Stop listening for input on the connection
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()
                    # Remove message queue
                    del message_queues[s]
        for s in writable:
            try:
                next_msg = message_queues[s].get_nowait()
                print(f"objet s {s}")
            # this handles a condition where client socket is in the writable list
            # even though it's been removed from the dictionary.
            except KeyError as err:
                pass
            except queue.Empty:
                # No messages waiting so stop checking for writability.
                print ("output queue for", s.getpeername(), "is empty")
                outputs.remove(s)
            else:
                print ('sending "%s" to %s' % (next_msg, s.getpeername()))
                s.send(next_msg)            
        for s in exceptional:
            print ("handling exceptional condition for", s.getpeername())
            # Stop listening for input on the connection
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()

            # Remove message queue
            del message_queues[s]
# shutdown the server when user presses Ctrl-C
except KeyboardInterrupt:
    # Stop listening for input on the connection
    inputs.remove(s)
    if s in outputs:
        outputs.remove(s)
    s.close()

                