import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('',8888))
s.setblocking(0)
data =''
address = ''
while True:
    try:
        data,address = s.recvfrom(10000)
    except socket.error:
        pass
    else: 
        print(f"recv: {data[0]} times {len(data)}")