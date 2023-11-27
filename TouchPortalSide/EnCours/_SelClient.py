# from https://cppsecrets.com/users/110711510497115104971101075756514864103109971051084699111109/Python-TCP-Server-Non-Blocking.php?fbclid=IwAR04S84RX1Zo0MkbyGWbvcSxf3PL8PKs9OJpkaY7yd6SGJIm2WLB6wEhDTg
# also from https://pymotw.com/3/selectors/
import selectors
import socket
import sys
import json
import time
import random
import types
import threading

#----------------------
# Create some instances
#----------------------

''' create a selectors object '''
sel = selectors.DefaultSelector()
''' create a socket for a client '''
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
update_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
''' create a structure for client '''
client_data = types.SimpleNamespace()

def service_connection(key, mask):
    # client_connection content local address (adress of the client) and remote address (the server) 
    client_connection = key.fileobj

    # does the server receive a message (the EVENT-WRITE must be the first event) or send a message (the EVENT-READ must be the first event)
    if mask & selectors.EVENT_READ:
        print('*** ready to read')
        recv_data = client_socket.recv(1024)  # Should be ready to read
        if recv_data:
            recv_data_decode = recv_data.decode()
            print('---> received decode:',recv_data_decode)

    if mask & selectors.EVENT_WRITE:
        print('*** ready to write')

        if client_data.outgoing:
            # Send the next message.
            next_msg = client_data.outgoing.pop()
            print('---> sending:',next_msg)
            client_socket.sendall(next_msg)

def read_client_data_from_xplane(key):
    print('inside thread')
    value = random.randint(1,5)
    print("value = ",value)
    if value == 4:
        print("generate message")
        update_socket.sendall(client_data.json_update_encode)
    time.sleep(1)

def main():

    client_data.keep_running = True #OUI
    json_data = {
        "command": "init",
        "datarefs": [
            {
                "dataref": "AirbusFBW/OHPLightSwitches[7]" # Strobe  -> int
            },
            {
                "dataref": "AirbusFBW/RMP3Lights[0]" # OVHD INTEG LT Brightness Knob -> float
            },
            {
                "dataref": "AirbusFBW/APUStarter" # APU Start -> int
            }
        ]
    }
    client_data.json_encode = json.dumps(json_data).encode() # OUI temporairement
    json_data = {
        "command": "update"
    }
    client_data.json_update_encode = json.dumps(json_data).encode() # OUI temporairement
    client_data.outgoing = [] #OUI
    client_data.outgoing.append(client_data.json_encode)
    client_data.pending_messages = [] #OUI

    host = socket.gethostbyname(socket.gethostname())
    port = 65432
            
    try:    
        client_socket.connect((host,port))
        update_socket.connect((host,port))
    except socket.error:
            print(f"X-Plane server is not running")
            sys.exit(-1)

    try:
        print(f"Connecting on {(host, port)}")
        # unblocking socket
        client_socket.setblocking(False)
        # register a file object for selection, monitoring it for I/O events
        sel.register(
            client_socket,
            selectors.EVENT_READ | selectors.EVENT_WRITE,
        )
        first_time = True
        while client_data.keep_running:
            #print('waiting for I/O')
            # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
            for key, mask in sel.select(timeout=0.1):
                service_connection(key, mask)
            read_client_data_from_xplane(key)

    except KeyboardInterrupt:
        client_data.keep_running = False
        print("Caught keyboard interrupt, exiting")
    except ConnectionAbortedError:
        print("X-Plane server closed suddenly")
    finally:
        print('shutting down')
        if sel:
            sel.unregister(client_socket)
            sel.close()
        if client_socket: 
            client_socket.close()

if __name__ == '__main__':
    main()
