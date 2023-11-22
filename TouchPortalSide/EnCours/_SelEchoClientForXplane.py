import selectors
import socket
import sys
import json
import time
from random import random


mysel = selectors.DefaultSelector()
keep_running = True
'''
outgoing = [
    b'It will be repeated.',
    b'This is the message.',
]
'''

# type class 'dict'
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
print(type(data_json))
data_json_encode = json.dumps(data_json).encode()
print(type(data_json_encode))
outgoing = []
outgoing.append(data_json_encode)

# Connecting is a blocking operation, so call setblocking()
# after it returns.
HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432
print(f'starting up on {HOST},{PORT}')
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    sock.connect((HOST,PORT))
except socket.error:
        print(f"X-Plane server is not running")
        sys.exit(-1)

sock.setblocking(False)

# Set up the selector to watch for when the socket is ready
# to send data as well as when there is data to read.
mysel.register(
    sock,
    selectors.EVENT_READ | selectors.EVENT_WRITE,
)

while keep_running:
    print('waiting for I/O')
    for key, mask in mysel.select(timeout=1):
        connection = key.fileobj

        if mask & selectors.EVENT_READ:
            print('  ready to read')
            data = connection.recv(1024)
            if data:
                # A readable client socket has data
                print('  received {!r}'.format(data))
                mydata = data.decode()
                mydata_json = json.loads(mydata)
                print(type(mydata_json))
                print(mydata_json)
                value = random()
                time.sleep(1)
                if value > 0.9:
                    print('Closing thread')
                    keep_running = False
                    break
                else:
                    outgoing.append(data_json_encode)
                    mysel.modify(sock, selectors.EVENT_WRITE)

        if mask & selectors.EVENT_WRITE:
            print('  ready to write')
            if not outgoing:
                # We are out of messages, so we no longer need to
                # write anything. Change our registration to let
                # us keep reading responses from the server.
                print('  switching to read-only')
                mysel.modify(sock, selectors.EVENT_READ)
            else:
                # Send the next message.
                next_msg = outgoing.pop()
                print('  sending {!r}'.format(next_msg))
                sock.sendall(next_msg)

print('shutting down')
mysel.unregister(connection)
connection.close()
mysel.close()