#####
# une bonne façon de valider
#####
'''
        if notificationId and title and msg and options and isinstance(options, list):
            for option in options:
                if 'id' not in option.keys() or 'title' not in option.keys():
                    self.__raiseException("all options require id and title keys")
'''

# attention, on a pas la valeur XPlanePlugin.ExtPowerAvailable ???

# ORDRE pour bonne réaction Touch Portal
# 1) Démarrer X-Plane () attendre d'être dans l'avion
# 2) Démarrer Touch Portal Desktop (attendre d'être complètement démarré)
# 2) Démarrer Touch Portal I-Pad

import TouchPortalAPI as TP
import sys 
import os 
import selectors
import socket
import json
import time
import random
import threading

# imports below are optional, to provide argument parsing and logging functionality
from argparse import ArgumentParser
from TouchPortalAPI.logger import Logger

__version__ = '1.0'
PLUGIN_ID = 'XPlanePlugin'

# Create the Touch Portal API client instance.
try:
    TPClient = TP.Client(
        pluginId = PLUGIN_ID,  # required ID of this plugin
        sleepPeriod = 0.05,    # allow more time than default for other processes
        autoClose = True,      # automatically disconnect when TP sends 'closePlugin' message
        checkPluginId = True,  # validate destination of messages sent to this plugin
        maxWorkers = 4,        # run up to 4 event handler threads
        updateStatesOnBroadcast = False  # do not spam TP with state updates on every page change
    )
except Exception as e:
    sys.exit(f'Could not create TP Client, exiting. Error was:\n{repr(e)}')

# Create the (optional) global logger, an instance of `TouchPortalAPI::Logger` helper class.
# Logging configuration is set up in main().
LOGGER = Logger(name = PLUGIN_ID)

# This event handler will run once when the client connects to Touch Portal
@TPClient.on(TP.TYPES.onConnect) # or 'info'
def onStart(data):
    LOGGER.info(f'Connected to Touch Portal Version {data.get("tpVersionString", "?")} plugin v {data.get("pluginVersion", "?")})')
    LOGGER.info(f'=================')
    LOGGER.info(f'SECTION {data.get("type")}')
    LOGGER.info(f'=================')
    LOGGER.info(f'{data}')
    LOGGER.info(f'{STATES}')
    '''
    # create Touch Portal State at runtime, from dataref id, value and group
    list_choices = []
    list_dataref = []
    for x in STATES["datarefs"]:
        # The value from JSON is correct and validated
        TPClient.createState(x["id"],x["desc"],str(x["value"]),x["group"])
        list_choices.append(x["desc"])
        ###
        # create a list of x["id"]; after this send command INIT within this list
        ###
    '''
    '''        
    # a test for a Touch Portal Action
    json_data_init = {
        'command': 'init',
        'datarefs': [
            {
                'dataref': 'AirbusFBW/OHPLightSwitches[7]' # Strobe  -> int
            },
            {
                'dataref': 'AirbusFBW/RMP3Lights[0]' # OVHD INTEG LT Brightness Knob -> float
            }

        append x["id"] to json_data_init
        AFTER for x in STATES["datarefs"]:... envoyer json_data_init
        RECEVOIR json_data_init du serveur qui contient les valeurs
        faire un for x... pour extraire les dataref et valeurs et
        faire un TPClient.stateUpdate(x["id"],str(valeur_recu))

                    if x["type"] == "int":
                        new_value = int(value)
                    elif x["type"] == "float":
                        new_value = round((float(value)/0.25),0) * 0.25
                    else:
                        new_value = value

    la valeur reçu est inscrite en str pour touch portal

    LOGGER.info(f"Touch Portal States Id created")
    
    LOGGER.info(f'Trying to connect to X-Plane server')
    #try:
    process_xplane.set()
    process_xplane_data()
    #except Exception as err:
    #    from traceback import format_exc
    #    LOGGER.error(f'{err}')
    '''


# Action handlers, called when user activates one of this plugin's actions in Touch Portal.
@TPClient.on(TP.TYPES.onAction) # or 'action'
def onAction(data):
    LOGGER.info(f'=================')
    LOGGER.info(f'SECTION {data.get("type")}')
    LOGGER.info(f'=================')
    LOGGER.info(f'{data}')

# Shutdown handler, called when Touch Portal wants to stop your plugin.
@TPClient.on(TP.TYPES.onShutdown) # or 'closePlugin'
def onShutdown(data):
    LOGGER.info(f'=================')
    LOGGER.info(f'SECTION {data.get("type")}')
    LOGGER.info(f'=================')
    LOGGER.info(f'{data}')
    LOGGER.info(f'Got Shutdown Message! Shutting Down the Plugin!')
    TPClient.disconnect()

# Error handler, called when Touch Portal catch an error.
@TPClient.on(TP.TYPES.onError) # or 'error'
def onShutdown(data):
    LOGGER.info(f'=================')
    LOGGER.info(f'SECTION {data.get("type")}')
    LOGGER.info(f'=================')
    LOGGER.info(f'{data}')
    LOGGER.info(f'Got error! Shutting Down the Plugin!')
    TPClient.disconnect()

