import json 
PLUGIN_ID = "XPlanePlugin"

STATES = {
    "datarefs": [
    {   
        "id":PLUGIN_ID+".ExtPower",
        "desc":"Ext power",
        "group":"OverHead",
        "value":"0",
        "dataref":"AirbusFBW/ElecOHPArray[3]"
    },
    {   "id":PLUGIN_ID+".Battery1",
        "desc":"Battery 1",
        "group":"OverHead",
        "value":"0",
        "dataref":"AirbusFBW/ElecOHPArray[5]"
    },
    {   "id":PLUGIN_ID+".Battery2",
        "desc":"Battery 2",
        "group":"OverHead",
        "value":"0",
        "dataref":"AirbusFBW/ElecOHPArray[6]"
    },
    {   "id":PLUGIN_ID+".Beacon",
        "desc":"Beacon",
        "group":"OverHead",
        "value":"0",
        "dataref":"AirbusFBW/OHPLightSwitches[0]"
    },
    {   "id":PLUGIN_ID+".Wing",
        "desc":"Wing",
        "group":"OverHead",
        "value":"0",
        "dataref":"AirbusFBW/OHPLightSwitches[1]"
    },
    {   "id":PLUGIN_ID+".ApuMaster",
        "desc":"Apu Master",
        "group":"OverHead",
        "value":"0",
        "dataref":"AirbusFBW/APUMaster"
    },
    {   "id":PLUGIN_ID+".IceIndNavAndLogo",
        "desc":"Ice Ind Nav & Logo",
        "group":"OverHead",
        "value":"0",
        "dataref":"AirbusFBW/OHPLightSwitches[9]"
    }
    ]
}

print(STATES)

with open( "Datarefs.json" , "w" ) as write: 
    json.dump( STATES , write, indent=4 )

