import json
from argparse import ArgumentParser

import TouchPortalAPI as TP
from TouchPortalAPI.logger import Logger

__version__ = "1.0"
PLUGIN_ID = "XPlanePlugin"

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
    g_log.info(f"")
    g_log.info(f"Connected")
    g_log.info(f"TP returned")
    g_log.info(f"-----------")
    g_log.debug(f"Data->: {data}")
    TPClient.createState("AirbusFBW_ElecOHPArray[3]","External Power","0")

# Action handlers, called when user activates one of this plugin's actions in Touch Portal.
@TPClient.on('action')
def onAction(data):
    g_log.info(f"")
    g_log.info(f"Action catch!")
    g_log.info(f"TP returned")
    g_log.info(f"-----------")
    g_log.info(f"")
    actionId = data["actionId"]
    g_log.debug(f"Event->: {actionId}")
    Dataref_name = list(TPClient.getStatelist().keys())[0]
    Dataref_value = list(TPClient.getStatelist().values())[0]
    g_log.debug(f"Dataref->: {Dataref_name}")
    ###
    ### Create a method to dispatch actions, create method for each action   
    ###
    if data["actionId"] == "XPlanePlugin.Dataref.Set":
        #print("value will be->",data["data"][1]["value"])
        pass
    else:
        #print("Value was->",Dataref_value)
        pass
    #for i in Statelist:
    #    print("Field for this event->",i)
    #    print("Value (actual)      ->",Statelist[i])
# ListChange handlers, called when user activates one of this plugin's actions in Touch Portal.
@TPClient.on('listChange')
def onAction(data):
    pass
    #print("ListChange catch!")
    #print("TP returned")

# Shutdown handler, called when Touch Portal wants to stop your plugin.
@TPClient.on('closePlugin')
def onShutdown(data):
    #print("Got Shutdown Message! Shutting Down the Plugin!")
    # Terminates the connection and returns from connect()
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
    g_log.info(f"Starting {PLUGIN_ID} v{__version__}")

    try:
        # Connect to Touch Portal desktop application.
        # If connection succeeds, this method will not return (blocks) until the client is disconnected.
        TPClient.connect()
        g_log.info('TP Client closed.')
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

    g_log.info(f"Starting {PLUGIN_ID} v{__version__} stopped.")
    return ret

if __name__ == "__main__":
    sys.exit(main())