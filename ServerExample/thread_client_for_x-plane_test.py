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

# --- functions ---

def send_data(conn, data):
    size = len(data)
    size_in_4_bytes = struct.pack('I', size)
    conn.send(size_in_4_bytes)
    conn.send(data)

# -------------------------------------------------------------------------
# ---                               MAIN                                ---
# -------------------------------------------------------------------------
host = socket.gethostname()
port = 65432

s = socket.socket()
s.connect((host, port))

print("Connected to the server")

for x in STATES:
    if x["desc"] == 'Ext power':
        panelAction = {'dataref' : x["dataref"], 'newValue' : 1}

print('send:', panelAction)

text = json.dumps(panelAction)
data = text.encode()
send_data(s, data)

s.close()