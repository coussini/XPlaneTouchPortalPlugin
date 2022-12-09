import struct
import socket

beacon = {
	"ip":"192.168.0.104",
	"port":49000
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 1) Subscribe to receive once per second
UDP_REQUEST = '<4sxf500s'  # UDP initial string
cmd = b'DREF'  # "Set DataRef"
value = 1      # value to set
dataref = "AirbusFBW/ElecOHPArray[3]"   
dataref = dataref.encode("utf-8")   

msg = struct.pack(UDP_REQUEST, cmd, value, dataref)
sock.sendto(msg, (beacon['ip'], beacon['port']))