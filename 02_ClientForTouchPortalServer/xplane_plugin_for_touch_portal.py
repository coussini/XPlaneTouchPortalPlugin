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
import threading

__plugin_id__ = 'xplane_plugin_for_touch_portal'
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
        '''
        Class initialization. 
        '''
        self.version = '1.0'
        #self.json_file = 'TolissA320.json'
        self.json_keys_first_level = 'datarefs'
        self.json_keys = ['id', 'desc', 'group', 'type', 'value', 'dataref', 'comment']
        self.json_keys.sort()

        if __is_windows__: self.touch_portal_xplane_json_folder = os.getenv('APPDATA') + '\\TouchPortal\\misc\\xplane\\';
        if __is_linux__: self.touch_portal_xplane_json_folder = '\\TouchPortal\\misc\\xplane\\';
        if __is_macos__: self.touch_portal_xplane_json_folder = '\\Documents\\TouchPortal\\misc\\xplane\\';

        #self.json_file_location = self.touch_portal_xplane_json_folder+ self.json_file
        self.json_folder_location = self.touch_portal_xplane_json_folder
        self.json_file_name = 'default.json'

        # keep states from json file
        self.states = None

    def validate_keys_from_json_file(self, states):
        '''
        Validate the json file to ensure that all keys are listed 
        '''
        successful = True

        if not self.json_keys_first_level in states:
            __logger__.error(f'json first level key must be {self.json_keys_first_level}')
            successful = False
            raise Exception(f'json into the custom json')
        else:
            for x in states['datarefs']:
                keys = list(x.keys())
                keys.sort()
                if keys != self.json_keys:
                    __logger__.error(f'json file keys must be {self.json_keys} and not {keys}')
                    successful = False
                    raise Exception(f'json into the custom json')
                    break

        return successful

    def get_dataref_values_from_json_file(self):
        '''
        Read the json file into a dictionary
        '''
        successful = False
        states = None
        
        __logger__.info(f'Trying to load datarefs from: {self.json_folder_location}')

        try:
            json_file = self.json_folder_location + self.json_file_name
            print(json_file)
            file = open(json_file, 'r')
            states = json.load(file)
            file.close()
            __logger__.info(f'Datarefs successfully loaded from {json_file} !')
            successful = self.validate_keys_from_json_file(states)
        except FileNotFoundError:
            __logger__.error(f'File {json_file} does not exist')
        except ValueError as err:
            __logger__.error(f'Invalid JSON syntax in {json_file}')
            __logger__.error(f'{err}')
        except Exception as err:
            from traceback import format_exc
            __logger__.error(f'str({err})')
        finally:
            if successful:
                __logger__.info(f'The json file: {json_file} is valid !')

        return successful, states
        
