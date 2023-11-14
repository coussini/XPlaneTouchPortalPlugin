"""
Written with Pep8 style guide 
Note: cls replaces self in Pep8 convention for classes.
    Always use self for the first argument to instance methods.
    Always use cls for the first argument to class methods.
"""
import xp
import time  # for test only

class PythonInterface:

    def __init__(cls):
        cls.name = "Hello World"
        cls.sig = "xppython3.hello"
        cls.desc = "Simple Hello World"
        cls.acf_ui_name  = None
        cls.start_program = False


    def XPluginStart(cls):

        return cls.name, cls.sig, cls.desc

    def XPluginStop(cls):

        pass

    def XPluginEnable(cls): # est appelé lorsque x-plane active les plugins (à tout moment)

        return 1

    def XPluginDisable(cls):

        pass

    def XPluginReceiveMessage(cls, inFromWho, inMessage, inParam):
        
        if inMessage == xp.MSG_AIRPORT_LOADED and inParam == 0:
            dataref_name = "sim/aircraft/view/acf_ui_name"
            dataref_index = None
            dataref_address,dataref_type,is_dataref_writable,dataref_value = cls.get_dataref_address_type_value(dataref_name,dataref_index)
            if cls.acf_ui_name  != dataref_value:
                cls.acf_ui_name  = dataref_value # keep the aircraft name to check if the user change the aircraft
                cls.start_program = cls.start_the_program(cls.acf_ui_name)
        
        pass 

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

    def start_the_program(cls,aircraft_name):

        print(f"")
        print(f"Load Aircraft name:{aircraft_name}")

        # Adirs IR1, BAT1, Strobe
        dataref_list = [
        "AirbusFBW/ElecOHPArray[5]",
        "AirbusFBW/ElecOHPArray[6]",
        "AirbusFBW/ElecOHPArray[3]",
        "AirbusFBW/PanelFloodBrightnessLevel",
        "sim/flightmodel/position/elevation",
        "AirbusFBW/RMP3Lights[0]",
        "AirbusFBW/OHPLightSwitches[7]"
        ]
        
        for dataref in dataref_list:
            dataref_name,dataref_index = cls.get_dataref_name_and_index(dataref)
            dataref_address,dataref_type,is_dataref_writable,dataref_value = cls.get_dataref_address_type_value(dataref_name,dataref_index)
            #print(dataref_type,dataref_value)
            if (dataref_type is None and dataref_value is None):
                print(f"")
                print(f"The {cls.acf_ui_name} does not correspond to your touch portal page!")
                print(f"")
                return False
            #print(f"For dataref : {dataref} the type is {dataref_type}, the value is {dataref_value} and is writable ? {is_dataref_writable}")
            #return_value = cls.write_a_dataref(dataref_address,dataref_type,dataref_index,1)
        print(f"")
        print(f"The {cls.acf_ui_name} is ready for your touch portal page!")
        print(f"")
        return True
