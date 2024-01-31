import socket

msgFromClient = "Hello UDP Server"
bytesToSend = str.encode(msgFromClient)
HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432
serverAddressPort   = (HOST,PORT)
bufferSize          = 1024

# Create a UDP socket at client side
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.settimeout(0)

# Send to server using created UDP socket
UDPClientSocket.sendto(bytesToSend, serverAddressPort)
print("Recieving data from server")
while True:
	try:
	    data = UDPClientSocket.recvfrom(1024)
	    UDPClientSocket.settimeout(0)
	except socket.error:
	    print("nothing")
	else:
		print(data)
		break

