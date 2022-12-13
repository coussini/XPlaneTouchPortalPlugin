import socket
import threading
import time
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

def handle_client(conn, addr):
    print("[thread] starting")

    # ---
    
    # recv message
    
    data = recv_data(conn)
    text = data.decode()

    print("[thread] client:", addr, 'recv:', text)
    
    # simulate longer work - to start next client at the same time
    time.sleep(5) 

    # send message
    
    text = "Bye!"
    print("[thread] client:", addr, 'send:', text)

    data = text.encode()
    send_data(conn, data)
    
    # ---

    # recv JSON

    data = recv_data(conn)
    text = data.decode()
    stock = json.loads(text)

    print("[thread] client:", addr, 'recv:', stock)

    # send JSON

    stock = {'diff': stock['close'] - stock['open']}
    
    print("[thread] client:", addr, 'send:', stock)

    text = json.dumps(stock)
    data = text.encode()
    send_data(conn, data)
    
    # ---
    
    conn.close()

    print("[thread] ending")
   
# --- main ---


host = socket.gethostname()
port = 65432

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # solution for "[Error 89] Address already in use". Use before bind()
s.bind((host, port))
s.listen(1)

all_threads = []

try:
    while True:
        print("Waiting for client")
        conn, addr = s.accept()
    
        print("Client:", addr)
        
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.start()
    
        all_threads.append(t)
except KeyboardInterrupt:
    print("Stopped by Ctrl+C")
finally:
    if s:
        s.close()
    for t in all_threads:
        t.join()