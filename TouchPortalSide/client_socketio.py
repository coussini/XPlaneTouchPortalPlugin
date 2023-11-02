import sys
import socketio

# Create a client instance.
sio = socketio.Client()

# Connect to server.
@sio.event
def connect():
    print('connection established')

# For receiving data from server.
@sio.event
def message(data):
    print(data)

# Disconnecting.
@sio.event
def disconnect():
    print('client disconnected')

# MAIN
print('client start')
sio.connect('http://localhost:54676')

print('send message')
sio.emit(event = 'demande_du_client', data = {'AirbusFBW/EnableExternalPower': '1'})

sio.disconnect()
