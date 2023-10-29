import eventlet
import socketio
import os

# Creating a server instance.
sio = socketio.Server()

#  We will use Eventlet server.
app = socketio.WSGIApp(sio, static_files = {'/static': './public'})

# On client connection.
@sio.event
def connect(sid, environ):
    print('The server receive a client connection')

# chatch message from client
@sio.event
def demande_du_client(sid,data):
    for keys, value in data.items():
        print(f"la cle demande est {keys} et sa valeur {value}")

# Write a disconnect handler which invokes if application initiated disconnects, server initiated disconnects, or accidental disconnects, for example due to networking failures.
@sio.event
def disconnect(sid):
    print('disconnect client from server')

if __name__ == '__main__':
    print("Server Started")
    # to mute any message from eventlet -> log=open(os.devnull,"w")
    eventlet.wsgi.server(eventlet.listen(('', 54676)), app, log=open(os.devnull,"w"))