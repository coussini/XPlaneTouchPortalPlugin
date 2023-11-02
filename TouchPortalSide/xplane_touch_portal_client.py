# attention, on a pas la valeur XPlanePlugin.ExtPowerAvailable ???

import TouchPortalAPI as TP
import sys 
import os 
import json 
import XPlaneUPD
from setup_logger import LOGGER

__version__ = "1.0"
PLUGIN_ID = "XPlanePlugin"

# Create the Touch Portal API client instance.
try:
    TPClient = TP.Client(
        pluginId = PLUGIN_ID,  # required ID of this plugin
        sleepPeriod = 0.05,    # allow more time than default for other processes
        autoClose = True,      # automatically disconnect when TP sends "closePlugin" message
        checkPluginId = True,  # validate destination of messages sent to this plugin
        maxWorkers = 4,        # run up to 4 event handler threads
        updateStatesOnBroadcast = False  # do not spam TP with state updates on every page change
    )
except Exception as e:
    sys.exit(f"Could not create TP Client, exiting. Error was:\n{repr(e)}")
# TPClient: TP.Client = None  # instance of the TouchPortalAPI Client, created in main()

# This event handler will run once when the client connects to Touch Portal
@TPClient.on(TP.TYPES.onConnect)
def onStart(data):
    LOGGER.info(f"Connected to Touch Portal Version {data.get('tpVersionString', '?')} plugin v {data.get('pluginVersion', '?')})")
    LOGGER.info(f"=================")
    LOGGER.info(f"SECTION {data.get('type')}")
    LOGGER.info(f"=================")
    LOGGER.info(f"{data}")

    # create Touch Portal State at runtime, from dataref id, value and group
    list_choices = []
    for x in STATES["datarefs"]:
        descrition = x["group"] + " - " + x["desc"]
        TPClient.createState(x["id"],descrition,x["value"],x["group"])
        TPClient.stateUpdate(x["id"],x["value"])
        list_choices.append(x["desc"])
        if CanCallXPLANE:
            XPUPD.AddDataRef(x["id"],1) #  SE FAIT UNE FOIS
    LOGGER.info(f"Touch Portal States Id created")
    # update Touch Portal action option at runtime, from dataref id, value and group
    list_choices.sort() # sort options for ease of use
    TPClient.choiceUpdate("XPlanePlugin.Dataref.SetTwoStates.Name",list_choices)
    TPClient.choiceUpdate("XPlanePlugin.Dataref.ToggleTwoStates.Choice",list_choices)
    LOGGER.info(f"Touch Portal Choices of States Id have been updated")
    # mettre à jour les states de Touch Portal from dataref X-PLane
    if CanCallXPLANE:
        NEW = XPUPD.GetValues() # see def onStart(data): XPUPD.AddDataRef
        for key, value in NEW.items():
            TPClient.stateUpdate(key,value)
        LOGGER.info(f"Touch Portal States value updated from X-Plane")
    LOGGER.info(f"Voici la liste des states {TPClient.getStatelist()}")

# Action handlers, called when user activates one of this plugin's actions in Touch Portal.
@TPClient.on(TP.TYPES.onAction)
def onAction(data):

    LOGGER.info(f"=================")
    LOGGER.info(f"SECTION {data.get('type')}")
    LOGGER.info(f"=================")
    LOGGER.info(f"{data}")
    # dispatch Touch Portal Action Id
    match data.get('actionId'):
        case "XPlanePlugin.Dataref.ToggleTwoStates":
            for x in STATES["datarefs"]:
                if x['desc'] == data.get('data')[0]['value']:
                    LOGGER.info(f"Call XPlaneUDP python with : {data.get('actionId')} and {x['dataref']}") 
        case "XPlanePlugin.Dataref.SetTwoStates":
            for x in STATES["datarefs"]:
                # 
                # call MyXplane python server with : XPlanePlugin.Dataref.SetTwoStates  
                #                                    and AirbusFBW/ElecOHPArray[3]  with value 1
                # value before = 0
                # value after = 1
                #
                if x['desc'] == data.get('data')[0]['value']:
                    la_liste = TPClient.getStatelist()
                    LOGGER.info(f"La valeur de EnableExternalPower est: {la_liste['AirbusFBW/EnableExternalPower']}")
                    LOGGER.info("##################")
                    LOGGER.info("# CALL XPLANEUDP #")
                    LOGGER.info("##################")
                    LOGGER.info(f"Call XPlaneUDP python with : {data.get('actionId')} and {x['dataref']} with value {data.get('data')[1]['value']}")
                    ##############################
                    ###### CALL XPLANE UDP #######
                    ##############################
                    dataref = x["dataref"]
                    value = data.get('data')[1]['value']
                    LOGGER.info(f"Dataref is {dataref}")
                    LOGGER.info(f"Value is {value}")
                    if CanCallXPLANE:
                        XPUPD.WriteDataRef(str(dataref),float(value))
                    LOGGER.info(f"Value before is {x['value']}")
                    x["value"] = data.get('data')[1]['value']
                    LOGGER.info(f"Value after is {x['value']}")
                    TPClient.stateUpdate(x["id"],x["value"])
                    LOGGER.info(f"Touch Portal value of the States Id {x['id']} updated with {x['value']}")

        case _:
            LOGGER.error(f"There is no action like : {data.get('actionId')}") 

