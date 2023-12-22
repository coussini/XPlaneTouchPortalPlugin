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

class ClientXP:
    def __init__(self):
        self.client_selectors = selectors.DefaultSelector()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = 65432
        self.keep_running = threading.Event()
        self.outgoing_data = []
        self.random_msg1 = None # temporary
        self.random_msg2 = None # temporary

    def connect(self):
        try:    
            self.client_socket.connect((self.host,self.port))
        except socket.error:
            print(f'X-Plane server is not running')
            return False
        else:
            return True

    def preparing_running(self):
        print(f'Connecting on {(self.host, self.port)}')
        # unblocking socket
        self.client_socket.setblocking(False)
        # register a file object for selection, monitoring it for I/O events
        self.client_selectors.register(self.client_socket, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)

    def run(self):
        # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in self.client_selectors.select(timeout=0.1):
            self.service_connection(key, mask)
            #self.put_some_random_message() # (1) run a class inside a thread... and from outside, feed class.outgoing with action message... (init...write...)

    # create some action to send to server
    def put_some_random_message(self):
        value = random.randint(1,7)
        print('value = ',value)
        if value == 5:
            print('generate message')
            message = json.dumps(self.random_msg1).encode()
            self.outgoing_data.append(message)
        elif value == 7:
            print('generate message')
            message = json.dumps(self.random_msg2).encode()
            self.outgoing_data.append(message)
        time.sleep(0.1)

    def shutting_down(self):
        if self.client_selectors:
            self.client_selectors.unregister(self.client_socket)
            self.client_selectors.close()
        if self.client_socket: 
            self.client_socket.close()

    def service_connection(self, key, mask):
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
                    self.managing_received_data(ingoing_data)
                else:
                    # No connection
                    #raise Exception('X-Plane server closed suddenly')
                    raise

        if mask & selectors.EVENT_WRITE:
            if self.outgoing_data:
                next_msg = self.outgoing_data.pop()
                server_socket.sendall(next_msg)

    def managing_received_data(self, ingoing_data):
        print(f'PREPARING DATA FOR UPDATING TOUYCH PORTAL ingoing_data = {ingoing_data}')
        print(f'ingoing_data = {ingoing_data}')
        pass 

    def thread_function(self):
        print("start thread")
        if self.connect():
            self.preparing_running()
            try:
                while self.keep_running.is_set():
                    self.run()
            except KeyboardInterrupt:
                self.keep_running.clear()
                print('Caught keyboard interrupt, exiting')
            except:
                self.keep_running.clear()
                print('X-Plane server closed suddenly')
            finally:
                print('shutting down')
                self.shutting_down()

    def treat_xplane_client(self):
        self.keep_running.set()
        xp_thread = threading.Thread(target=self.thread_function, args=())
        xp_thread.start()

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

    ''' Prepare an ClientXP object for the Touch Portal Action purposes '''
    client_xp = ClientXP()
    client_xp.treat_xplane_client()

    while client_xp.keep_running.is_set():
        value = random.randint(1,100)
        print('value = ',value)
        if value == 5:
            print('generate message')
            message = json.dumps(json_data_init).encode()
            client_xp.outgoing_data.append(message)
        elif value == 7:
            print('generate message')
            message = json.dumps(json_data_write).encode()
            client_xp.outgoing_data.append(message)
        elif value == 25:
            print('generate message')
            message = json.dumps(json_data_init).encode()
            client_xp.outgoing_data.append(message)
        elif value == 17:
            print('generate message')
            message = json.dumps(json_data_write).encode()
            client_xp.outgoing_data.append(message)
        elif value == 37:
            client_xp.keep_running.clear()
        time.sleep(0.1)


if __name__ == '__main__':
    main()