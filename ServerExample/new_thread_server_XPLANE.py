#!/usr/bin/python

import json, socket, select, struct

# -------------------------------------------------------------------------
# ---                              FUNCTION                             ---
# -------------------------------------------------------------------------
def send_data(conn, data):
    size = len(data)
    size_in_4_bytes = struct.pack('I', size)
    conn.send(size_in_4_bytes)
    conn.send(data)

def recv_data(conn):
    size_in_4_bytes = conn.recv(4)
    size = struct.unpack('I', size_in_4_bytes)
    size = size[0]
    data = conn.recv(size)
    return data

# -------------------------------------------------------------------------
# ---                               MAIN                                ---
# -------------------------------------------------------------------------
host = socket.gethostbyname(socket.gethostname())
port = 65432
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind((host, port))
print("Server socket bound with ip address {} on port {}".format(host, port))
print("CTRL-C several time to stop")
print("")
socket.listen(1)
inputs = [socket]

while True:
        infds, outfds, errfds = select.select(inputs, inputs, [], 5)
        if len(infds):
                #print 'enter infds'    
                for fds in infds:
                        if fds is socket:
                                clientsock, clientaddr = fds.accept()
                                inputs.append(clientsock)
                                print(f'Client connected: {clientaddr}')
                        else:
                                #print 'enter data recv'  
                                data = recv_data(fds)
                                if not data:
                                        inputs.remove(fds)
                                else:
                                        text = data.decode()
                                        stock = json.loads(text)
                                        print('Receive data from client')
                                        print('ActionID   :', stock.get('dataref'))
                                        print('Value      :', stock.get('newValue'))
                                        '''
                                        print('Sending Echo data to client')
                                        print('Stock:', stock)
                                        text = json.dumps(stock)
                                        print('Dumps:', text)
                                        data = text.encode()
                                        print('Data:', data)
                                        send_data(infds, data)
                                        '''
                
        if len(outfds):
                #print 'enter outfds'   
                for fds in outfds:
                        fds.send(b"python select server from Debian.\n") 