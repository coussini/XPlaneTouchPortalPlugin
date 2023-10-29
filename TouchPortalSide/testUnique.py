import socket

HOST = "127.0.0.1"
PORT = 12136
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
client.send(b"{'type':'stateUpdate','id':'XPlanePlugin.Battery2','value':'0'}")
