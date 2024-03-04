import sys 
import os
import platform
import argparse # argparse.ArgumentParser X-Plane server is not running
import TouchPortalAPI as TP_API
import TouchPortalAPI.logger as TP_API_LOG # TouchPortalAPI.logger.Logger
import selectors
import socket
import json
import time
import threading
from traceback import format_exc # to catch more information concerning exception error
import queue # this is only to pass exception from the secondary thread to the main thread

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

    class CustomErrorPlugin(Exception): 

        def __init__(self, message):
            '''
            Initialization of the exception class for handling plugin errors
            '''
            super().__init__(message)

    class CustomErrorJson(Exception):

        def __init__(self, message):
            '''
            Initialization of the exception class for handling the custom Json errors
            '''
            super().__init__(message)

    class CustomErrorXPlane(Exception):

        def __init__(self, message):
            '''
            Initialization of the exception class for handling the communication between the X-Plane client and the X-Plane Server
            '''
            super().__init__(message)

    def __init__(self):
        '''
        Class initialization. 
        '''

        '''
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        | Concerning the "custom JSON" that contains dataref informations |
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        '''
        self.json_keys_first_level = 'datarefs'
        self.json_keys = ['id', 'desc', 'group', 'type', 'value', 'dataref', 'comment']
        self.json_keys.sort()

        if __is_windows__: self.touch_portal_xplane_json_folder = os.getenv('APPDATA') + '\\TouchPortal\\misc\\xplane\\';
        if __is_linux__: self.touch_portal_xplane_json_folder = '\\TouchPortal\\misc\\xplane\\';
        if __is_macos__: self.touch_portal_xplane_json_folder = '\\Documents\\TouchPortal\\misc\\xplane\\';

        self.json_folder_location = self.touch_portal_xplane_json_folder
        self.json_file_name = 'default.json'         # Default Custom json file

        # keep states from json file
        self.states = None

        '''
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        | Concerning the Touch Portal API and Touch Portal Client |
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        '''
        try:
            self.tp_api = TP_API.Client(            # Create the Touch Portal API client instance
                pluginId = __plugin_id__,           # Required ID of this plugin
                sleepPeriod = 0.05,                 # Allow more time than default for other processes
                autoClose = True,                   # Automatically disconnect when TP sends 'closePlugin' message
                checkPluginId = True,               # Validate destination of messages sent to this plugin
                maxWorkers = 4,                     # Run up to 4 event handler threads
                updateStatesOnBroadcast = False,    # Do not spam TP with state updates on every page change
                logFileName = __log_file__          # For log messages. Paths are relative to current working directory     
            )
        except Exception as e:
            sys.exit(f'Could not create a Touch Portal API client instance, exiting. Error was:\n{repr(e)}')

        # Event for the Touch Portal API
        self.on_connect = TP_API.TYPES.onConnect
        self.on_action = TP_API.TYPES.onAction
        self.on_shutdown = TP_API.TYPES.onShutdown

        '''
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        | Concerning the X-Plane client for the X-Plane server |
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        '''
        self.exception_error_queue = queue.Queue() # keep the exception from the x-plane thread
        self.client_selectors = selectors.DefaultSelector()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = 65432
        
        self.keep_running = threading.Event()
        self.connected = threading.Event()
        self.xplane_client_thread = None # For the instance of threading.Thread class

        self.init_phase_done = threading.Event()
        self.init_phase_running = threading.Event()

        self.outgoing_data = []

        # Keep a sorted datarefs list that should be working on
        self.datarefs_list = []
        self.nb_entries_datarefs_list = 0

        # keep a dataref list that should be initialized
        self.datarefs_list_initialized = []
        self.nb_entries_datarefs_list_initialized = 0

        # Store datarefs and their values from X-Plane in a dictionary for updating states in Touch Portal
        self.datarefs_and_values_dictionary = {}
        '''
        ============================================================================================
        This is the chart for communication paquet between the X-Plane client and the X-Plane server
        ============================================================================================
        '''
        # Packet that asks this server for the current dataref value in X-Plane (initialization part)  
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

    def custom_json_validate_keys(self):
        '''
        Validate the json file to ensure that all keys are listed 
        '''
        successful = True

        if not self.json_keys_first_level in self.states:
            raise self.CustomErrorJson(f'The first-level-key must be\n{self.json_keys_first_level}')
            successful = False
        else:
            for x in self.states['datarefs']:
                keys = list(x.keys())
                keys.sort()
                if keys != self.json_keys:
                    raise self.CustomErrorJson(f'The second-level-key must be\n{self.json_keys}\nAnd not {keys}\nSecond-level keys with Error: {x}')
                    successful = False
                    break

        return successful

    def custom_json_get_dataref_and_set_state(self):
        '''
        Read the json file into a dictionary and set states for Touch Portal
        '''
        successful = False
        
        __logger__.info(f'Trying to load datarefs from: {self.json_folder_location}')

        try:
            json_file = self.json_folder_location + self.json_file_name
            print(json_file)
            file = open(json_file, 'r')
            self.states = json.load(file)
            file.close()
            __logger__.info(f'Datarefs successfully loaded from {json_file} !')
            successful = self.custom_json_validate_keys()
        except self.CustomErrorJson:
            raise # Bubbling the exception
        except FileNotFoundError:
            raise self.CustomErrorJson(f'{json_file} does not exist')
        except ValueError as e:
            raise self.CustomErrorJson(f'Syntax error in {json_file}\nMessage: {e}')
        except Exception as e:
            error_report = format_exc()
            raise self.CustomErrorJson(f'Other Error for {json_file}\nMessage: {e}\nError report: {error_report}' )
        finally:
            if successful:
                __logger__.info(f'The json file: {json_file} is valid !')

        return successful

    def touch_portal_client_on_action_set_custom_dataref_json_file(self, data):
        '''
        Set the custom dataref json file name for the Touch Portal page purpose 
        Get the dataref info from this custom dataref json file and put it in states 
        '''
        successful = False
        
        self.json_file_name = data.get('data')[0]['value'].strip()
        __logger__.info(f'Custom json file = {self.json_file_name}')

        if self.json_file_name == '':
            raise self.CustomErrorJson(f'The custom dataref field in the touch portal page must not be empty\nSee inside the "Not Loaded JSON" button')
        else:
            # Get the json file name without extension to display in page
            json_file_name_without_extension = os.path.splitext(self.json_file_name)[0]
            # Set states from custom json files that contains dataref info
            successful = self.custom_json_get_dataref_and_set_state()
        
            if successful:
                self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.custom_json_file_name', json_file_name_without_extension)
                self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.main_status', '4') # Json loaded
    
                try:
                    choices_list = []
                    datarefs_list = []
                    
                    # ------------------------------------- 
                    # example for one state for one dataref
                    # ------------------------------------- 
                    # "id": "AirbusFBW/ADIRUSwitchArray[0]",
                    # "desc": "Adirs IR1",
                    # "group": "OverHead",
                    # "dataref": "AirbusFBW/ADIRUSwitchArray[0]",
                    # "comment": "0 to 2 (0 = OFF, 1 = NAV, 2 = ATT)"
                    # 
                    
                    # Process each dataref found in states python dictionnary . States data comes from the datarefs.json file
                    for x in self.states['datarefs']:
                        description = x['group'] + ' - ' + x['desc']                      # Create a description within a group and desc
                        self.tp_api.createState(x['id'],description,'0',x['group'])       # Create a TP State for a dataref at runtime
                        choices_list.append(x['desc'])                                    # Save dataref desc for choiceUpdate purpose
                        self.datarefs_list.append(x['dataref'])                           # dataref will be use for comparaison
                    
                    # Feed the valueChoices for each action: ref entry.tp file
                    choices_list.sort() # Sort options for ease of use in Touch Portal apps
                    
                    self.tp_api.choiceUpdate('xplane_plugin_for_touch_portal.dataref.set_states.name',choices_list) # Update action option at runtime
                    
                    __logger__.info(f'Touch Portal Choices of States Id have been updated !')
                    
                    self.datarefs_list.sort() # Sorted dataref will be use for comparaison
                    self.nb_entries_datarefs_list = len(self.datarefs_list) # Keep datarefs occurence count

                except Exception as e:
                    error_report = format_exc()
                    raise self.CustomErrorPlugin(f'Other Error for {__plugin_id__}\nMessage: {e}\nError report: {error_report}' )
                

    def touch_portal_client_on_action_start_communication_with_xplane_server(self):
        '''
        Start the communication with the X-Plane server 
        '''
        self.xplane_client_communicate_with_xplane_server()

    def touch_portal_client_on_action_stop_communication_with_xplane_server(self):
        '''
        Stop the communication with the X-Plane server 
        '''
        self.xplane_client_stop_communicate_with_xplane_server()
        
        self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.main_status', '4') # Json loaded
        __logger__.info("touch_portal_client_on_action_stop_communication_with_xplane_server")

    def touch_portal_client_on_action_set_states(self, data):
        '''
        Set states value and send it to X-Plane server 
        '''
        try:
            for x in self.states['datarefs']:
                if x['desc'] == data.get('data')[0]['value']:
                    
                    self.tp_api.stateUpdate(x['dataref'],data.get('data')[1]['value']) # Update the value in Touch Portal State
                    
                    __logger__.info(f"===================")
                    __logger__.info(f"State Update with : {x['dataref']} with value {data.get('data')[1]['value']}")
                    __logger__.info(f"===================")
                    
                    outgoing_request = {}
                    outgoing_request['command'] = self.request_update_from_touch_portal
                    outgoing_request['dataref'] = x['dataref']
                    outgoing_request['value'] = data.get('data')[1]['value']
                    outgoing_request_encode = json.dumps(outgoing_request).encode()
                    
                    self.outgoing_data.append(outgoing_request_encode) # Request for update the value in X-Plane dataref
                    
                    break

        except Exception as e:
            error_report = format_exc()
            raise self.CustomErrorPlugin(f'Other Error for {__plugin_id__}\nMessage: {e}\nError report: {error_report}' )

    def touch_portal_client_on_connect_process(self, data):
        '''
        Proceed the Touch Portal 'on connect' event 
        '''
        __logger__.info(f'Connected to Touch Portal Version {data.get("tpVersionString", "?")} plugin v {data.get("pluginVersion", "?")})')
        __logger__.info(f'=======================')
        __logger__.info(f'Touch Portal on_connect')
        __logger__.info(f'=======================')
        __logger__.info(f'{data}')

        self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.main_status', '2')

    def touch_portal_client_on_action_process(self, data):
        '''
        Proceed the Touch Portal 'on action' event 
        '''
        __logger__.info(f'======================')
        __logger__.info(f'Touch Portal on_action')
        __logger__.info(f'======================')
        __logger__.info(f'{data}')

        # Dispatch Touch Portal Action Id (see inside entry.tp for that)
        match data.get('actionId'):
            case 'xplane_plugin_for_touch_portal.plugin.set_main_status_to':

                self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.main_status', data.get('data')[0]['value'])

            case 'xplane_plugin_for_touch_portal.plugin.set_custom_dataref_json_file':

                try:
                    self.touch_portal_client_on_action_set_custom_dataref_json_file(data)
                    '''
                    Exception for the plugin
                    '''
                except self.CustomErrorPlugin as e:
                    __logger__.error(f'ERROR -> XPLANE PLUGIN FOR TOUCH PORTAL')
                    error_messages = str(e).split('\n')
                    for error_message in error_messages:
                        __logger__.error(f'ERROR -> {error_message}')
                    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.main_status', '1') # Customized Json error
                    '''
                    Main exception for the Customized Json
                    '''
                except self.CustomErrorJson as e:
                    __logger__.error(f'ERROR -> CUSTOMIZED JSON')
                    error_messages = str(e).split('\n')
                    for error_message in error_messages:
                        __logger__.error(f'ERROR -> {error_message}')
                    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.main_status', '3') # Customized Json error

            case 'xplane_plugin_for_touch_portal.plugin.start_communication_with_server':

                try:
                    start_communication_with_server = data.get('data')[0]['value']
                    __logger__.info(f'Start = {start_communication_with_server}')
                    if start_communication_with_server == 'Yes':
                        self.touch_portal_client_on_action_start_communication_with_xplane_server()
                    else:
                        self.touch_portal_client_on_action_stop_communication_with_xplane_server()
                    '''
                    Exception arround the X-Plane server
                    '''
                except self.CustomErrorXPlane as e:
                    __logger__.error(f'ERROR -> XPLANE SERVER COMMUNICATION')
                    error_messages = str(e).split('\n')
                    for error_message in error_messages:
                        __logger__.error(f'ERROR -> {error_message}')
                    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.main_status', '5') # Customized Json error

            case 'xplane_plugin_for_touch_portal.dataref.set_states':

                try:
                    self.touch_portal_client_on_action_set_states(data)
                    '''
                    Exception for the plugin
                    '''
                except self.CustomErrorPlugin as e:
                    __logger__.error(f'ERROR -> XPLANE PLUGIN FOR TOUCH PORTAL')
                    error_messages = str(e).split('\n')
                    for error_message in error_messages:
                        __logger__.error(f'ERROR -> {error_message}')
                    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.main_status', '1') # Customized Json error

            case _:
                '''
                Exception for the plugin
                '''
                error_report = format_exc()
                e = f"There is no action like the following\n{data.get('actionId')}\nMessage report:{error_report}"
                __logger__.error(f'ERROR -> XPLANE PLUGIN FOR TOUCH PORTAL')
                error_messages = str(e).split('\n')
                for error_message in error_messages:
                    __logger__.error(f'ERROR -> {error_message}')
                self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.main_status', '1') # Customized Json error

    def touch_portal_client_on_shutdown_process(self, data):
        '''
        Proceed the Touch Portal 'on shutdown' event. When Touch Portal tries to close plugin 
        '''
        __logger__.info(f'========================')
        __logger__.info(f'Touch Portal on_shutdown')
        __logger__.info(f'========================')
        __logger__.info(f'{data}')

    def touch_portal_client_process(self):
        '''
        Proceed all Touch Portal events (Main process for Touch Portal)
        '''
        successful = False

        # Create an object concerning the Touch Portal API client for the following decorator @
        tp_api = self.tp_api

        # This event handler will run once when the client connects to Touch Portal
        @tp_api.on(self.on_connect) 
        def onConnect(data):

            self.touch_portal_client_on_connect_process(data)

        # Action handlers, called when user activates one of this plugin's actions in Touch Portal.
        @tp_api.on(self.on_action) 
        def onAction(data):

            self.touch_portal_client_on_action_process(data)

        # Shutdown handler, called when Touch Portal wants to stop your plugin.
        @tp_api.on(self.on_shutdown) 
        def onShutdown(data):

            self.touch_portal_client_on_shutdown_process(data)

        __logger__.info(f'Trying to connect to Touch Portal Apps')
        
        try:
            self.tp_api.connect()
        except KeyboardInterrupt:
            __logger__.warning('Caught keyboard interrupt, exiting.')
        except ConnectionRefusedError:
            __logger__.error(f'ERROR -> TOUCH PORTAL\nCannot connect to Touch Portal\nProbably it is not running')
        except Exception as e:
            error_report = format_exc()
            __logger__.error(f'ERROR -> TOUCH PORTAL\nMessage: {e}\nError report: {error_report}' )
            self.keep_running.clear()
        else:
            __logger__.info(f'TP Client Disconnected')
            successful = True
        finally:
            self.keep_running.clear()
            self.tp_api.disconnect()

        return successful

    def xplane_client_connect(self):
        '''
        Establish a connection between this client and the X-Plane server. 
        '''
        successful = True

        try:    
            self.client_socket.connect((self.host,self.port))
        except socket.error as e:
            error_report = format_exc()
            self.exception_error_queue.put(f'X-Plane server is not running \nMessage: {e}\nError report: {error_report}')            
            self.keep_running.clear()
            successful = False

        return successful

    def xplane_client_separate_data_received(self, ingoing_data):
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

    def xplane_client_managing_received_data(self, ingoing_data):
        '''
        Process the received data packet from the X-Plane server
        '''
        ingoing_data_paquet = self.xplane_client_separate_data_received(ingoing_data.decode())

        for one_ingoing in ingoing_data_paquet: 
            __logger__.info(f'Ingoing_data = {one_ingoing}') 
            try:
                one_ingoing_object = json.loads(one_ingoing)
                keys = list(one_ingoing_object.keys())
                keys.sort()

                # Process a response for the current dataref value in X-Plane (initialization part)
                # N.B: update the states in Touch Portal later from theses ingoing dataref values
                if one_ingoing_object['command'] == self.response_dataref_value and keys == self.response_dataref_value_paquet:

                    __logger__.info(f'Message from the server: {one_ingoing_object["message"]}')
                    self.datarefs_list_initialized.append(one_ingoing_object['dataref'])
                    self.datarefs_and_values_dictionary.update({one_ingoing_object['dataref']:one_ingoing_object['value']})

                # Process a reponse in case the initialization part is completed  
                elif one_ingoing_object['command'] == self.response_initialization_done and keys == self.response_initialization_done_paquet:

                    __logger__.info(f'Message from the server: {one_ingoing_object["message"]}')

                # Process a reponse in case a dataref value has been updated in Touch Portal 
                elif one_ingoing_object['command'] == self.response_update_from_touch_portal and keys == self.response_update_from_touch_portal_paquet:

                    __logger__.info(f'Message from the server: {one_ingoing_object["message"]}')

                # Process a request from the server concerning because a dataref value has been updated in X-Plane    
                elif one_ingoing_object['command'] == self.request_update_from_x_plane and keys == self.request_update_from_x_plane_paquet:

                    dataref = one_ingoing_object['dataref']
                    value = one_ingoing_object['value']
                    self.tp_api.stateUpdate(dataref,value)
                    __logger__.info(f"===================")
                    __logger__.info(f"State Update with : {dataref} with value {value}")
                    __logger__.info(f"===================")
                    # Send a response to the server
                    outgoing_request = {}
                    outgoing_request['command'] = self.response_update_from_x_plane
                    outgoing_request['message'] = 'States updated successfully'
                    outgoing_request_encode = json.dumps(outgoing_request).encode()
                    self.outgoing_data.append(outgoing_request_encode)

                # Process a reponse in case a dataref value has been updated in Touch Portal 
                elif one_ingoing_object['command'] == self.response_update_from_x_plane and keys == self.response_update_from_x_plane:

                    __logger__.info(f'Message from the server: {one_ingoing_object["message"]}')

                else:
                    command = one_ingoing_object['command']
                    raise ValueError(f'This response is not part of the communication chart between the \n X-Plane client and the X-Plane server.\nThe following command has been rejected\n{command}' )
                    break

            except ValueError as e:
                self.exception_error_queue.put(str(e))            
                self.keep_running.clear()
                raise # Bubbling the exception
                break 
            except Exception as e:
                error_report = format_exc()
                self.exception_error_queue.put(f'There is exception in xplane_client_managing_received_data\nMessage: {e}\nError report: {error_report}')            
                self.keep_running.clear()
                break

    def xplane_client_service_connection(self, key, mask):
        '''
        Managing sockets, selectors, received data and data to be sent.
        '''
        server_socket = key.fileobj
    
        if mask & selectors.EVENT_READ:
            try:
                ingoing_data = server_socket.recv(8192) # Should be ready to read 
            except BlockingIOError:
                pass  # Resource temporarily unavailable (errno EWOULDBLOCK)
            except:
                raise # Bubbling the exception
            else:
                if ingoing_data:
                    self.xplane_client_managing_received_data(ingoing_data)
                else:
                    raise # Bubbling the exception

        if mask & selectors.EVENT_WRITE:
            if self.outgoing_data and self.keep_running.is_set():
                next_msg = self.outgoing_data.pop(0)
                __logger__.info(f'Outgoing_data = {next_msg}')
                __logger__.info(f'')
                server_socket.sendall(next_msg)
    
    def xplane_client_treat_init_phase(self):
        '''
        Send each dataref that come from the json file to the X-Plane server for receiving it's value
        '''
        if not self.init_phase_done.is_set():
            for dataref in self.datarefs_list:
                # Prepare a request_dataref_value for the X-Plane server
                outgoing_request = {}
                outgoing_request['command'] = self.request_dataref_value
                outgoing_request['dataref'] = dataref
                outgoing_request_encode = json.dumps(outgoing_request).encode()
                self.outgoing_data.append(outgoing_request_encode)

            # Tell the server that the initialization commands have been completed. 
            # The server will then start a thread to check every second if the user press a command on the X-Plane side. 
            # Then, with this thread, the server will send the updated data to refresh the Touch Portal status and screen.  
            outgoing_request = {}
            outgoing_request['command'] = self.request_initialization_done
            outgoing_request_encode = json.dumps(outgoing_request).encode()
            self.outgoing_data.append(outgoing_request_encode)

        else:
            # Make sure that every datarefs from the datarefs_list are initialized by the X-Plane server
            self.nb_entries_datarefs_list_initialized = len(self.datarefs_list_initialized) 
            if self.nb_entries_datarefs_list_initialized == self.nb_entries_datarefs_list:
                self.datarefs_list_initialized.sort()
                if self.datarefs_list_initialized == self.datarefs_list:
                    # Every dataref passed through initialization
                    __logger__.info(f'Datarefs initialization processing was completed correctly !')
                    # Update values that come from the X-Plane server for each dataref
                    for dataref in self.datarefs_and_values_dictionary:
                        value = self.datarefs_and_values_dictionary[dataref]
                        one_id = dataref
                        one_value = value
                        __logger__.info(f'>>>>>>>>>>>>>>> {dataref} and {one_value} for stateUpdate')
                        self.tp_api.stateUpdate(one_id,one_value)
                    __logger__.info(f'State update completed !')
                    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.state.main_status', '6') # Successful Communication
                    self.init_phase_running.clear()
                else:
                    __logger__.error(f'There are initialization problem')
                    __logger__.error(f'Datarefs initialization processing was not completed correctly')
                    self.init_phase_running.clear()

        self.init_phase_done.set()

    def xplane_client_run(self):
        '''
        Handling selectors in communication with xplane server
        '''
        # The mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in self.client_selectors.select(timeout=0.1):
            if self.keep_running.is_set():
                self.xplane_client_service_connection(key, mask)
            if self.init_phase_running.is_set():
                self.xplane_client_treat_init_phase()

    def xplane_client_shutting_down(self):
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
            pass # skip any error here

    def xplane_client_thread_for_communication_with_xplane_server(self):

        '''
        Use a socket in non-blocking mode to establish a network connection with the X-Plane server. 
        Use a selector to allows monitoring multiple sockets to check their status and see if 
        they are ready for operations such as reading or writing.

        This allowing multi connection   
        '''
        self.keep_running.set()
        self.init_phase_running.set()

        try:
            if self.xplane_client_connect():
                __logger__.info(f'Preparing X-Plane to running')
                __logger__.info(f'Connecting on {(self.host, self.port)}')
                # Unblocking socket
                self.client_socket.setblocking(False)
                # Register a file object for selection, monitoring it for I/O events
                self.client_selectors.register(self.client_socket, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)

                while self.keep_running.is_set():
                    self.xplane_client_run()
        except Exception as e:
            error_report = format_exc()
            self.exception_error_queue.put(f'X-Plane server closed suddenly\nfor the xplane_client_thread_for_communication_with_xplane_server\n Message: {e}\nError report: {error_report}')            
            self.keep_running.clear()
        finally:
            __logger__.info('Ending X-Plane client thread')
            self.xplane_client_shutting_down()

    def xplane_client_stop_communicate_with_xplane_server(self):
        '''
        Stop a thread. This thread is used for network communication between the X-Plane plugin and the X-Plane server. 
        '''
        __logger__.info('Server communication shutdown and kill a thread')

        self.keep_running.clear()

    def xplane_client_communicate_with_xplane_server(self):
        '''
        Call a thread. This thread is used for network communication between the X-Plane plugin and the X-Plane server. 
        This thread will finish when the keep_running was cleared
        '''
        __logger__.info('Starting X-Plane client thread')

        try:
            self.xplane_client_thread = threading.Thread(target=self.xplane_client_thread_for_communication_with_xplane_server, args=())
            self.xplane_client_thread.start()
            self.xplane_client_thread.join()
            '''
            If an error is present in self.exception_error_queue (an error appears in the xplane_client_thread_for_communication_with_xplane_server), 
            it is retrieved and a new exception (self.CustomErrorXPlane) is raised with the error message.
            '''
            error = self.exception_error_queue.get_nowait()
            raise self.CustomErrorXPlane(str(error))
            '''
            If no error is present, the exception queue.Empty is raised by get_nowait(), 
            indicating that the queue is empty. 
            This exception is caught by the except queue.Empty (no errors detected).
            '''
        except queue.Empty:
            __logger__.info('Ending communication with X-Plane server')

def main():
    
    # Create an instance from the XPlanePlugin class.
    __XPlanePlugin = XPlanePlugin()

    successful = __XPlanePlugin.touch_portal_client_process()

    del __XPlanePlugin

    __logger__.info(f'{__plugin_id__} Return code : {successful}')
    
    sys.exit(successful)

if __name__ == '__main__':
    main()
