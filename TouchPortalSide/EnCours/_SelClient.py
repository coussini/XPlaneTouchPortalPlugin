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


class Communication:
    def __init__(cls):
        cls.sel = selectors.DefaultSelector()
        cls.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
            print(f"X-Plane server is not running")
            return False
        else:
            return True

    def preparing_running(cls):
        print(f"Connecting on {(cls.host, cls.port)}")
        # unblocking socket
        cls.sock.setblocking(False)
        # register a file object for selection, monitoring it for I/O events
        cls.sel.register(
            cls.sock,
            selectors.EVENT_READ | selectors.EVENT_WRITE,
        )

    def run(cls):
        # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in cls.sel.select(timeout=0.1):
            cls.service_connection(key, mask)
            cls.put_some_random_message() # (1) run a class inside a thread... and from outside, feed class.outgoing with action message... (init...write...)

    def put_some_random_message(cls):
        value = random.randint(1,20)
        print("value = ",value)
        if value == 5:
            print("generate message")
            message = json.dumps(cls.random_msg1).encode()
            cls.outgoing.append(message)
        elif value == 7:
            print("generate message")
            message = json.dumps(cls.random_msg2).encode()
            cls.outgoing.append(message)
        time.sleep(1)

    def shutting_down(cls):
        if cls.sel:
            cls.sel.unregister(cls.sock)
            cls.sel.close()
        if cls.sock: 
            cls.sock.close()

    def service_connection(cls, key, mask):
        service_socket = key.fileobj
    
        if mask & selectors.EVENT_READ:
            recv_data = service_socket.recv(1024) 
            if recv_data:
                cls.managing_received_data(recv_data)

        if mask & selectors.EVENT_WRITE:
            if cls.outgoing:
                next_msg = cls.outgoing.pop()
                service_socket.sendall(next_msg)

    def managing_received_data(cls, recv_data):
        print(recv_data)
        pass 

def main(): 
    # a test for a Touch Portal Action
    json_data_init = {
        "command": "init",
        "datarefs": [
            {
                "dataref": "AirbusFBW/OHPLightSwitches[7]", # Strobe  -> int
                "value":   "2" # Strobe  -> int
            },
            {
                "dataref": "AirbusFBW/RMP3Lights[0]", # OVHD INTEG LT Brightness Knob -> float
                "value":   "0.50" # OVHD INTEG LT Brightness Knob -> float
            },
            {
                "dataref": "AirbusFBW/APUStarter", # APU Start -> int
                "value":   "4" # APU Start -> int
            }
        ]
    }
    json_data_write = {
        "command": "write",
        "datarefs": [
            {
                "dataref": "AirbusFBW/OHPLightSwitches[7]", # Strobe  -> int
                "value":   "0"
            },
            {
                "dataref": "AirbusFBW/RMP3Lights[0]", # OVHD INTEG LT Brightness Knob -> float
                "value":   "0.30"
            },
            {
                "dataref": "AirbusFBW/APUStarter", # APU Start -> int
                "value":   "2"
            }
        ]
    }
    # a test for schedulling update process
    # for a dataref update from X-Plane
    json_data_update = {"command": "update"}


    ''' Prepare an communication object for the Touch Portal Action purposes '''
    ''' Prepare an communication object for the Touch Portal Action purposes '''
    ''' Prepare an communication object for the Touch Portal Action purposes '''
    client_action = Communication()
    client_action.keep_running.set()
    client_action.random_msg1 = json_data_init
    client_action.random_msg2 = json_data_write
    
    if client_action.connect():
        client_action.preparing_running()
        try:
            while client_action.keep_running.is_set():
                client_action.run()
        except KeyboardInterrupt:
            client_action.keep_running.clear()
            print("Caught keyboard interrupt, exiting")
        except ConnectionAbortedError:
            client_action.keep_running.clear()
            print("X-Plane server closed suddenly")
        finally:
            print('shutting down')
            client_action.shutting_down()

if __name__ == '__main__':
    main()