# Shutdown handler, called when Touch Portal wants to stop your plugin.
@TPClient.on(TP.TYPES.onShutdown) # or 'closePlugin'
def onShutdown(data):
    LOGGER.info(f"=================")
    LOGGER.info(f"SECTION {data.get('type')}")
    LOGGER.info(f"=================")
    LOGGER.info(f"{data}")
    LOGGER.info(f"Got Shutdown Message! Shutting Down the Plugin!")
    TPClient.disconnect()

def foo():
    LOGGER.info(time.ctime())
    OLD = TPClient.getStatelist()
    if CanCallXPLANE:
        NEW = XPUPD.GetValues() # see def onStart(data): XPUPD.AddDataRef
        LOGGER.info(f"NEW = {NEW}")
    LOGGER.info(f"OLD = {OLD}")
    '''
    for key, value in NEW.items():
        if int(value) != int(OLD.get(key)):
            #LOGGER.info("il y a eu changement du cote de xplane")
            LOGGER.info(f"[NEW] Pour la cle {key} et la valeur {value}")
            LOGGER.info(f"[OLD] Pour la cle {key} et la valeur {int(OLD.get(key))}")

    
    if int(OLD.get("AirbusFBW/ElecOHPArray[3]")) != int(NEW.get("AirbusFBW/ElecOHPArray[3]")):
        LOGGER.info("il y a eu changement du cote de xplane")
        LOGGER.info(OLD.get("AirbusFBW/ElecOHPArray[3]"))
        LOGGER.info(NEW.get("AirbusFBW/ElecOHPArray[3]"))

    #LOGGER.info(f"OLD = {OLD}")
    #LOGGER.info(f"NEW = {NEW}")
    #LOGGER.info(f"NEW = {NEW_VALUE}")
    
    a = sorted(OLD_VALUE.items()) != sorted(NEW_VALUE.items())
    if a:
        LOGGER.info("il y a eu changement du cotÃ© de xplane")
        OLD_VALUE = NEW_VALUE
    ''' 
    threading.Timer(WAIT_SECONDS, foo()).start()
def GetDatarefValuesFromJsonFile(JsonFile):
    
    STATES = {"datarefs": []}
    
    LOGGER.info(f"Trying to load datarefs from:")
    LOGGER.info(f"---------------------------------")
    LOGGER.info(f"{os.getcwd()}\{JsonFile}")
    LOGGER.info(f"---------------------------------")
    
    try:
        file = open(JsonFile, 'r')
        STATES = json.load(file)
        file.close()
        LOGGER.info(f"Datarefs successfully loaded from {JsonFile}")
    except FileNotFoundError:
        LOGGER.error(f"File {JsonFile} does not exist")
        return False
    except ValueError:
        LOGGER.error(f"Invalid JSON syntax in {JsonFile}")
        return False
    except Exception as err:
        from traceback import format_exc
        LOGGER.error(f"{err}")
        return False

    return True, STATES

def OpenGatewayXPlane():
    
    XPUPD = XPlaneUPD.XPlaneUdp() #instance
    XPUPD.defaultFreq = 1 # each second

    LOGGER.info(f"Trying to find any running XPlane IP")

    try:
        beacon = XPUPD.FindIp()
    except Exception as err:
        from traceback import format_exc
        LOGGER.error(f"{err}")
        return False, XPUPD
    else:
        LOGGER.info(f"Connected successfully with X-Plane")
    
    return True, XPUPD

def main():

    global TPClient, STATES, XPUPD, CanCallXPLANE

    successful = False
    CanCallXPLANE = False
    WAIT_SECONDS = 1
    JsonFile = 'Datarefs.json'

    successful, STATES = GetDatarefValuesFromJsonFile(JsonFile)
    
    if CanCallXPLANE:
        successful, XPUPD = OpenGatewayXPlane()
    else:
        LOGGER.info(f"Cannot connect to X-PLane due to the variable CanCallXPLANE")

    LOGGER.info(f"Trying to connect to Touch Portal Apps")
    
    try:
        TPClient.connect()
    except ConnectionRefusedError:
        LOGGER.error(f"Cannot connect to Touch Portal, probably it is not running")
        return
    except Exception as err:
        from traceback import format_exc
        LOGGER.error(f"{err}")
        return
    finally:
        LOGGER.info(f"TP Client Disconnected")
        TPClient.disconnect()

    del TPClient

    LOGGER.info(f"Return code = {successful}")
    sys.exit(successful)

if __name__ == "__main__":
    main()