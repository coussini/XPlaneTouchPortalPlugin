# attention, on a pas la valeur XPlanePlugin.ExtPowerAvailable ???

import TouchPortalAPI as TP
import sys 
import os 
import json 
import XPlaneUPD
import logging

__version__ = "1.0"
PLUGIN_ID = "XPlanePlugin"

# Create the logging facility.
logging.basicConfig(level=logging.INFO,
                    format="%(levelname)8s: %(name)15s:  %(message)s",
                    filename="xplane_touch_portal_client.log",
                    filemode="w")
LOGGER = logging.getLogger(PLUGIN_ID)

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
    option = [
    {
      "id":"option id",
      "title":"option title 1"
    },
    {
      "id":"option id",
      "title":"option title 2"
    }
  ]
    LOGGER.info(f"Connected to Touch Portal Version {data.get('tpVersionString', '?')} plugin v {data.get('pluginVersion', '?')})")
    LOGGER.info(f"=================")
    LOGGER.info(f"SECTION {data.get('type').upper()}")
    LOGGER.info(f"=================")
    LOGGER.info(f"{data}")

    # create Touch Portal State at runtime, from dataref id, value and group
    list_choices = []
    for x in STATES["datarefs"]:
        descrition = x["group"] + " - " + x["desc"]
        TPClient.createState(x["id"],descrition,x["value"],x["group"])
        list_choices.append(x["desc"])
    LOGGER.info(f"Touch Portal States Id created")

    # update Touch Portal action option at runtime, from dataref id, value and group
    #TPClient.choiceUpdate("XPlanePlugin.Dataref.SetTwoStates.Name",list_choices)
    TPClient.choiceUpdate("XPlanePlugin.Dataref.SetTwoStates.Name",list_choices)
    TPClient.choiceUpdate("XPlanePlugin.Dataref.ToggleTwoStates.Choice",list_choices)
    LOGGER.info(f"Touch Portal Choices of States Id have been updated")

# Action handlers, called when user activates one of this plugin's actions in Touch Portal.
@TPClient.on(TP.TYPES.onAction)
def onAction(data):

    LOGGER.info(f"=================")
    LOGGER.info(f"SECTION {data.get('type').upper()}")
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
                    converted_dataref = str(dataref)
                    XPUPD.WriteDataRef(dataref,int(value))
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
    LOGGER.info(f"SECTION {data.get('type').upper()}")
    LOGGER.info(f"=================")
    LOGGER.info(f"{data}")
    LOGGER.info(f"Got Shutdown Message! Shutting Down the Plugin!")
    TPClient.disconnect()

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
        LOGGER.error(f"Datarefs successfully loaded from {JsonFile}")
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
    
    global TPClient

    LOGGER.info(f"Trying to connect to Touch Portal Apps")
    
    try:
        TPClient.connect()
    except ConnectionRefusedError:
        LOGGER.error(f"Cannot connect to Touch Portal, probably it is not running")
        return False
    except Exception as err:
        from traceback import format_exc
        LOGGER.error(f"{err}")
        return False
    finally:
        TPClient.disconnect()

    del TPClient

    return True

if __name__ == "__main__":

    global successful, STATES

    WAIT_SECONDS = 1
    JsonFile = 'Datarefs.json'
    
    successful, STATES = GetDatarefValuesFromJsonFile(JsonFile)
    
    if successful:
        successful, XPUPD = OpenGatewayXPlane()

    if successful:
        successful = main()

    LOGGER.error(f"Return code = {successful}")
    sys.exit(successful)
