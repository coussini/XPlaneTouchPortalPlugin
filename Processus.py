import xp 

def get_dataref_name_and_index(cls,dataref):
    
    """
    receive a dataref from a JSON
    theres examples of dataref names including or not an index
    'sim/aircraft/electrical/num_batteries'
    'sim/multiplayer/combat/team_status[3]' the index is 3
    """

    dataref_index = None 
    dataref_name = dataref.replace("["," ")
    dataref_name = dataref_name.replace("]"," ")
    dataref_name = dataref_name.split()

    # it's a dataref with an index
    if len(dataref_name) == 2: 
        dataref_index = dataref_name[1]
        dataref_name = dataref_name[0]
    
    # it's not a dataref with an index
    else: 
        dataref_name = dataref_name[0]

    return dataref_name,dataref_index 

def get_dataref_address_type_value(cls,dataref_name,dataref_index):
    
    """ receive a dataref including or not an index """

    dataref_type = None
    is_dataref_writable = False
    dataref_value = None

    # comment from X-Plane: findDataRef function is relatively expensive; save the result. 
    # Do not repeat a lookup every time you need to read or write it.
    dataref_address = xp.findDataRef(dataref_name)
    
    if dataref_address != None:
        dataref_type = xp.getDataRefTypes(dataref_address)
        is_dataref_writable = xp.canWriteDataRef(dataref_address)
        dataref_value = cls.read_a_dataref(dataref_address,dataref_type,dataref_index)
    
    return dataref_address,dataref_type,is_dataref_writable,dataref_value

def read_a_dataref(cls,dataref_address,dataref_type,dataref_index):

    """ read a dataref according to it's address, type and index """

    if bool(dataref_type & xp.Type_Unknown):
        return None
    
    elif bool(dataref_type & xp.Type_Int):
        return xp.getDatai(dataref_address) 
    
    elif bool(dataref_type & xp.Type_Float):
        return xp.getDataf(dataref_address) 
    
    elif bool(dataref_type & xp.Type_Double):
        return xp.getDatad(dataref_address) 
    
    elif bool(dataref_type & xp.Type_FloatArray):
        values = []
        xp.getDatavf(dataref_address, values, int(dataref_index), 1)
        return values[0]
    
    elif bool(dataref_type & xp.Type_IntArray):
        values = []
        xp.getDatavi(dataref_address, values, int(dataref_index), 1)
        return values[0]
    
    elif bool(dataref_type & xp.Type_Data):
        return xp.getDatas(dataref_address) # Data
    
    else:
        return None

def write_a_dataref(cls,dataref_address,dataref_type,dataref_index,dataref_value):

    """ write a dataref according to it's address, type, index and value """

    print(dataref_type,xp.Type_Unknown)
    if bool(dataref_type & xp.Type_Unknown):
        return False
    
    elif bool(dataref_type & xp.Type_Int):
        xp.setDatai(dataref_address,dataref_value) 
    
    elif bool(dataref_type & xp.Type_Float):
        xp.setDataf(dataref_address,dataref_value) 
    
    elif bool(dataref_type & xp.Type_Double):
        xp.setDatad(dataref_address,dataref_value) 
    
    elif bool(dataref_type & xp.Type_FloatArray):
        xp.setDatavf(dataref_address, [dataref_value], int(dataref_index), 1)
    
    elif bool(dataref_type & xp.Type_IntArray):
        xp.setDatavi(dataref_address, [dataref_value], int(dataref_index), 1)
    
    elif bool(dataref_type & xp.Type_Data):
        xp.setDatas(dataref_address) # Data
    
    else:
        return False

    return True

# receiving dataJson "init"
#
"""
==============
Initialization
==============
dataJson = {
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
        },
    ]
}
"""
cls.acf_ui_name  = None
array_dataref_full_name = [] # dataref full name with bracket and value
array_dataref_address = [] # address of the finded dataref
array_dataref_type = [] # a number that should be compare with xp.Type_Int...
array_is_dataref_writable = [] # if it's writable dataset
array_dataref_value = [] # value of dataref in str format ### THIS IS THE VALUE INTO Touch Portal Page Side

"""
NOTE
                    if x["type"] == "int":
                        new_value = int(value)
                    elif x["type"] == "float":
                        new_value = round((float(value)/0.25),0) * 0.25

"""
if dataJson["command"] == "init":
    # at beginning, verify if current touch portal variable corresponding to the current loaded aircraft
    dataref_name = "sim/aircraft/view/acf_ui_name"
    dataref_index = None
    dataref_address,dataref_type,is_dataref_writable,dataref_value = cls.get_dataref_address_type_value(dataref_name,dataref_index)
    if cls.acf_ui_name  != dataref_value:
        cls.acf_ui_name  = dataref_value # keep the aircraft name to check if the user change the aircraft
        for x in dataJson["datarefs"]:
            dataref_name,dataref_index = cls.get_dataref_name_and_index(x["dataref"])
            dataref_address,dataref_type,is_dataref_writable,dataref_value = cls.get_dataref_address_type_value(dataref_name,dataref_index)
            if (dataref_type is None and dataref_value is None):
                print(f"")
                print(f"The {cls.acf_ui_name} does not correspond to your touch portal page!")
                print(f"")
                return False
            else:
                array_dataref_full_name.append(x["dataref"])
                array_dataref_address.append(dataref_address)
                array_dataref_type.append(dataref_type)
                array_is_dataref_writable.append(is_dataref_writable)
                array_dataref_value.append(dataref_value) 

# sending dataJson "init"
#
#
dataJson = {
    "command": "init",
    "datarefs": [
        {
            "dataref": "AirbusFBW/OHPLightSwitches[7]", # Strobe  -> int
            "value": "2" # Strobe  -> int
        },
        {
            "dataref": "AirbusFBW/RMP3Lights[0]", # OVHD INTEG LT Brightness Knob -> float
            "value": "0.50" # OVHD INTEG LT Brightness Knob -> float
        },
        {
            "dataref": "AirbusFBW/APUStarter", # APU Start -> int
            "value": "4" # APU Start -> int
        }
    ]
}


# receiving dataJson "update"
#
"""
===============
Write a dataset
===============
dataJson = {
    "command": "update",
    "dataref": "AirbusFBW/OHPLightSwitches[7]", # Strobe  -> int
    "value": "0"
}
"""
i = array_dataref_full_name.index(dataJson["dataref"])
dataref_address = array_dataref_address[i]
dataref_type = array_dataref_type[i]
dataref_index = array_dataref_index[i]
dataref_value = dataJson["value"]
array_dataref_value[i] = dataJson["value"]
rc = write_a_dataref(cls,dataref_address,dataref_type,dataref_index,dataref_value)

# sending dataJson "write"
#
#
dataJson = {
    "command": "write",
    "dataref": "AirbusFBW/OHPLightSwitches[7]", # Strobe  -> int
    "value": "True or False" # rc from write_a_dataref()
}


# ============= L O O P ===============
# sending dataJson "read"
#
# dataref_value = read_a_dataref(cls,dataref_address,dataref_type,dataref_index)
"""

for x in array_dataref_full_name:
    current_value = read_a_dataref(cls,array_dataref_address[x],array_dataref_type[x],array_dataref_index[x])
    if current_value != array_dataref_value[x]:
        send current_value to Touch Portal (SEE FORMAT BELLOW)


===============
read a dataset
===============
dataJson = {
    "command": "read",
    "dataref": "AirbusFBW/OHPLightSwitches[7]", # Strobe  -> int
    "value": "0"
}
"""