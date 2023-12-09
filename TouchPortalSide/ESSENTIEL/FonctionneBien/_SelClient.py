# dans xplane_touch_portal_client.py... injecter les données à envoyer comme  "put_some_random_message"

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
        cls.client_selectors = selectors.DefaultSelector()
        cls.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        cls.host = socket.gethostbyname(socket.gethostname())
        cls.port = 65432
        cls.outgoing_data = []
        cls.keep_running = threading.Event()
        cls.random_msg1 = None # temporary
        cls.random_msg2 = None # temporary

    def connect(cls):
        try:    
            cls.client_socket.connect((cls.host,cls.port))
        except socket.error:
            print(f'X-Plane server is not running')
            return False
        else:
            return True

    def preparing_running(cls):
        print(f'Connecting on {(cls.host, cls.port)}')
        # unblocking socket
        cls.client_socket.setblocking(False)
        # register a file object for selection, monitoring it for I/O events
        cls.client_selectors.register(cls.client_socket, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)

    def run(cls):
        # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in cls.client_selectors.select(timeout=0.1):
            cls.service_connection(key, mask)
            cls.put_some_random_message() # (1) run a class inside a thread... and from outside, feed class.outgoing with action message... (init...write...)

    # create some action to send to server
    def put_some_random_message(cls):
        value = random.randint(1,20)
        print('value = ',value)
        if value == 5:
            print('generate message')
            message = json.dumps(cls.random_msg1).encode()
            cls.outgoing_data.append(message)
        elif value == 7:
            print('generate message')
            message = json.dumps(cls.random_msg2).encode()
            cls.outgoing_data.append(message)
        time.sleep(0.1)

    def shutting_down(cls):
        if cls.client_selectors:
            cls.client_selectors.unregister(cls.client_socket)
            cls.client_selectors.close()
        if cls.client_socket: 
            cls.client_socket.close()

    def service_connection(cls, key, mask):
        server_socket = key.fileobj
    
        if mask & selectors.EVENT_READ:
            try:
                # Should be ready to read
                ingoing_data = server_socket.recv(1024) 
            except BlockingIOError:
                pass  # Resource temporarily unavailable (errno EWOULDBLOCK)
            except:
                # No connection
                #raise Exception('X-Plane server closed suddenly')
                raise
            else:
                if ingoing_data:
                    cls.managing_received_data(ingoing_data)
                else:
                    # No connection
                    #raise Exception('X-Plane server closed suddenly')
                    raise

        if mask & selectors.EVENT_WRITE:
            if cls.outgoing_data:
                next_msg = cls.outgoing_data.pop()
                server_socket.sendall(next_msg)

    def managing_received_data(cls, ingoing_data):
        print(f'ingoing_data = {ingoing_data}')
        pass 

def main(): 
    # a test for a Touch Portal Action
    json_data_init = {
        'command': 'init',
        'datarefs': [
            {
                'dataref': 'AirbusFBW/OHPLightSwitches[7]', # Strobe  -> int
                'value':   '2' # Strobe  -> int
            },
            {
                'dataref': 'AirbusFBW/RMP3Lights[0]', # OVHD INTEG LT Brightness Knob -> float
                'value':   '0.50' # OVHD INTEG LT Brightness Knob -> float
            },
            {
                'dataref': 'AirbusFBW/APUStarter', # APU Start -> int
                'value':   '4' # APU Start -> int
            }
        ]
    }
    json_data_write = {
        'command': 'write',
        'datarefs': [
            {
                'dataref': 'AirbusFBW/OHPLightSwitches[7]', # Strobe  -> int
                'value':   '0'
            },
            {
                'dataref': 'AirbusFBW/RMP3Lights[0]', # OVHD INTEG LT Brightness Knob -> float
                'value':   '0.30'
            },
            {
                'dataref': 'AirbusFBW/APUStarter', # APU Start -> int
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