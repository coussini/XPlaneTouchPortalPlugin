#!/usr/bin/env python3
# also from https://pymotw.com/3/selectors/
import selectors
import socket
import json
import time
import random
import threading
import sys

class Communication:
    def __init__(cls):
        cls.sel = selectors.DefaultSelector()
        cls.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        cls.host = socket.gethostbyname(socket.gethostname())
        cls.port = 65432
        cls.outgoing = []
        cls.keep_running = threading.Event()
        cls.random_msg1 = None # temporary
        cls.random_msg2 = None # temporary

    def connect(cls):
        try:    
            cls.sock.connect((cls.host,cls.port))
        except socket.error:
            print(f'X-Plane server is not running')
            return False
        else:
            return True

    def preparing_running(cls):
        print(f'Connecting on {(cls.host, cls.port)}')
        # unblocking socket
        cls.sock.setblocking(False)
        # register a file object for selection, monitoring it for I/O events
        cls.sel.register(cls.sock, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)

    def run(cls):
        # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in cls.sel.select(timeout=0.1):
            cls.service_connection(key, mask)
            cls.put_some_random_message() # (1) run a class inside a thread... and from outside, feed class.outgoing with action message... (init...write...)

    # create some action to send to server
    def put_some_random_message(cls):
        value = random.randint(1,20)
        print('value = ',value)
        if value == 5:
            print('generate message')
            message = json.dumps(cls.random_msg1).encode()
            cls.outgoing.append(message)
        elif value == 7:
            print('generate message')
            message = json.dumps(cls.random_msg2).encode()
            cls.outgoing.append(message)
        time.sleep(0.1)

    def shutting_down(cls):
        if cls.sel:
            cls.sel.unregister(cls.sock)
            cls.sel.close()
        if cls.sock: 
            cls.sock.close()

    def service_connection(cls, key, mask):
        service_socket = key.fileobj
    
        if mask & selectors.EVENT_READ:
            try:
                # Should be ready to read
                recv_data = service_socket.recv(1024) 
            except BlockingIOError:
                pass  # Resource temporarily unavailable (errno EWOULDBLOCK)
            except:
                # No connection
                #raise Exception('X-Plane server closed suddenly')
                raise
            else:
                if recv_data:
                    cls.managing_received_data(recv_data)
                else:
                    # No connection
                    #raise Exception('X-Plane server closed suddenly')
                    raise

        if mask & selectors.EVENT_WRITE:
            if cls.outgoing:
                next_msg = cls.outgoing.pop()
                service_socket.sendall(next_msg)

    def managing_received_data(cls, recv_data):
        print(f'recv_data = {recv_data}')
        pass 

def main(): 
    # a test for a Touch Portal Action
    json_data_init = {
        'command': 'init',
        'datarefs': [
            {
                'dataref': 'C1_AirbusFBW/OHPLightSwitches[7]', # Strobe  -> int
                'value':   '2' # Strobe  -> int
            },
            {
                'dataref': 'C1_AirbusFBW/RMP3Lights[0]', # OVHD INTEG LT Brightness Knob -> float
                'value':   '0.50' # OVHD INTEG LT Brightness Knob -> float
            },
            {
                'dataref': 'C1_AirbusFBW/APUStarter', # APU Start -> int
                'value':   '4' # APU Start -> int
            }
        ]
    }
    json_data_write = {
        'command': 'write',
        'datarefs': [
            {
                'dataref': 'C1_AirbusFBW/OHPLightSwitches[7]', # Strobe  -> int
                'value':   '0'
            },
            {
                'dataref': 'C1_AirbusFBW/RMP3Lights[0]', # OVHD INTEG LT Brightness Knob -> float
                'value':   '0.30'
            },
            {
                'dataref': 'C1_AirbusFBW/APUStarter', # APU Start -> int
                'value':   '2'
            }
        ]
    }
    # a test for schedulling update process
    # for a dataref update from X-Plane
    json_data_update = {'command': 'update'}

    ''' Prepare an communication object for the Touch Portal Action purposes '''
    client_xp = Communication()
    client_xp.keep_running.set()
    client_xp.random_msg1 = json_data_init
    client_xp.random_msg2 = json_data_write
    
    if client_xp.connect():
        client_xp.preparing_running()
        try:
            while client_xp.keep_running.is_set():
                client_xp.run()
        except KeyboardInterrupt:
            client_xp.keep_running.clear()
            print('Caught keyboard interrupt, exiting')
        except:
            client_xp.keep_running.clear()
            print('X-Plane server closed suddenly')
        finally:
            print('shutting down')
            client_xp.shutting_down()

if __name__ == '__main__':
    main()