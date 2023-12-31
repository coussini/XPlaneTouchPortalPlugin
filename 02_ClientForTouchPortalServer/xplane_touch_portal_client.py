###
## les ingoing dans init phase sera
## self.input_json_keys = ['command', 'dataref', 'value']
## le outgoing sera self.input_json_keys = ['command', 'dataref']
##
## ajuster le programme pour cela et regarder les listes et les noms
## qu'on utilise pour comparer les listes (peut-on simplifier ?)
##
###


import sys 
import os
import platform
import argparse # argparse.ArgumentParser
import TouchPortalAPI as TP_API
import TouchPortalAPI.logger as TP_API_LOG # TouchPortalAPI.logger.Logger
import selectors
import socket
import json
import time
import random # temporary
import threading

__plugin_id__ = 'xplane_touch_portal_client'
__log_file__ = f'./{__plugin_id__}.log'
        
# Get OS where python is running.
__is_windows__ = True if (platform.system() == 'Windows') else False
__is_linux__ = True if (platform.system() == 'Linux') else False
__is_macos__ = True if (platform.system() == 'Darwin') else False

# Create the (optional) global __logger__, an instance of `TouchPortalAPI::Logger` helper class.
try:
    __logger__ = TP_API_LOG.Logger(name = __plugin_id__)
except Exception as e:
    sys.exit(f'Could not create a Touch Portal log file. Error was:\n{repr(e)}')

class XPlanePlugin:
    
    def __init__(self):

        self.version = '1.0'
        self.json_file = 'datarefs.json'
        self.json_keys_first_level = 'datarefs'
        self.json_keys = ['id', 'desc', 'group', 'type', 'value', 'dataref', 'comment']
        self.json_keys.sort()

        if __is_windows__: self.touch_portal_data_folder = os.getenv('APPDATA') + '\\TouchPortal\\plugins\\';
        if __is_linux__: self.touch_portal_data_folder = '\\TouchPortal\\plugins\\';
        if __is_macos__: self.touch_portal_data_folder = '\\Documents\\TouchPortal\\plugins\\';

        self.json_file_location = self.touch_portal_data_folder+ self.json_file

        # keep states from json file
        self.states = None

    def validate_keys_from_json_file(self, states):
        
        successful = True

        if not self.json_keys_first_level in states:
            __logger__.error(f'json first level key must be {self.json_keys_first_level}')
            successful = False
        else:
            for x in states['datarefs']:
                keys = list(x.keys())
                keys.sort()
                if keys != self.json_keys:
                    __logger__.error(f'json file keys must be {self.json_keys} and not {keys}')
                    successful = False
                    break

        return successful

    def get_dataref_values_from_json_file(self):
        
        successful = False
        states = None
        
        __logger__.info(f'Trying to load datarefs from: {self.json_file_location}')

        try:
            file = open(self.json_file, 'r')
            states = json.load(file)
            file.close()
            __logger__.info(f'Datarefs successfully loaded from {self.json_file} !')
            successful = self.validate_keys_from_json_file(states)
        except FileNotFoundError:
            __logger__.error(f'File {self.json_file} does not exist')
        except ValueError as err:
            __logger__.error(f'Invalid JSON syntax in {self.json_file}')
            __logger__.error(f'{err}')
        except Exception as err:
            from traceback import format_exc
            __logger__.error(f'str({err})')
        finally:
            if successful:
                __logger__.info(f'The json file: {self.json_file_location} is valid !')

        return successful, states
        
