import struct
import socket

beacon = {
	"ip":"192.168.0.104",
	"port":49000
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 1) Subscribe to receive once per second
initialString = "<4sxii400s"
cmd = b'RREF'  # "Request DataRef(s)"
freq = 1       # number of times per second (integer)
index = 0      # "my" number, so I can match responsed with my request
#msg = struct.pack("<4sxii400s", cmd, freq, index, b'sim/aircraft/engine/acf_num_engines')
msg = struct.pack(initialString, cmd, freq, index, b'AirbusFBW/ElecOHPArray[3]')
sock.sendto(msg, (beacon['ip'], beacon['port']))

# 2) Block, waiting to receive a packet
data, addr = sock.recvfrom(2048)
print(data)
print("")
header = data[0:5]
if header != b'RREF,':
    raise ValueError("Unknown packet")

# 3) Unpack the data:
idx, value = struct.unpack("<if", data[5:13])
assert idx == index
print("reasult for this Dataref is {}".format(int(value)))

# 4) Unsubscribe -- as otherwise we'll continue to get this data, once every second!
freq = 0
msg = struct.pack(initialString, cmd, freq, index, b'AirbusFBW/ElecOHPArray[3]')
sock.sendto(msg, (beacon['ip'], beacon['port']))