class TouchPortalClient:
   
    def __init__(self):
        '''
        Class initialization. Create the Touch Portal API client instance 
        '''
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
        self.on_connect = TP_API.TYPES.onConnect
        self.on_action = TP_API.TYPES.onAction
        self.on_shutdown = TP_API.TYPES.onShutdown

    def on_connect_process(self, data, plugin_XP, client_TP, client_XP):
        '''
        Proceed the Touch Portal 'on connect' event 
        '''
        __logger__.info(f'Connected to Touch Portal Version {data.get("tpVersionString", "?")} plugin v {data.get("pluginVersion", "?")})')
        __logger__.info(f'==================')
        __logger__.info(f'SECTION on_connect')
        __logger__.info(f'==================')
        __logger__.info(f'{data}')

        client_TP.stateUpdate('xplane_plugin_for_touch_portal.state.touch_portal_ready', '1')

        '''
        successful, plugin_XP.states = plugin_XP.get_dataref_values_from_json_file()

        if successful:
            choices_list = []
            datarefs_list = []
            
            # ------------------------------------- 
            # example for one state for one dataref
            # ------------------------------------- 
            # "id": "AirbusFBW/ADIRUSwitchArray[0]",
            # "desc": "Adirs IR1",
            # "group": "OverHead",
            # "type": "int",
            # "value": "0",
            # "dataref": "AirbusFBW/ADIRUSwitchArray[0]",
            # "comment": "0 to 2 (0 = OFF, 1 = NAV, 2 = ATT)"
            # 
            
            # Process each dataref found in states python dictionnary . States data comes from the datarefs.json file
            for x in plugin_XP.states['datarefs']:
                descrition = x['group'] + ' - ' + x['desc']                     # Create a description within a group and desc
                client_TP.createState(x['id'],descrition,x['value'],x['group']) # Create a TP State for a dataref at runtime
                choices_list.append(x['desc'])                                  # Save dataref desc for choiceUpdate purpose
                datarefs_list.append(x['dataref'])                              # dataref will be use for comparaison in XPlaneClient class
            
            # Feed the valueChoices for each action: ref entry.tp file
            choices_list.sort() # sort options for ease of use in Touch Portal apps
            client_TP.choiceUpdate('xplane_plugin_for_touch_portal.dataref.set_states.name',choices_list)      # Update action option at runtime
            
            __logger__.info(f'Touch Portal Choices of States Id have been updated !')
            
            datarefs_list.sort()                                    # Sorted dataref will be use for comparaison in XPlaneClient class
            client_XP.datarefs_list = datarefs_list                 # Save sorted datarefs_list in XPlaneClient class 
            client_XP.nb_entries_datarefs_list = len(datarefs_list) # Keep datarefs occurence count

            # Start a thread to communicate with the x-plane server. This thread will finish when the Touch Portal Server are close
            client_XP.communicate_with_xplane_server()
        '''

    def on_action_process(self, data, plugin_XP, client_TP, client_XP):
        '''
        Proceed the Touch Portal 'on action' event 
        '''
        __logger__.info(f'=================')
        __logger__.info(f'SECTION on_action')
        __logger__.info(f'=================')
        __logger__.info(f'{data}')

        # dispatch Touch Portal Action Id
        match data.get('actionId'):
            case 'xplane_plugin_for_touch_portal.plugin.set_custom_dataref_json_file':
                # get the value from the action data (a string the user specified)
                plugin_XP.json_file_name = data.get('data')[0]['value']
                __logger__.info(f'json file = {plugin_XP.json_file_name}')
                  # We can also update our ExampleStates with the Action Value
                json_file_name_without_extension = os.path.splitext(plugin_XP.json_file_name)[0]
                client_TP.stateUpdate('xplane_plugin_for_touch_portal.state.custom_json_file_name', json_file_name_without_extension)
                successful, plugin_XP.states = plugin_XP.get_dataref_values_from_json_file()
        '''



            case 'xplane_plugin_for_touch_portal.dataref.set_states':
                for x in states['datarefs']:
                    if x['desc'] == data.get('data')[0]['value']:
                        # On attend que X-plane envoie la valeur
                        client_TP.stateUpdate(x['dataref'],data.get('data')[1]['value']) # update the value in Touch Portal State
                        __logger__.info(f"===================")
                        __logger__.info(f"State Update with : {x['dataref']} with value {data.get('data')[1]['value']}")
                        __logger__.info(f"===================")
                        outgoing_request = {}
                        outgoing_request['command'] = client_XP.request_update_from_touch_portal
                        outgoing_request['dataref'] = x['dataref']
                        outgoing_request['value'] = data.get('data')[1]['value']
                        outgoing_request_encode = json.dumps(outgoing_request).encode()
                        client_XP.outgoing_data.append(outgoing_request_encode) # request for update the value in XPlane Dataref
                        break
            case _:
                __logger__.info(f"There is no action like : {data.get('actionId')}") 

        '''

    def on_shutdown_process(self, data, client_TP):
        '''
        Proceed the Touch Portal 'on shutdown' event. When Touch Portal tries to close plugin 
        '''
        __logger__.info(f'===================')
        __logger__.info(f'SECTION on_shutdown')
        __logger__.info(f'===================')
        __logger__.info(f'{data}')

        #client_TP.disconnect()

    def treat_touch_portal_client(self, plugin_XP, client_XP):
        '''
        Proceed all Touch Portal events (Main process for Touch Portal)
        '''
        successful = False

        # Create an object concerning Touch Portal client
        client_TP = self.tp_api

        # This event handler will run once when the client connects to Touch Portal
        @client_TP.on(self.on_connect) 
        def onConnect(data):

            self.on_connect_process(data, plugin_XP, client_TP, client_XP)

        # Action handlers, called when user activates one of this plugin's actions in Touch Portal.
        @client_TP.on(self.on_action) 
        def onAction(data):

            self.on_action_process(data, plugin_XP, client_TP, client_XP)

        # Shutdown handler, called when Touch Portal wants to stop your plugin.
        @client_TP.on(self.on_shutdown) 
        def onShutdown(data):

            self.on_shutdown_process(data, client_TP)

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
        '''
        Class initialization. 
        '''
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

        # keep a sorted datarefs list that should be working on
        self.datarefs_list = []
        self.nb_entries_datarefs_list = 0

        # keep a dataref list that should be initialized
        self.datarefs_list_initialized = []
        self.nb_entries_datarefs_list_initialized = 0

        # store datarefs and their values from X-Plane in a dictionary for updating states in Touch Portal
        self.datarefs_and_values_dictionary = {}
        '''
        ============================================================================
        This is the chart for communication paquet between the client and the server
        ============================================================================
        '''
        # Packet that asks this server for the current dataref value in x-plane (initialization part)  
        self.request_dataref_value = 'request_dataref_value'
        self.request_dataref_value_paquet = ['command', 'dataref']
        # Packet for response for the previous request  
        self.response_dataref_value = 'response_dataref_value'
        self.response_dataref_value_paquet = ['command', 'dataref', 'message', 'value']

        # Packet that explains to this server that the initialization part is completed  
        self.request_initialization_done = 'request_initialization_done'
        self.request_initialization_done_paquet = ['command']
        # Packet for response for the previous request  
        self.response_initialization_done = 'response_initialization_done'
        self.response_initialization_done_paquet = ['command', 'message']

        # Packet that explains to this server that a dataref value has been updated in Touch Portal  
        self.request_update_from_touch_portal = 'request_update_from_touch_portal'
        self.request_update_from_touch_portal_paquet = ['command', 'dataref', 'value']
        # Packet for response for the previous request  
        self.response_update_from_touch_portal = 'response_update_from_touch_portal'
        self.response_update_from_touch_portal_paquet = ['command', 'message']

        # Packet that explains to the client that a dataref value has been updated in X-Plane  
        self.request_update_from_x_plane = 'request_update_from_x_plane'
        self.request_update_from_x_plane_paquet = ['command', 'dataref', 'value']
        # Packet for response for the previous request  
        self.response_update_from_x_plane = 'response_update_from_x_plane'
        self.response_update_from_x_plane_paquet = ['command', 'message']

    def connect(self):
        '''
        Establish a connection between this client and the X-Plane server. 
        '''
        successful = True

        try:    
            self.client_socket.connect((self.host,self.port))
        except socket.error:
            __logger__.error(f'X-Plane server is not running')            
            successful = False

        return successful

    def separate_data_received(self, ingoing_data):
        '''
        Process and separate data received from the server. 
        We can receive several commands in one data reception. 
        That's why we need to separate the commands and put them in ingoing_data_paquet
        '''
        new = ''
        ingoing_data_paquet = []

        for char in ingoing_data:
            if char == '{' and new != '':
                ingoing_data_paquet.append(new)
                new = ''
                new = new + char
            elif char == '{':
                new = new + char
            else:
                new = new + char

        ingoing_data_paquet.append(new)

        return ingoing_data_paquet

    def managing_received_data(self, ingoing_data):
        '''
        Process the received data packet from the x-plane server
        '''
        ingoing_data_paquet = self.separate_data_received(ingoing_data.decode())
        #__logger__.info(f'THIS IS THE INGOING_LIST') 
        #__logger__.info(f'{ingoing_data_paquet}') 

        for one_ingoing in ingoing_data_paquet: 
            __logger__.info(f'ingoing_data = {one_ingoing}') 
            try:
                one_ingoing_object = json.loads(one_ingoing)
                keys = list(one_ingoing_object.keys())
                keys.sort()

                # process a response for the current dataref value in x-plane (initialization part)
                # N.B: update the states in Touch Portal later from theses ingoing dataref values
                if one_ingoing_object['command'] == self.response_dataref_value and keys == self.response_dataref_value_paquet:
                    __logger__.info(f'message from the server: {one_ingoing_object["message"]}')
                    self.datarefs_list_initialized.append(one_ingoing_object['dataref'])
                    self.datarefs_and_values_dictionary.update({one_ingoing_object['dataref']:one_ingoing_object['value']})
                    #__logger__.info(f'append {one_ingoing_object["dataref"]}')
                # process a reponse in case the initialization part is completed  
                elif one_ingoing_object['command'] == self.response_initialization_done and keys == self.response_initialization_done_paquet:
                    __logger__.info(f'message from the server: {one_ingoing_object["message"]}')
                # process a reponse in case a dataref value has been updated in Touch Portal 
                elif one_ingoing_object['command'] == self.response_update_from_touch_portal and keys == self.response_update_from_touch_portal_paquet:
                    __logger__.info(f'message from the server: {one_ingoing_object["message"]}')
                # process a request from the server concerning because a dataref value has been updated in X-Plane    
                elif one_ingoing_object['command'] == self.request_update_from_x_plane and keys == self.request_update_from_x_plane_paquet:
                    dataref = one_ingoing_object['dataref']
                    value = one_ingoing_object['value']
                    self.client_TP.stateUpdate(dataref,value)
                    __logger__.info(f"===================")
                    __logger__.info(f"State Update with : {dataref} with value {value}")
                    __logger__.info(f"===================")
                    # send a response to the server
                    outgoing_request = {}
                    outgoing_request['command'] = self.response_update_from_x_plane
                    outgoing_request['message'] = 'states updated successfully'
                    outgoing_request_encode = json.dumps(outgoing_request).encode()
                    self.outgoing_data.append(outgoing_request_encode)
                # process a reponse in case a dataref value has been updated in Touch Portal 
                elif one_ingoing_object['command'] == self.response_update_from_x_plane and keys == self.response_update_from_x_plane:
                    __logger__.info(f'message from the server: {one_ingoing_object["message"]}')
                else:
                    __logger__.error(f'this response is not part of the communication chart between the client and the server')
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

    def service_connection(self, key, mask):
        '''
        managing sockets, selectors, received data and data to be sent.
        '''
        server_socket = key.fileobj
    
        if mask & selectors.EVENT_READ:
            try:
                # Should be ready to read
                ingoing_data = server_socket.recv(8192) 
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
    
    def treat_init_phase(self):
        '''
        Send each dataref that come from the json file to the x-plane server for receiving it's value
        '''
        if not self.init_phase_done.is_set():
            for dataref in self.datarefs_list:
                # prepare a request_dataref_value for the x-plane server
                outgoing_request = {}
                outgoing_request['command'] = self.request_dataref_value
                outgoing_request['dataref'] = dataref
                outgoing_request_encode = json.dumps(outgoing_request).encode()
                self.outgoing_data.append(outgoing_request_encode)

            # Tell the server that the initialization commands have been completed. 
            # The server will then start a thread to check every second if the user press a command on the X-plane side. 
            # Then, with this thread, the server will send the updated data to refresh the Touch Portal status and screen.  
            outgoing_request = {}
            outgoing_request['command'] = self.request_initialization_done
            outgoing_request_encode = json.dumps(outgoing_request).encode()
            self.outgoing_data.append(outgoing_request_encode)

        else:
            # make sure that every datarefs from the datarefs_list are initialized by the x-plane server
            self.nb_entries_datarefs_list_initialized = len(self.datarefs_list_initialized) 
            if self.nb_entries_datarefs_list_initialized == self.nb_entries_datarefs_list:
                self.datarefs_list_initialized.sort()
                if self.datarefs_list_initialized == self.datarefs_list:
                    # every dataref passed through initialization
                    __logger__.info(f'datarefs initialization processing was completed correctly !')
                    # update values that come from the x-plane server for each dataref
                    for dataref in self.datarefs_and_values_dictionary:
                        value = self.datarefs_and_values_dictionary[dataref]
                        one_id = dataref
                        one_value = value
                        __logger__.info(f'>>>>>>>>>>>>>>> {dataref} and {one_value} for stateUpdate')
                        self.client_TP.stateUpdate(one_id,one_value)
                    __logger__.info(f'state update completed !')
                    self.init_phase_running.clear()
                else:
                    __logger__.error(f'there are initialization problem')
                    __logger__.error(f'datarefs initialization processing was not completed correctly')
                    self.init_phase_running.clear()

        self.init_phase_done.set()

    def run(self):
        '''
        Handling selectors in communication with xplane server
        '''
        # The mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in self.client_selectors.select(timeout=0.1):
            if self.keep_running.is_set():
                self.service_connection(key, mask)
            if self.init_phase_running.is_set():
                self.treat_init_phase()

    def shutting_down(self):
        '''
        Processing the client closure procedure
        '''
        try:
            __logger__.info(f'=========== shutting_down X-Plane Client ===========')
            if self.client_selectors:
                self.client_selectors.unregister(self.client_socket)
                self.client_selectors.close()
            if self.client_socket: 
                self.client_socket.close()
        except:
            pass

    def thread_for_communication_with_xplane_server(self):
        '''
        Use a socket in non-blocking mode to establish a network connection with the x-plane server. 
        Use a selector to allows monitoring multiple sockets to check their status and see if 
        they are ready for operations such as reading or writing.

        This allowing multi connection   
        '''
        self.keep_running.set()
        self.init_phase_running.set()

        try:
            if self.connect():
                __logger__.info(f'preparing x-plane to running')
                __logger__.info(f'Connecting on {(self.host, self.port)}')
                # unblocking socket
                self.client_socket.setblocking(False)
                # register a file object for selection, monitoring it for I/O events
                self.client_selectors.register(self.client_socket, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)

                while self.keep_running.is_set():
                    self.run()
        except:
            self.keep_running.clear()
            __logger__.error('X-Plane server closed suddenly')
        finally:
            __logger__.info('ending X-Plane client thread')
            self.shutting_down()

    def communicate_with_xplane_server(self):
        '''
        Call a thread. This thread is used for network communication between the x-plane plugin and the x-plane server. 
        This thread will finish when the Touch Portal Server are close
        '''
        __logger__.info('starting X-Plane client thread')

        try:
            xp_thread = threading.Thread(target=self.thread_for_communication_with_xplane_server, args=(), daemon=True)
            xp_thread.start()
        except:
            self.keep_running.clear()
            __logger__.error('something wrong with thread X-Plane')

def main():
    
    # Create a XPlane Plugin instance.
    plugin_XP = XPlanePlugin()

    # Create a Touch Portal client instance.
    client_TP = TouchPortalClient()

    # Create a XPlane client instance. Keep the client_TP for any status update
    client_XP = XPlaneClient(client_TP)

    # extract all datarefs from the JSON file.
    #successful, plugin_XP.states = plugin_XP.get_dataref_values_from_json_file()

    #if successful:
    successful = client_TP.treat_touch_portal_client(plugin_XP, client_XP)

    __logger__.info(f'Return code = {successful}')
    sys.exit(successful)

if __name__ == '__main__':
    main()