class TouchPortalClient:
   
    def __init__(self):
        
        # Create the Touch Portal API client instance.
        try:
            self.tp_api = TP_API.Client(
                pluginId = __plugin_id__,           # required ID of this plugin
                sleepPeriod = 0.05,                 # allow more time than default for other processes
                autoClose = True,                   # automatically disconnect when TP sends 'closePlugin' message
                checkPluginId = True,               # validate destination of messages sent to this plugin
                maxWorkers = 4,                     # run up to 4 event handler threads
                updateStatesOnBroadcast = False,    # do not spam TP with state updates on every page change
                logFileName = __log_file__          # For log messages. Paths are relative to current working directory     
            )
        except Exception as e:
            sys.exit(f'Could not create a Touch Portal API client instance, exiting. Error was:\n{repr(e)}')

        # Event for the Touch Portal API
        self.on_info = TP_API.TYPES.onConnect
        self.on_action = TP_API.TYPES.onAction
        self.on_close_plugin = TP_API.TYPES.onShutdown

    def treat_touch_portal_client(self, states, client_XP):

        successful = False

        # Create an object concerning Touch Portal client
        client_TP = self.tp_api

        # This event handler will run once when the client connects to Touch Portal
        @client_TP.on(self.on_info) 
        def onStart(data):

            __logger__.info(f'Connected to Touch Portal Version {data.get("tpVersionString", "?")} plugin v {data.get("pluginVersion", "?")})')
            __logger__.info(f'=================')
            __logger__.info(f'SECTION on_info')
            __logger__.info(f'=================')
            __logger__.info(f'{data}')
            
            choices_list = []
            datarefs_list = []
            
            for x in states['datarefs']:
                descrition = x['group'] + ' - ' + x['desc']
                client_TP.createState(x['id'],descrition,x['value'],x['group']) # create a TP State default value at runtime
                choices_list.append(x['desc'])
                datarefs_list.append(x['dataref'])
            
            choices_list.sort() # sort options for ease of use
            client_TP.choiceUpdate('xplane_touch_portal_client.dataref.toggle_two_states.choice',choices_list) # update action option at runtime
            client_TP.choiceUpdate('xplane_touch_portal_client.dataref.set_two_states.name',choices_list) # update action option at runtime
            
            __logger__.info(f'Touch Portal Choices of States Id have been updated !')
            
            # start a thread to treat xplane client. The thread will finish when the Touch Portal Server are close
            datarefs_list.sort() # sort datarefs for future comparaison
            client_XP.datarefs_list = datarefs_list
            client_XP.nb_entries_datarefs_list = len(datarefs_list)
            client_XP.keep_running.set()
            client_XP.treat_xplane_client()

        # Action handlers, called when user activates one of this plugin's actions in Touch Portal.
        @client_TP.on(self.on_action) 
        def onAction(data):

            __logger__.info(f'=================')
            __logger__.info(f'SECTION on_action')
            __logger__.info(f'=================')
            __logger__.info(f'{data}')

        # Shutdown handler, called when Touch Portal wants to stop your plugin.
        @client_TP.on(self.on_close_plugin) 
        def onShutdown(data):

            __logger__.info(f'=======================')
            __logger__.info(f'SECTION on_close_plugin')
            __logger__.info(f'=======================')
            __logger__.info(f'{data}')
            client_TP.disconnect()

        __logger__.info(f'Trying to connect to Touch Portal Apps')
        
        try:
            client_TP.connect()
        except KeyboardInterrupt:
            __logger__.warning('Caught keyboard interrupt, exiting.')
        except ConnectionRefusedError:
            __logger__.error(f'Cannot connect to Touch Portal, probably it is not running')
        except Exception:
            # This will catch and report any critical exceptions in the base client_TP code,
            # _not_ exceptions in this plugin's event handlers (use onError(), above, for that).
            from traceback import format_exc
            __logger__.error(f'Exception in TP Client:\n{format_exc()}')
            client_XP.keep_running.clear()
        else:
            __logger__.info(f'TP Client Disconnected')
            successful = True
        finally:
            client_XP.keep_running.clear()
            client_TP.disconnect()

        del client_XP
        del client_TP

        return successful

