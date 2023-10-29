import socket
import socketio

hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)
PORT = ":54676"
sio = socketio.Client()

@sio.event
def connect():
    print('connection established')

@sio.event
def my_message(data):
    print('message received with ', data)
    sio.emit('my response', {'response': 'my response'})

@sio.event
def disconnect():
    print('disconnected from server')

sio.connect('http://localhost:54676')
sio.wait()