def GetDatarefValuesFromJsonFile(JsonFile):
    
    STATES = {'datarefs': []}
    MSG = None
    
    LOGGER.info(f'Trying to load datarefs from:')
    LOGGER.info(f'---------------------------------')
    LOGGER.info(f'{os.getcwd()}\{JsonFile}')
    LOGGER.info(f'---------------------------------')
    
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
        LOGGER.info(f'Datarefs successfully loaded from {JsonFile}')
    except FileNotFoundError:
        #LOGGER.error(f'File {JsonFile} does not exist')
        MSG = f'File {JsonFile} does not exist'
        return False, MSG, None
    except ValueError:
        #LOGGER.error(f'Invalid JSON syntax in {JsonFile}')
        MSG = f'Invalid JSON syntax in {JsonFile}'
        return False, MSG, None
    except Exception as err:
        from traceback import format_exc
        #LOGGER.error(f'str({err})')
        MSG = f'An exception occured for {JsonFile}'
        return False, MSG, None

    return True, MSG, STATES

def logging_configuration(log_file_name):

    # default log file destination
    logFile = log_file_name
    # default log stream destination
    logStream = sys.stdout

    # Set up and handle CLI arguments. These all relate to logging options.
    # The plugin can be run with '-h' option to show available argument options.
    # Addtionally, a file constaining any of these arguments can be specified on the command line
    # with the `@` prefix. For example: `plugin-example.py @config.txt`
    # The file must contain one valid argument per line, including the `-` or `--` prefixes.
    # See the plugin-example-conf.txt file for an example config file.
    parser = ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('-d', action='store_true',
                        help='Use debug logging.')
    parser.add_argument('-w', action='store_true',
                        help='Only log warnings and errors.')
    parser.add_argument('-q', action='store_true',
                        help='Disable all logging (quiet).')
    parser.add_argument('-l', metavar='<logfile>',
                        help=f'Log file name (default is {logFile}). Use "none" to disable file logging.')
    parser.add_argument('-s', metavar='<stream>',
                        help='Log to output stream: "stdout" (default), "stderr", or "none".')

    # his processes the actual command line and populates the `opts` dict.
    opts = parser.parse_args()
    del parser

    # trim option string (they may contain spaces if read from config file)
    opts.l = opts.l.strip() if opts.l else 'none'
    opts.s = opts.s.strip().lower() if opts.s else 'stdout'

    # Set minimum logging level based on passed arguments
    logLevel = 'INFO'
    if opts.q: logLevel = None
    elif opts.d: logLevel = 'DEBUG'
    elif opts.w: logLevel = 'WARNING'

    # set log file if -l argument was passed
    if opts.l:
        logFile = None if opts.l.lower() == 'none' else opts.l
    # set console logging if -s argument was passed
    if opts.s:
        if opts.s == 'stderr': logStream = sys.stderr
        elif opts.s == 'stdout': logStream = sys.stdout
        else: logStream = None

    return logFile, logStream, logLevel

def main():

    global LOGGER, TPClient, STATES

    logFile, logStream, logLevel = logging_configuration(f'./{PLUGIN_ID}.log')

    # Configure the Client logging based on command line arguments.
    # Since the Client uses the 'root' logger by default,
    # this also sets all default logging options for any added child loggers, such as our g_log instance we created earlier.
    TPClient.setLogFile(logFile)
    TPClient.setLogStream(logStream)
    TPClient.setLogLevel(logLevel)

    JsonFile = 'Datarefs.json'
    successful, MSG, STATES = GetDatarefValuesFromJsonFile(JsonFile)

    if not successful:
        print("")
        print("NOT SUCCESSFUL")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #client_socket.connect((TPClient.TPHOST, TPClient.TPPORT))  # connect to the server
        client_socket.connect(('192.168.0.108', 12135))  # connect to the server
        options = [{"id":str(PLUGIN_ID+"_optionID1"),"title":"TITRE1"},{"id":str(PLUGIN_ID+"_optionID2"),"title":"TITRE2"}]
        outgoing = {
            "type": "showNotification",
            "notificationId": str(PLUGIN_ID+"_notificationID"),
            "title": str("Dataref input JSON file Error"),
            "msg": str(MSG),
            "options": options
        }
        print("")
        print(outgoing)
        print("")
        tp_msg_type = json.dumps(outgoing).encode()
        client_socket.sendall(tp_msg_type)
        #client_socket.close()  # Client sending close message. Close the connection
        #del TPClient
    else:
        LOGGER.info(f'Trying to connect to Touch Portal Apps')
        
        try:
            TPClient.connect()
        except KeyboardInterrupt:
            LOGGER.warning("Caught keyboard interrupt, exiting.")
            successful = False
        except ConnectionRefusedError:
            LOGGER.error(f'Cannot connect to Touch Portal, probably it is not running')
            successful = False
            return
        except Exception:
            # This will catch and report any critical exceptions in the base TPClient code,
            # _not_ exceptions in this plugin's event handlers (use onError(), above, for that).
            from traceback import format_exc
            LOGGER.error(f"Exception in TP Client:\n{format_exc()}")
            successful = False
            return
        finally:
            LOGGER.info(f'TP Client Disconnected')
            TPClient.disconnect()

        del TPClient

    #LOGGER.info(f'Return code = {successful}')
    #sys.exit(successful)

if __name__ == '__main__':
    main()