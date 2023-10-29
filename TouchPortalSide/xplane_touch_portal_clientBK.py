import sys
from argparse import ArgumentParser
import TouchPortalAPI as TP
import socket
import XPlaneUPD
import json
import os

import threading
import time

import logging

logging.basicConfig(level=logging.INFO,
                    format="%(levelname)-8s: %(name)-15s:  %(message)s",
                    filename="XplaneTouchPortalPlugin.log",
                    filemode="w")
#console = logging.StreamHandler()
#console.setLevel(logging.DEBUG)
#formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
#console.setFormatter(formatter)
#logging.getLogger('').addHandler(console)

__version__ = "1.0"

PLUGIN_ID = "XPlanePlugin"
LOGGER = logging.getLogger(PLUGIN_ID)

# Create the Touch Portal API client.
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

# This event handler will run once when the client connects to Touch Portal (successful pairing)
@TPClient.on('info') # <- TPClient.connect()
def onInfo(data):
    print("")
    print("====================================")
    print("SIGNAL: Touch Portal Event connect")
    print("====================================")
    print("")
    print("Connected to Touch Portal Version",data.get('tpVersionString', '?'),"plugin v",data.get('pluginVersion', '?'))
    print("")
    print("STATES are:")
    print("----------------")
    print(STATES)
    print("----------------")
    print("")
    print("Touch Portal returned following:")
    print("-------------------------------------")
    print(data)
    print("-------------------------------------")
    list_choices = []
    for x in STATES["datarefs"]:
        descrition = x["group"] + " - " + x["desc"]
        TPClient.createState(x["id"],descrition,x["value"],x["group"]) # create a TP State default value at runtime
        list_choices.append(x["desc"])
    TPClient.choiceUpdate("XPlanePlugin.Dataref.SetTwoStates.Name",list_choices) # update action option at runtime
    TPClient.choiceUpdate("XPlanePlugin.Dataref.ToggleTwoStates.Choice",list_choices) # update action option at runtime
# Action handlers, called when user activates one of this plugin's actions in Touch Portal.
@TPClient.on('action')
def onAction(data): # User press a button

    # if the json structure of data is not conform... skip it
    if not (action_data := data.get('data')) or not (action_actionId := data.get('actionId')):
        return

    LOGGER.info("")
    LOGGER.info(f"[SIGNAL]: Touch Portal Event Action on {data.get('data')[0]['value']}")
    LOGGER.info("")
    LOGGER.info("Touch Portal returned following:")
    LOGGER.info("-------------------------------")
    LOGGER.info(f"{data}")
    LOGGER.info("-------------------------------")
    LOGGER.info(f"data : {data.get('data')}")
    LOGGER.info(f"pluginId : {data.get('pluginId')}")
    LOGGER.info(f"actionId (EVENT) : {data.get('actionId')}")
    LOGGER.info(f"type : {data.get('type')}")
    LOGGER.info(f"data value : {data.get('data')[0]['value']}")
    ###
    ### Create a method to dispatch actions, create method for each action   
    ###
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
                    #XPUPD.WriteDataRef("AirbusFBW/ElecOHPArray[3]",1)

                    LOGGER.info(f"Value before is {x['value']}")
                    x["value"] = data.get('data')[1]['value']
                    LOGGER.info(f"Value after is {x['value']}")
                    TPClient.stateUpdate(x["id"],x["value"])
        case _:
            LOGGER.error(f"There is no action like : {data.get('actionId')}") 
    #for i in Statelist:
    #    print("Field for this event->",i)
    #    print("Value (actual)      ->",Statelist[i])

# Shutdown handler, called when Touch Portal wants to stop your plugin.
# Also, when a user do a TP Restart from windows systray
@TPClient.on('closePlugin')
def onShutdown(data):
    #print("Got Shutdown Message! Shutting Down the Plugin!")
    # Terminates the connection and returns from connect()
    LOGGER.info("SIGNAL: Touch Portal Event closePlugin")
    LOGGER.info(f"{PLUGIN_ID} v {__version__} disconnected.")
    TPClient.disconnect()

