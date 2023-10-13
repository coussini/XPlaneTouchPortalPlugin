import json
import socket
import struct
import threading


# -------------------------------------------------------------------------
# ---                              FUNCTION                             ---
# -------------------------------------------------------------------------
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

    # Recv JSON

    data = recv_data(conn)
    text = data.decode()
    stock = json.loads(text)

    print('recv actionID   :', stock.get('dataref'))
    print('recv wich value :', stock.get('newValue'))

    # Send JSON

    stock = {'diff': 25 - 6}
    
    text = json.dumps(stock)
    data = text.encode()
    send_data(conn, data)
    
    # Close

    conn.close()

    print("[thread] ending")
   
# -------------------------------------------------------------------------
# ---                               MAIN                                ---
# -------------------------------------------------------------------------
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
        conn, addr = s.accept() # receive a client host and address
        print("Client:", addr)
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.start()
        all_threads.append(t)

# The following KeyboardInterrupt is NOT NECCESSARY IN X_PLANE 12 (when shutdown x-plane that's stopped the python server)
#except KeyboardInterrupt: 
#    print("Stopped by Ctrl+C")
finally:
    if s:
        s.close()
    for t in all_threads:
        t.join()