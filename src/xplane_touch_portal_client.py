import sys
from argparse import ArgumentParser

import TouchPortalAPI as TP
from TouchPortalAPI.logger import Logger

__version__ = "1.0"
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
# Create the Touch Portal API client.
try:
    TPClient = TP.Client(
        pluginId = PLUGIN_ID,  # required ID of this plugin
        sleepPeriod = 0.05,    # allow more time than default for other processes
        autoClose = True,      # automatically disconnect when TP sends "closePlugin" message
        checkPluginId = True,  # validate destination of messages sent to this plugin
        maxWorkers = 4,        # run up to 4 event handler threads
        updateStatesOnBroadcast = False,  # do not spam TP with state updates on every page change
    )
except Exception as e:
    sys.exit(f"Could not create TP Client, exiting. Error was:\n{repr(e)}")
# TPClient: TP.Client = None  # instance of the TouchPortalAPI Client, created in main()

# Crate the (optional) global logger, an instance of `TouchPortalAPI::Logger` helper class.
# Logging configuration is set up in main().
g_log = Logger(name = PLUGIN_ID)

# This event handler will run once when the client connects to Touch Portal
@TPClient.on('info')
def onInfo(data):
    print("Connected!")
    print("TP RETURNED FOLLOWING:")
    print(data)
    print("Connected to TP v",data.get('tpVersionString', '?'),"plugin v",data.get('pluginVersion', '?'))
    for x in STATES:
        TPClient.createState(x["id"],x["desc"],x["value"])

# Action handlers, called when user activates one of this plugin's actions in Touch Portal.
@TPClient.on('action')
def onAction(data):
    print("")
    print("Action catch!")
    print("TP RETURNED FOLLOWING DATA:")

    if not (action_data := data.get('data')) or not (action_actionId := data.get('actionId')):
        return
    
    print(data)
    print("")
    print("GET SEPARATE PART FROM RETURNED DATA")
    print("data :",data.get('data'))
    print("pluginId :",data.get('pluginId'))
    print("actionId (EVENT) :",data.get('actionId'))
    print("type :",data.get('type'))
    print("data value :",data.get('data')[0]["value"])
    print("")
    ###
    ### Create a method to dispatch actions, create method for each action   
    ###
    match data.get('actionId'):
        case "XPlanePlugin.Dataref.ToggleTwoStates":
            for x in STATES:
                if x["desc"] == data.get('data')[0]["value"]:
                    print("call MyXplane python server with :",data.get('actionId')," and",x["dataref"]) 
        case "XPlanePlugin.Dataref.SetTwoStates":
            for x in STATES:
                if x["desc"] == data.get('data')[0]["value"]:
                    print("call MyXplane python server with :",data.get('actionId')," and",x["dataref"]," with value",data.get('data')[1]["value"])
                    print("value before =",x["value"])
                    x["value"] = data.get('data')[1]["value"]
                    print("value after =",x["value"])
                    TPClient.stateUpdate(x["id"],x["value"])
        case _:
            print("there is no action like :",data.get('actionId')) 
    #for i in Statelist:
    #    print("Field for this event->",i)
    #    print("Value (actual)      ->",Statelist[i])

# Shutdown handler, called when Touch Portal wants to stop your plugin.
@TPClient.on('closePlugin')
def onShutdown(data):
    #print("Got Shutdown Message! Shutting Down the Plugin!")
    # Terminates the connection and returns from connect()
    print("ClosePlugin!")
    print(PLUGIN_ID,"v",__version__,"disconnected.")
    TPClient.disconnect()

def main():
    global TPClient, g_log
    ret = 0  # sys.exit() value

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
    print("Starting",{PLUGIN_ID},"v",__version__)

    try:
        # Connect to Touch Portal desktop application.
        # If connection succeeds, this method will not return (blocks) until the client is disconnected.
        TPClient.connect()
        print('TP Client closed.')
    except KeyboardInterrupt:
        g_log.warning("Caught keyboard interrupt, exiting.")
    except Exception:
        # This will catch and report any critical exceptions in the base TPClient code,
        # _not_ exceptions in this plugin's event handlers (use onError(), above, for that).
        from traceback import format_exc
        g_log.error(f"Exception in TP Client:\n{format_exc()}")
        ret = -1
    finally:
        # Make sure TP Client is stopped, this will do nothing if it is already disconnected.
        TPClient.disconnect()

    # TP disconnected, clean up.
    del TPClient

    print("Starting",PLUGIN_ID,"v",__version__,"stopped.")
    return ret

if __name__ == "__main__":
    sys.exit(main())