def foo():
    LOGGER.info(time.ctime())
    OLD = TPClient.getStatelist()
    NEW = XPUPD.GetValues()
    LOGGER.info(f"OLD = {OLD}")
    LOGGER.info(f"NEW = {NEW}")
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
        LOGGER.info("il y a eu changement du coté de xplane")
        OLD_VALUE = NEW_VALUE
    ''' 
    threading.Timer(WAIT_SECONDS, foo()).start()

def Task_GetDatarefValueFromXPlane():
    print("Task Executed")
    #print("Doing task...",helper.get_time())
    #allDatarefs = XPUPD.GetValues()
    #for (k, v) in allDatarefs.items():
    #   LOGGER.info(f"SCHEDULER: Key = {k}")
    #   LOGGER.info(f"SCHEDULER: value = {v}")

def GetDatarefValuesFromJsonFile():
    ret = 0  # sys.exit() value
    STATES = {"datarefs": []}
    
    LOGGER.info("INFO: Trying to load dataref from:")
    LOGGER.info("---------------------------------")
    LOGGER.info(f"{os.getcwd()}\Datarefs.json")
    LOGGER.info("---------------------------------")
    
    try:
        f = open('Datarefs.json')
        STATES = json.load(f)      
    except FileNotFoundError:
        LOGGER.error("")
        LOGGER.error("File does not exist")        
        ret = -1
    except ValueError:
        LOGGER.error("")
        LOGGER.error("Invalid JSON syntax")        
        ret = -1
    except Exception:
        LOGGER.error("")
        LOGGER.error("An error occurred")        
        ret = -1
    finally:
        f.close()

    return ret, STATES

def OpenGatewayXPlane():
    ret = 0  # sys.exit() value

    XPUPD = XPlaneUPD.XPlaneUdp() #instance
    XPUPD.defaultFreq = 1 # each second

    LOGGER.info("Trying to find any running XPlane IP")

    beacon = XPUPD.FindIp()
    
    return ret, XPUPD

def main():
    global TPClient

    ret = 0  # sys.exit() value

    # Set up and handle CLI arguments. These all relate to logging options.
    # The plugin can be run with "-h" option to show available argument options.
    # Addtionally, a file constaining any of these arguments can be specified on the command line
    # with the `@` prefix. For example: `plugin-example.py @config.txt`
    # The file must contain one valid argument per line, including the `-` or `--` prefixes.
    # See the plugin-example-conf.txt file for an example config file.
    #parser = ArgumentParser(fromfile_prefix_chars='@')
    #parser.add_argument("-d", action='store_true',
    #                    help="Use debug logging.")
    #parser.add_argument("-w", action='store_true',
    #                    help="Only log warnings and errors.")
    #parser.add_argument("-q", action='store_true',
    #                    help="Disable all logging (quiet).")
    #parser.add_argument("-l", metavar="<logfile>",
    #                    help=f"Log file name (default is ). Use 'none' to disable file logging.")
    #parser.add_argument("-s", metavar="<stream>",
    #                    help="Log to output stream: 'stdout' (default), 'stderr', or 'none'.")

    # his processes the actual command line and populates the `opts` dict.
    #opts = parser.parse_args()
    #del parser

    # trim option string (they may contain spaces if read from config file)
    #opts.l = opts.l.strip() if opts.l else 'none'
    #opts.s = opts.s.strip().lower() if opts.s else 'stdout'
    #LOGGER.info(PLUGIN_ID," & Parsers option = ",opts)

    # Set minimum logging level based on passed arguments
    #logLevel = "INFO"
    #if opts.q: logLevel = None
    #elif opts.d: logLevel = "DEBUG"
    #elif opts.w: logLevel = "WARNING"

    # set log file if -l argument was passed
    #if opts.l:
    #    logFile = None if opts.l.lower() == "none" else opts.l
    # set console logging if -s argument was passed
    #if opts.s:
    #    if opts.s == "stderr": logStream = sys.stderr
    #    elif opts.s == "stdout": logStream = sys.stdout
    #    else: logStream = None

    # Configure the Client logging based on command line arguments.
    # Since the Client uses the "root" logger by default,
    # this also sets all default logging options for any added child loggers, such as our g_log instance we created earlier.
    #TPClient.setLogFile(logFile)
    #TPClient.setLogStream(logStream)
    #TPClient.setLogLevel(logLevel)

    # ready to go
    #text = "Starting Touch Portal PLugin"+PLUGIN_ID+"v"+__version__
    LOGGER.info(f"Starting Touch Portal PLugin {PLUGIN_ID} v {__version__}")
    
    try:
        # Connect to Touch Portal desktop application.
        # If connection succeeds, this method will not return (blocks) until the client is disconnected.
        TPClient.connect()
        LOGGER.info("Touch Portal Client closed.")
    except ConnectionRefusedError:
        LOGGER.error("Cannot connect to Touch Portal, probably the apps in not running.")
    except KeyboardInterrupt:
        LOGGER.warning("Caught keyboard interrupt, exiting.")
    except Exception:
        # This will catch and report any critical exceptions in the base TPClient code,
        # _not_ exceptions in this plugin's event handlers (use onError(), above, for that).
        from traceback import format_exc
        LOGGER.error(f"Exception in TP Client")
        LOGGER.error(f"\n{format_exc()}")
        ret = -1
    finally:
        # Make sure TP Client is stopped, this will do nothing if it is already disconnected.
        TPClient.disconnect()

    # TP disconnected, clean up.
    del TPClient

    LOGGER.info(f"Starting {PLUGIN_ID} v {__version__} stopped.")
    return ret

if __name__ == "__main__":

    WAIT_SECONDS = 1
    
    ret, STATES = GetDatarefValuesFromJsonFile()

    if ret != -1: 
        ret, XPUPD = OpenGatewayXPlane()
    
    if ret != -1:
        ret = main()

    sys.exit(ret)