# attention, on a pas la valeur XPlanePlugin.ExtPowerAvailable ???

# ORDRE pour bonne réaction Touch Portal
# 1) Démarrer X-Plane () attendre d'être dans l'avion
# 2) Démarrer Touch Portal Desktop (attendre d'être complètement démarré)
# 2) Démarrer Touch Portal I-Pad

import TouchPortalAPI as TP
import sys 
import os 
import json 
import XPlaneUPD

# imports below are optional, to provide argument parsing and logging functionality
from argparse import ArgumentParser
from TouchPortalAPI.logger import Logger

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

# Create the (optional) global logger, an instance of `TouchPortalAPI::Logger` helper class.
# Logging configuration is set up in main().
LOGGER = Logger(name = PLUGIN_ID)

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
        # The value from JSON is correct and validated
        TPClient.createState(x["id"],x["desc"],str(x["value"]),x["group"])
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
            for x in STATES["datarefs"]:
                if x["id"] == key:
                    if x["type"] == "int":
                        new_value = int(value)
                    elif x["type"] == "float":
                        new_value = round((float(value)/0.25),0) * 0.25
                    else:
                        new_value = value
                    break
            TPClient.stateUpdate(key,str(new_value))
        LOGGER.info(f"Touch Portal States value updated from X-Plane")
    #LOGGER.info(f"Voici la liste des states {TPClient.getStatelist()}")

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
                    LOGGER.info("##################")
                    LOGGER.info("# CALL XPLANEUDP #")
                    LOGGER.info("##################")
                    LOGGER.info(f"Call XPlaneUDP python with : {data.get('actionId')} and {x['dataref']} with value {data.get('data')[1]['value']}")
                    ##############################
                    ###### CALL XPLANE UDP #######
                    ##############################
                    dataref = x["dataref"]
                    value = data.get('data')[1]['value']
                    if CanCallXPLANE:
                        XPUPD.WriteDataRef(str(dataref),float(value)) # write alway float for XUPD
                    x["value"] = data.get('data')[1]['value']
                    TPClient.stateUpdate(x["id"],str(x["value"]))
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

def GetDatarefValuesFromJsonFile(JsonFile):
    
    STATES = {"datarefs": []}
    
    LOGGER.info(f"Trying to load datarefs from:")
    LOGGER.info(f"---------------------------------")
    LOGGER.info(f"{os.getcwd()}\{JsonFile}")
    LOGGER.info(f"---------------------------------")
    
    ######
    ######
    # After this, validate that each value correcponding to the type Float or Int or Data (str)(validation)
    '''
    def is_float(number):
        if isinstance(number, float):
            return True
        else:
            return False

    if is_float(number_1):
    # do something

    '''
    ######
    ######
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

    BeaconData = {}
    XPUPD = XPlaneUPD.XPlaneUdp() #instance
    XPUPD.defaultFreq = 1 # each second

    LOGGER.info(f"Trying to find any running XPlane IP")

    try:
        Is_good_Result, BeaconData = XPUPD.FindIp()
    except Exception as err:
        from traceback import format_exc
        LOGGER.error(f"{err}")
        return False, XPUPD
    else:
        LOGGER.info(f"Connected successfully with X-Plane version {BeaconData['XPlaneVersion']}")
    
    return True, XPUPD

def main():

    global LOGGER, TPClient, STATES, BeaconData, XPUPD, CanCallXPLANE
    #global LOGGER, TPClient, STATES, XPUPD, CanCallXPLANE

##################################
    # default log file destination
    logFile = f"./{PLUGIN_ID}.log"
    # default log stream destination
    logStream = sys.stdout

    # Set up and handle CLI arguments. These all relate to logging options.
    # The plugin can be run with "-h" option to show available argument options.
    # Addtionally, a file constaining any of these arguments can be specified on the command line
    # with the `@` prefix. For example: `plugin-example.py @config.txt`
    # The file must contain one valid argument per line, including the `-` or `--` prefixes.
    # See the plugin-example-conf.txt file for an example config file.
    parser = ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument("-d", action='store_true',
                        help="Use debug logging.")
    parser.add_argument("-w", action='store_true',
                        help="Only log warnings and errors.")
    parser.add_argument("-q", action='store_true',
                        help="Disable all logging (quiet).")
    parser.add_argument("-l", metavar="<logfile>",
                        help=f"Log file name (default is '{logFile}'). Use 'none' to disable file logging.")
    parser.add_argument("-s", metavar="<stream>",
                        help="Log to output stream: 'stdout' (default), 'stderr', or 'none'.")

    # his processes the actual command line and populates the `opts` dict.
    opts = parser.parse_args()
    del parser

    # trim option string (they may contain spaces if read from config file)
    opts.l = opts.l.strip() if opts.l else 'none'
    opts.s = opts.s.strip().lower() if opts.s else 'stdout'
    print(opts)

    # Set minimum logging level based on passed arguments
    logLevel = "INFO"
    if opts.q: logLevel = None
    elif opts.d: logLevel = "DEBUG"
    elif opts.w: logLevel = "WARNING"

    # set log file if -l argument was passed
    if opts.l:
        logFile = None if opts.l.lower() == "none" else opts.l
    # set console logging if -s argument was passed
    if opts.s:
        if opts.s == "stderr": logStream = sys.stderr
        elif opts.s == "stdout": logStream = sys.stdout
        else: logStream = None

    # Configure the Client logging based on command line arguments.
    # Since the Client uses the "root" logger by default,
    # this also sets all default logging options for any added child loggers, such as our g_log instance we created earlier.
    TPClient.setLogFile(logFile)
    TPClient.setLogStream(logStream)
    TPClient.setLogLevel(logLevel)

    # ready to go
##################################

    successful = False
    CanCallXPLANE = False
    WAIT_SECONDS = 1
    JsonFile = 'Datarefs.json'

    successful, STATES = GetDatarefValuesFromJsonFile(JsonFile)
    
    if CanCallXPLANE:
        successful, XPUPD = OpenGatewayXPlane()
        if not successful:
            CanCallXPLANE = False
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