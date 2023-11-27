import json 
import sys

json_data = {
    "command": "init",
    "datarefs": [
        {
            "dataref": "AirbusFBW/OHPLightSwitches[7]" # Strobe  -> int
        },
        {
            "dataref": "AirbusFBW/RMP3Lights[0]" # OVHD INTEG LT Brightness Knob -> float
        },
        {
            "dataref": "AirbusFBW/APUStarter" # APU Start -> int
        }
    ]
}

json_data = ''
recv_data = json.dumps(json_data).encode() # OUI temporairement
print()
print()
print(recv_data)

recv_data_decode = recv_data.decode()
print(recv_data_decode)
print()

dummy = recv_data_decode
tb_message = []
tb_message.append(recv_data_decode)

i = tb_message.find('"command": "init"',2,-1)
if i == -1:
    pass
else:
    tb = []
    while True:
        i = tb_message.find('"command": "init"',2,-1)
        print(i)
        break 

sys.exit(-1)

recv_data_decode = recv_data_decode[2:-2].replace("'", "").replace('"', '').replace('{', '').replace('}', '').split(',')
print('received decode without guille',recv_data_decode)

fave_phrase = "Hello world et les cochon!"

# find the index of the letter 'w' between the positions 3 and 8
index = fave_phrase.find("world",1,-1)
print()
print(index)
print()
