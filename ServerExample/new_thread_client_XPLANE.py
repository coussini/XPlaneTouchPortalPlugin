import json
import socket
import struct

PLUGIN_ID = "XPlanePlugin"

STATES = [
    {   
        "id":PLUGIN_ID+".ExtPower",
        "desc":"Ext power",
        "value":"0",
        "dataref":"AirbusFBW/ElecOHPArray[3]"
    },
    {   "id":PLUGIN_ID+".Battery1",
        "desc":"Battery 1",
        "value":"0",
        "dataref":"AirbusFBW/ElecOHPArray[5]"
    },
    {   "id":PLUGIN_ID+".Battery2",
        "desc":"Battery 2",
        "value":"0",
        "dataref":"AirbusFBW/ElecOHPArray[6]"
    },
    {   "id":PLUGIN_ID+".Beacon",
        "desc":"Beacon",
        "value":"0",
        "dataref":"AirbusFBW/OHPLightSwitches[0]"
    },
    {   "id":PLUGIN_ID+".Wing",
        "desc":"Wing",
        "value":"0",
        "dataref":"AirbusFBW/OHPLightSwitches[1]"
    },
    {   "id":PLUGIN_ID+".ApuMaster",
        "desc":"Apu Master",
        "value":"0",
        "dataref":"AirbusFBW/APUMaster"
    },
    {   "id":PLUGIN_ID+".IceIndNavAndLogo",
        "desc":"Ice Ind Nav & Logo",
        "value":"0",
        "dataref":"AirbusFBW/OHPLightSwitches[9]"
    }
]

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

# -------------------------------------------------------------------------
# ---                               MAIN                                ---
# -------------------------------------------------------------------------
host = socket.gethostname()
port = 65432

s = socket.socket()
s.connect((host, port))

print("Connected to the server")

# send JSON

# stock = {'open': 12, 'close': 15}

for x in STATES:
    if x["desc"] == 'Ext power':
        panelAction = {'dataref' : x["dataref"], 'newValue' : 1}

print('Send to server:', panelAction)

text = json.dumps(panelAction) # format from single quote to double quote json data
print('Send to server dumps:', text)
data = text.encode() # add a "b" byte to data
print('Send to server data:', data)
send_data(s, data)

# recv JSON

#data = recv_data(s)
#text = data.decode()
#stock = json.loads(text)

#print('recv:', stock)

# ---

#s.close()