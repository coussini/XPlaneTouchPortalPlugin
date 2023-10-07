'''
Connected to the server
send: Hello
recv: Bye!
send: {'open': 12, 'close': 15}
recv: {'diff': 3}
'''
import socket
import struct
import json

# --- functions ---

def send_data(conn, data):
    size = len(data)
    size_in_4_bytes = struct.pack('I', size)
    conn.send(size_in_4_bytes)
    conn.send(data)

def recv_data(conn):
    size_in_4_bytes = conn.recv(4)
    size = struct.unpack('I', size_in_4_bytes)
    size = size[0]
    data = conn.recv(size)
    return data

# -------------------------------------------------------------------------
# ---                               MAIN                                ---
# -------------------------------------------------------------------------
host = socket.gethostname()
port = 65432

s = socket.socket()
s.connect((host, port))

print("Connected to the server")

# ---

# send message

text = "Hello"

print('send:', text)

data = text.encode()
send_data(s, data)

# recv message

data = recv_data(s)
text = data.decode()

print('recv:', text)

# ---

# send JSON

stock = {'open': 12, 'close': 15}

print('send:', stock)

text = json.dumps(stock)
data = text.encode()
send_data(s, data)

# recv JSON

data = recv_data(s)
text = data.decode()
stock = json.loads(text)

print('recv:', stock)

# ---

s.close()