class XPlaneClient:
    
    def __init__(self, client_TP):

        self.client_TP = client_TP.tp_api # keep the client tp for the status update
        self.client_selectors = selectors.DefaultSelector()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = 65432
        
        self.keep_running = threading.Event()
        self.connected = threading.Event()
        self.init_phase_done = threading.Event()
        self.init_phase_running = threading.Event()
        
        self.outgoing_data = []
        
        self.input_json_keys = ['command', 'dataref']

        # attention temporaire
        self.input_json_keys = ['command', 'dataref', 'value']
        self.update_json_keys = ['command', 'dataref', 'value']
        # pas necessaire
        #self.input_json_keys.sort()
        #self.update_json_keys.sort()

        # keep a sorted datarefs list that should be working on
        self.datarefs_list = []
        self.nb_entries_datarefs_list = 0

        # keep a dataref list that should be initialized
        self.datarefs_list_initialized = []
        self.nb_entries_datarefs_list_initialized = 0

        # store datarefs and their values from X-Plane in a dictionary for updating states in Touch Portal
        self.datarefs_and_values_dictionary = {}

    def connect(self):
        
        successful = True

        try:    
            self.client_socket.connect((self.host,self.port))
        except socket.error:
            __logger__.error(f'X-Plane server is not running')            
            successful = False

        return successful

    def treat_xplane_client(self):

        __logger__.info("starting X-Plane client thread")
        self.keep_running.set()
        self.init_phase_running.set()

        try:
            xp_thread = threading.Thread(target=self.thread_function, args=(), daemon=True)
            xp_thread.start()
        except:
            self.keep_running.clear()
            __logger__.error('something wrong with thread X-Plane')

    def thread_function(self):

        try:
            if self.connect():
                self.connected.set()
                self.preparing_running()
                while self.keep_running.is_set():
                    self.run()
        except:
            self.keep_running.clear()
            __logger__.error('X-Plane server closed suddenly')
        finally:
            __logger__.info('ending X-Plane client thread')
            self.shutting_down()

    def preparing_running(self):

        __logger__.info(f'preparing x-plane to running')
        __logger__.info(f'Connecting on {(self.host, self.port)}')

        # unblocking socket
        self.client_socket.setblocking(False)
        # register a file object for selection, monitoring it for I/O events
        self.client_selectors.register(self.client_socket, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)

    def run(self):

        # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in self.client_selectors.select(timeout=0.1):
            if self.keep_running.is_set():
                self.service_connection(key, mask)
            if self.init_phase_running.is_set():
                self.treat_init_phase()
    
    def treat_init_phase(self):
            
        # send each dataref that come from json file to the x-plane server 
        # for receiving it's value
        if not self.init_phase_done.is_set():
            for dataref in self.datarefs_list:
                # prepare a init packet for the x-plane server
                
                # this is temporary for value. the value must not be there for init

                a_dataref = {}
                a_dataref["command"] = "init"
                a_dataref["dataref"] = dataref
                a_dataref["value"] = str(random.randint(0,3))
                message = json.dumps(a_dataref).encode()
                self.outgoing_data.append(message)
        else:
            # make sure that every datarefs from the datarefs_list are initialized by the x-plane server
            self.nb_entries_datarefs_list_initialized = len(self.datarefs_list_initialized) 
            if self.nb_entries_datarefs_list_initialized == self.nb_entries_datarefs_list:
                self.datarefs_list_initialized.sort()
                if self.datarefs_list_initialized == self.datarefs_list:
                    # every dataref passed through initialization
                    __logger__.info(f'datarefs initialization processing was completed correctly !')
                    #######
                    # update value that come from the x-plane server for each dataref
                    #

                    #
                    #for dataref in self.datarefs_list:
                    
                    
                    for dataref in self.datarefs_and_values_dictionary:
                        
                        value = self.datarefs_and_values_dictionary[dataref]
                        ##### normally come from x-plane Dataref
                        one_id = dataref
                        one_value = value
                        __logger__.info(f'>>>>>>>>>>>>>>> {dataref} and {value} for stateUpdate')
                        ##### 

                        self.client_TP.stateUpdate(one_id,one_value)
                    
                    __logger__.info(f'state update completed !')
                    self.init_phase_running.clear()
                else:
                    __logger__.error(f'there are initialization problem')
                    __logger__.error(f'datarefs initialization processing was not completed correctly')
                    self.init_phase_running.clear()

        self.init_phase_done.set()

    def shutting_down(self):

        try:
            __logger__.info(f'=========== shutting_down X-Plane Client ===========')
            if self.client_selectors:
                self.client_selectors.unregister(self.client_socket)
                self.client_selectors.close()
            if self.client_socket: 
                self.client_socket.close()
        except:
            pass

    def service_connection(self, key, mask):

        server_socket = key.fileobj
    
        if mask & selectors.EVENT_READ:
            try:
                # Should be ready to read
                ingoing_data = server_socket.recv(4096) 
            except BlockingIOError:
                pass  # Resource temporarily unavailable (errno EWOULDBLOCK)
            except:
                # No connection
                #raise Exception('X-Plane server closed suddenly')
                raise
            else:
                if ingoing_data:
                    self.managing_received_data(ingoing_data)
                else:
                    # No connection
                    #raise Exception('X-Plane server closed suddenly')
                    raise

        if mask & selectors.EVENT_WRITE:
            if self.outgoing_data and self.keep_running.is_set():
                next_msg = self.outgoing_data.pop(0)
                __logger__.info(f'outgoing_data = {next_msg}')
                __logger__.info(f'')
                server_socket.sendall(next_msg)

    # separate the ingoing packet on store it in ingoing_list    
    def treat_ingoing_string(self, ingoing_str):

        new = ''
        ingoing_list = []

        for char in ingoing_str:
            if char == '{' and new != '':
                ingoing_list.append(new)
                new = ''
                new = new + char
            elif char == '{':
                new = new + char
            else:
                new = new + char

        ingoing_list.append(new)

        return ingoing_list

    def managing_received_data(self, ingoing_data):

        ingoing_list = self.treat_ingoing_string(ingoing_data.decode())
        __logger__.info(f'THIS IS THE INGOING_LIST') 
        __logger__.info(f'{ingoing_list}') 

        for one_ingoing in ingoing_list: 
            __logger__.info(f'ingoing_data = {one_ingoing}') 
            try:
                one_ingoing_object = json.loads(one_ingoing)
                keys = list(one_ingoing_object.keys())
                keys.sort()
                # treat each dataref for the initialization phase
                if keys == self.input_json_keys:
                    self.datarefs_list_initialized.append(one_ingoing_object['dataref'])
                    self.datarefs_and_values_dictionary.update({one_ingoing_object['dataref']:one_ingoing_object['value']})
                    __logger__.info(f'append {one_ingoing_object["dataref"]}')
                elif keys == self.update_json_keys:
                    __logger__.info(f'this json file keys is ok: {self.update_json_keys}')
                else:
                    __logger__.error(f'json file keys must be:')
                    __logger__.error(f'{self.input_json_keys}')
                    __logger__.error(f'{self.update_json_keys}')
                    __logger__.error(f'the following json file keys has been rejected:')
                    __logger__.error(f'{keys}')
                    self.keep_running.clear()
                    break
            except Exception:
                # This will catch and report any critical exceptions in the base client_TP code,
                # _not_ exceptions in this plugin's event handlers (use onError(), above, for that).
                from traceback import format_exc
                __logger__.error(f'an error occurred when trying to make a json object') 
                __logger__.error(f'the receiving string is not a json') 
                __logger__.error(f'xception in XP Client:\n{format_exc()}')
                self.keep_running.clear()
                break
            __logger__.info(f'') 

def main():
    
    # Create a XPlane Plugin instance.
    xplane_plugin = XPlanePlugin()

    # Create a Touch Portal client instance.
    client_TP = TouchPortalClient()

    # Create a XPlane client instance. Keep the client_TP for any status update
    client_XP = XPlaneClient(client_TP)

    # extract all datarefs from the JSON file.
    successful, xplane_plugin.states = xplane_plugin.get_dataref_values_from_json_file()

    if successful:
        successful = client_TP.treat_touch_portal_client(xplane_plugin.states, client_XP)

    __logger__.info(f'Return code = {successful}')
    sys.exit(successful)

if __name__ == '__main__':
    main()
