# from https://cppsecrets.com/users/110711510497115104971101075756514864103109971051084699111109/Python-TCP-Server-Non-Blocking.php?fbclid=IwAR04S84RX1Zo0MkbyGWbvcSxf3PL8PKs9OJpkaY7yd6SGJIm2WLB6wEhDTg
# also from https://pymotw.com/3/selectors/
import selectors
import socket
import sys
import json
import time
from random import random

''' Create a TCP Server and respond to client's requests '''
host = socket.gethostbyname(socket.gethostname())
port = 65432
# create a TCP / IPv4 socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# flag for the main loop
keep_running = True
# create a selectors object
sel = selectors.DefaultSelector()
# type class 'dict' for x-plane structure
data_json = {
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
data_json_encode = json.dumps(data_json).encode()
outgoing = []
outgoing.append(data_json_encode)
client_connection = None

def service_connection(key, mask):
    global keep_running, data_json_encode, outgoing
    # client_connection content local address (adress of the client) and remote address (the server) 
    client_connection = key.fileobj

    # does the server receive a message (the EVENT-WRITE must be the first event) or send a message (the EVENT-READ must be the first event)
    if mask & selectors.EVENT_READ:
        #print('  ready to read')
        recv_data = client_socket.recv(1024)  # Should be ready to read
        if recv_data:
            # a readable client socket has data
            print('  received {!r}'.format(recv_data))
            recv_data_json = json.loads(recv_data.decode())
            print(recv_data_json)
            simulate_closing_thread_value = random()
            # the next wait 1 second to allow seeing display for simulation
            time.sleep(1) 
            if simulate_closing_thread_value > 0.9:
                print('Closing thread')
                keep_running = False
            else:
                outgoing.append(data_json_encode)
                sel.modify(client_socket, selectors.EVENT_WRITE)

    if mask & selectors.EVENT_WRITE:
        #print('  ready to write')
        if not outgoing:
            # We are out of messages, so we no longer need to
            # write anything. Change our registration to let
            # us keep reading responses from the server.
            print('  switching to read-only')
            sel.modify(client_socket, selectors.EVENT_READ)
        else:
            # Send the next message.
            next_msg = outgoing.pop()
            print('  sending {!r}'.format(next_msg))
            client_socket.sendall(next_msg)

def main():
        
    try:    
        client_socket.connect((host,port))
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
        while keep_running:
            #print('waiting for I/O')
            # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
            for key, mask in sel.select(timeout=0.1):
                service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    except ConnectionAbortedError:
        print("X-Plane server closed suddenly")
    finally:
        print('shutting down')
        sel.unregister(client_socket)
        sel.close()
        if client_socket : client_socket.close();

if __name__ == '__main__':
    main()
