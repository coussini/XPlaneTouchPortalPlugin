import xp
import selectors
import socket
import json
import threading
import types

MESSAGE_DELIMITER = '#'
BUFFER_SIZE_USUAL = 1024
BUFFER_SIZE_INIT = 10240
BUFFER_SIZE = BUFFER_SIZE_INIT
HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432


class PythonInterface:

    def __init__(self):
        '''
        Class initialization. 
        '''
        self.name = 'Xplane Server For Touch Portal'
        self.sig = 'xplane.server.for.touch.portal'
        self.desc = 'An Xplane Server For Touch Portal'
        self.server_XP = None

        xp.log(f'==> Initialization')

    def XPluginStart(self):
        '''
        Called by X-Plane at startup, this is called for every plugin and each plugin returns its signature.
        '''
        return self.name, self.sig, self.desc

    def XPluginStop(self):
        '''
        Called after all plugins are disabled so each plugin is able to save its state, close files, deallocate resources.
        '''
        pass

    def XPluginEnable(self): 
        '''
        Once all plugins are started, X-Plane calls each plugin to register callbacks and other resources. 
        Each plugin returns 1 or 0 indicating it enabled properly.
        '''

        # Restart the X-Plane server at reload
        if xp.getCycleNumber() > 0: 
            self.server_XP = XPlaneServer()
            self.start_xplane_server()

        return 1

    def XPluginDisable(self):
        '''
        Called at X-Plane termination so each plugin can unregister any callbacks and stop 'doing work'.
        '''

        # Instance of XPlaneServer
        if self.server_XP is not None and self.server_XP.keep_running.is_set():
            self.stop_xplane_server()

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        '''
        While running, X-Plane may send messages to all plugins such as 'PLANE_LOADED' or 'ENTERED_VR'. Plugins use this call to handle (or ignore) the message.
        '''
        if inMessage == xp.MSG_PLANE_UNLOADED:

            try:
                if self.server_XP is not None and self.server_XP.keep_running.is_set():
                    self.stop_xplane_server()
            except:
                pass

        # A new aircraft is loaded into X-Plane (xp.MSG_AIRPORT_LOADED = 103)
        if inMessage == xp.MSG_AIRPORT_LOADED and inParam == 0:
            
            if self.server_XP is not None and self.server_XP.keep_running.is_set():
                pass
            else:

                xp.log(f'==> Start Server')
    
                # Instance of XPlaneServer
                self.server_XP = XPlaneServer()
                self.start_xplane_server()

    def start_xplane_server(self):
        
        # keep the aircraft name to check if the user change the aircraft
        self.acf_ui_name  = None
        self.dataref_name = 'sim/aircraft/view/acf_ui_name'
        self.dataref_index = None

        # This is the main loop for the XPlane Server for Touch Portal
        '''
        This is also, the loop for updates from X-Plane. 
        When a user presses a key or a command in the simulated aircraft, the dataref associated with that key is updated. 
        We then check, in this loop, if any changes have been made to the datarefs. Send any update to the Touch Portal client.
        '''
        self.xplane_server_main_loop_id = xp.createFlightLoop(self.server_XP.xplane_server_main_loop, 0, self.server_XP)

        # This is the loop for any hold command (as the cessna starter command)
        self.server_XP.xplane_server_process_request_command_3_for_touch_portal_id = xp.createFlightLoop(self.server_XP.xplane_server_process_request_command_3_for_touch_portal, 0, self.server_XP.current_command_3_status)

        # get the aircraft name 
        dataref_address, dataref_type, is_dataref_writable, dataref_value = self.server_XP.xplane_server_get_dataref_address_type_value(self.dataref_name, self.dataref_index)

        if self.acf_ui_name  != dataref_value:
            self.acf_ui_name  = dataref_value # keep the aircraft name to check if the user change the aircraft
            # prepare server configuration
            self.server_XP.xplane_server_prepare_configuration()
            # upto max 6 connection requests
            self.server_XP.server_socket.listen(6)

            xp.log(f'==> Listening on {(self.server_XP.host, self.server_XP.port)}')

            # unblocking socket
            self.server_XP.server_socket.setblocking(False)
            # Register a file object for selection, monitoring if there's new client to serve
            self.server_XP.selector.register(self.server_XP.server_socket, selectors.EVENT_READ, data=None)
            
            self.server_XP.keep_running.set()

            xp.scheduleFlightLoop(self.xplane_server_main_loop_id, -1)

    def stop_xplane_server(self):

        self.server_XP.keep_running.clear()
        self.server_XP.update_running.clear()

        # Deactivate flight loops. Flight loops remains registered, but are not called
        xp.scheduleFlightLoop(self.xplane_server_main_loop_id, 0)
        xp.scheduleFlightLoop(self.server_XP.xplane_server_process_request_command_3_for_touch_portal_id, 0)
        
        self.server_XP.xplane_server_shutting_down()
        
        # unregister instances
        xp.destroyFlightLoop(self.xplane_server_main_loop_id)
        xp.destroyFlightLoop(self.server_XP.xplane_server_process_request_command_3_for_touch_portal_id)
        self.server_XP = None
        
        xp.log(f'==> shutting down completed')

class XPlaneServer:

    def __init__(self):
        '''
        Class initialization 
        '''
        # X-Plane selectors is used for: 
        # Accepting new connections (new client)
        # Reading data sent by these accepted clients and sending data these accepted clients  
        self.selector = selectors.DefaultSelector()
        
        self.keep_running = threading.Event()
        self.update_running = threading.Event()

        # Client Connection information package or session data container for TCP/IP exchange 
        # inb: for receiving 
        # outb: for sending
        self.shared_data_container = types.SimpleNamespace(inb=bytearray(), outb=bytearray()) 

        # List of client accepted socket
        self.client_socket_list = []

        # Type for any command
        self.command_type = 9999

        # Flight Loop ID for the command hold
        self.xplane_server_process_request_command_3_for_touch_portal_id = None

        # For the 3_seconds_command process (contains dataref address and status)
        self.current_command_3_address = None
        self.current_command_3_status = {'started': False}

        self.quick_access_dataref_for_state_id_dictionary_lock = threading.Lock()         
        '''
        This following variable "self.dataref_address_for_state_id_with_value_list" is an important internal reference python list. 
        This list will be created during initialization. After this program use the "self.quick_access_dataref_for_state_id_dictionary"
            
            1) Initially, the server receives all datarefs that will be processed by Touch Portal.
               The server searches for the values of these datarefs from X-Plane side, and builds the list.
               When initialization has been completed, the program will create the "self.quick_access_dataref_for_state_id_dictionary" table 
               using the list "self.dataref_address_for_state_id_with_value_list" created in initialization.
               The values are transmitted to Touch Portal
            
            2) When a value of dataref is modified on the Touch Portal, the server receive it.
               The server searches for this datarefs in the "self.quick_access_dataref_for_state_id_dictionary" table and update the value
               The value is update on the x-plane side
            
            3) The server compares in its main loop, the datarefs from the "self.quick_access_dataref_for_state_id_dictionary" with the datarefs from x-plane.
               If there are changes, we update the special quick-access-dictionnary, then the values are transmitted to Touch Portal     

        Example of list:
        ---------------

        self.dataref_address_for_state_id_with_value_list = [
            {
                'name': 'AirbusFBW/ADIRUSwitchArray', 
                'full_name': 'AirbusFBW/ADIRUSwitchArray[0]', 
                'index': '0', 
                'address': <capsule object "XPLMDataRef" at 0x000002B768F650E0>, 
                'type': 16, 
                'is_writable': True, 
                'value': 0,
                'xplane_update_min_value' :'',
                'xplane_update_max_value' :''
            }, 
            {
                'name': 'AirbusFBW/EnableExternalPower', 
                'full_name': 'AirbusFBW/EnableExternalPower', 
                'index': None, 
                'address': <capsule object "XPLMDataRef" at 0x000002B768F64360>, 
                'type': 1, 
                'is_writable': True, 
                'value': 1,
                'xplane_update_min_value' :'',
                'xplane_update_max_value' :''
        ]   

        '''
        self.dataref_address_for_state_id_with_value_list = [] # for the initialization only
        self.quick_access_dataref_for_state_id_dictionary = {} # build with the "self.dataref_address_for_state_id_with_value_list" data
        
        '''
        This following variable "self.command_address_for_state_id" is an important internal reference python list for any X-Plane command. 
        This list contains several python dictionary. After this program use the "self.quick_access_command_dictionnary"
            
            1) Initially, the server receives all datarefs that will be processed by Touch Portal.
               The server builds the "self.command_address_for_state_id" to keep the command and address.
               When initialization has been completed, the program will create the "self.quick_access_command_dictionnary" table 
               using the list "self.command_address_for_state_id" created in initialization.


        Example of list:
        ---------------

        self.command_address_for_state_id = [
            {
                'name': 'sim/autopilot/fdir_servos_toggle', 
                'full_name': 'sim/autopilot/fdir_servos_toggle', 
                'address': <capsule object "XPLMDataRef" at 0x000002B768F64360> 
            }, 
            {
                'name': 'sim/autopilot/heading', 
                'full_name': 'sim/autopilot/heading', 
                'address': <capsule object "XPLMDataRef" at 0x000005B8558D1283> 
            }.... 
        ]   

        '''
        self.command_address_for_state_id = [] 
        self.quick_access_command_for_state_id_dictionary = {} # build with the "self.command_address_for_state_id" data

        '''
        ============================================================================
        This is the chart for communifcation paquet between the client and the server
        ============================================================================
        '''
        # Packet that asks this server for the current state_id value in x-plane (initialization part)  
        self.request_state_id_value = 'request_state_id_value'
        self.request_state_id_value_paquet = ['command', 'state_id', 'dataref', 'xplane_update_max_value', 'xplane_update_min_value']

        # Packet for response for the previous request  
        self.response_state_id_value = 'response_state_id_value'
        self.response_state_id_value_paquet = ['command', 'state_id', 'message', 'value']

        # Packet that explains to this server that the initialization part is completed  
        self.request_initialization_done = 'request_initialization_done'
        self.request_initialization_done_paquet = ['command']
        # Packet for response for the previous request  
        self.response_initialization_done = 'response_initialization_done'
        self.response_initialization_done_paquet = ['command', 'message']

        # Packet that explains to this server that a state_id value has been updated in Touch Portal  
        self.request_update_from_touch_portal = 'request_update_from_touch_portal'
        self.request_update_from_touch_portal_paquet = ['command', 'state_id', 'value']
        # Packet for response for the previous request  
        self.response_update_from_touch_portal = 'response_update_from_touch_portal'
        self.response_update_from_touch_portal_paquet = ['command', 'state_id', 'message']

        # Packet that explains to this server that a command must be executed on the x-plane side  
        self.request_command_for_touch_portal = 'perform_command_for_touch_portal'
        self.request_command_for_touch_portal_paquet = ['command', 'state_id']
        # Packet for response for the previous request  
        self.response_command_for_touch_portal = 'response_perform_command_for_touch_portal'
        self.response_command_for_touch_portal_paquet = ['command', 'state_id', 'message']

        # Packet that explains to this server that a command_3 must be executed on the x-plane side  
        self.request_command_3_for_touch_portal = 'perform_command_3_for_touch_portal'
        self.request_command_3_for_touch_portal_paquet = ['command', 'state_id']
        # Packet for response for the previous request  
        self.response_command_3_for_touch_portal = 'response_perform_command_3_for_touch_portal'
        self.response_command_3_for_touch_portal_paquet = ['command', 'state_id', 'message']

        # Packet that explains to the client that a state_id value has been updated in X-Plane  
        self.request_update_from_x_plane = 'request_update_from_x_plane'
        self.request_update_from_x_plane_paquet = ['command', 'state_id', 'value']
        # Packet for response for the previous request  
        self.response_update_from_x_plane = 'response_update_from_x_plane'
        self.response_update_from_x_plane_paquet = ['command', 'state_id', 'message']

    def is_int(self, dataref_value):
        ''' 
        Validate the received dataref's value according to int
        '''

        try:
            int(dataref_value)
            return True, int(dataref_value)
        except ValueError:
            return False, None

    def is_float_or_double(self, dataref_value):
        ''' 
        Validate the received dataref's value according to float or double
         
        '''

        try:
            float(dataref_value)
            return True, float(dataref_value)
        except ValueError:
            return False, None

    def xplane_server_split_to_dataref_name_and_index(self, dataref):
        '''
        Separate name and index of received dataref string

        Exemple for a dataref parameter contaning 'AirbusFBW/OHPLightSwitches[9]'
            dataref_name  = AirbusFBW/OHPLightSwitches
            dataref_index = 9

        Exemple for a dataref parameter contaning 'AirbusFBW/PanelFloodBrightnessLevel'
            dataref_name  = AirbusFBW/PanelFloodBrightnessLevel
            dataref_index = None
        '''
        dataref_index = None 
        dataref_name = dataref.replace('[',' ').replace(']',' ').split()

        # it's a dataref with an index
        if len(dataref_name) == 2: 
            dataref_index = dataref_name[1]
            dataref_name = dataref_name[0]
        
        # it's not a dataref with an index
        else: 
            dataref_name = dataref_name[0]

        return dataref_name, dataref_index 

    def xplane_server_read_a_dataref(self, dataref_address, dataref_type, dataref_index):
        ''' 
        Read a dataref according to it's address, type and index
        Keep only 2 digit for any float and double  
    
        ==============
        IMPORTANT NOTE:
        ==============
        Only 2 digits are kept in x-plane for float or double. 

        I consider two decimal, to be sufficient for a good processing in touch portal.
        These values are stored in a special internal table.

        *** By increasing the number of digits, the server must send data more often. 
            Precision is more demanding in terms of exchange.

        '''
        if bool(dataref_type & xp.Type_Unknown):
            return None
        
        elif bool(dataref_type & xp.Type_Int):
            value = xp.getDatai(dataref_address) 
            return value
        
        elif bool(dataref_type & xp.Type_Float):
            value = xp.getDataf(dataref_address)
            return round(value, 2)
        
        elif bool(dataref_type & xp.Type_Double):
            value = xp.getDatad(dataref_address)
            return round(value, 2)
        
        elif bool(dataref_type & xp.Type_FloatArray):
            values = []
            xp.getDatavf(dataref_address, values, int(dataref_index), 1)
            return round(values[0], 2)
        
        elif bool(dataref_type & xp.Type_IntArray):
            values = []
            xp.getDatavi(dataref_address, values, int(dataref_index), 1)
            return values[0]
        
        elif bool(dataref_type & xp.Type_Data):
            return xp.getDatas(dataref_address) # Data
        
        else:
            return None

    def xplane_server_append_to_dataref_address_for_state_id_with_value_list(self, state_id, dataref_name, dataref, dataref_index, dataref_address, dataref_type, is_dataref_writable, dataref_value, xplane_update_min_value, xplane_update_max_value):
        '''
        Initialization of internal list dataref_address_for_state_id_with_value_list
        '''
        # make a python list within data
        append_state_id = {
            'state_id': state_id, 
            'name': dataref_name, 
            'full_name': dataref, 
            'index': dataref_index,
            'address': dataref_address, 
            'type': dataref_type,
            'is_writable': is_dataref_writable, 
            'value': dataref_value,
            'xplane_update_min_value': xplane_update_min_value,
            'xplane_update_max_value': xplane_update_max_value
        }  

        # append this dataref to the internal list  
        self.dataref_address_for_state_id_with_value_list.append(append_state_id)

    def xplane_server_append_to_command_address_for_state_id(self, state_id, command_name, command_full_name, command_address):
        '''
        Initialization of internal list command_address_for_state_id
        '''
        
        # make a python list within data
        append_state_id = {
            'state_id': state_id, 
            'name': command_name, 
            'full_name': command_full_name, 
            'address': command_address 
        }  

        # append this dataref to the internal list  
        self.command_address_for_state_id.append(append_state_id)

    def xplane_server_get_dataref_address_type_value(self, dataref_name, dataref_index):
        ''' 
        The following data will be obtained within dataref name and dataref index:
            -The address of the dataref read: we'll keep this address for greater access efficiency.  
            -The type of dataref: can be Int, Float, Double, FloatArray, IntArray and Data.
            -Whether or not if this dataref is writable.
        '''

        dataref_type = None
        is_dataref_writable = False
        dataref_value = None

        # Note: findCommand function is relatively expensive. For this reason, we'll save the command address in an array 
        dataref_address = xp.findCommand(dataref_name)

        if dataref_address != None:
            dataref_type = self.command_type # special type for a command type
        else:    
            # Note: findDataRef function is relatively expensive. For this reason, we'll save the dataref address in an array
            # At this point, if the address from the command "xp.findDataRef" = None, this means that there is no information for the dataref_name received. 
            dataref_address = xp.findDataRef(dataref_name) 
            if dataref_address != None: 
                dataref_type = xp.getDataRefTypes(dataref_address)
                is_dataref_writable = xp.canWriteDataRef(dataref_address)
                dataref_value = self.xplane_server_read_a_dataref(dataref_address, dataref_type, dataref_index)
        
        return dataref_address, dataref_type, is_dataref_writable, dataref_value

    def xplane_server_get_quick_access_dataref_for_state_id_dictionary(self, state_id):
        '''
        Get the state_id's address, type and index
        '''
        dataref_address = None
        dataref_type = None 
        dataref_index = None 

        # search in the "self.quick_access_dataref_for_state_id_dictionary" for the dataref
        dataref_item = self.quick_access_dataref_for_state_id_dictionary.get(state_id)

        if dataref_item:
            dataref_address = dataref_item['address']
            dataref_type = dataref_item['type']
            dataref_index = dataref_item['index']

        return dataref_address, dataref_type, dataref_index 

    def xplane_server_get_quick_access_command_for_state_id_dictionary(self, state_id):
        '''
        Get the address for command
        '''
        command_address = None

        # search in the "self.quick_access_command_for_state_id_dictionary" for the command
        command_item = self.quick_access_command_for_state_id_dictionary.get(state_id)

        if command_item:
            command_address = command_item['address']

        return command_address 

    def xplane_server_update_quick_access_dataref_for_state_id_dictionary(self, state_id, value):
        '''
        Update the internal list with the new dataref's value for corresponding state_id
        '''
        # search in the "self.quick_access_dataref_for_state_id_dictionary" for the state_id
        dataref_item = self.quick_access_dataref_for_state_id_dictionary.get(state_id)

        if dataref_item:
            with self.quick_access_dataref_for_state_id_dictionary_lock:            
                dataref_item['value'] = value    
    
    def xplane_server_process_request_state_id_value(self, state_id, dataref, xplane_update_min_value, xplane_update_max_value):
        '''
        Next, the program will store the state_id's data in a python list, wich will used during the update. 
        The update will use the dataref's address (stored during initialization) to update its value.
        Send the value to the x-plane server client

        Context:
        As soon as we display a Touch Portal page and its buttons, we need to obtain the button values (associated with a dataref). 
        The purpose of this is to have the same buttons state on both sides (airplane in X-Plane vs Touch Portal panel).
        '''
        dataref_name, dataref_index = self.xplane_server_split_to_dataref_name_and_index(dataref)
        dataref_address, dataref_type, is_dataref_writable, dataref_value = self.xplane_server_get_dataref_address_type_value(dataref_name, dataref_index)

        message = {}
        message['command'] = self.response_state_id_value
        message['state_id'] = state_id
        message['value'] = str(dataref_value)

        if dataref_address == None: 
            message['message'] = 'dataref is not found or it is not a command type'
        elif dataref_type != self.command_type:
            self.xplane_server_append_to_dataref_address_for_state_id_with_value_list(state_id, dataref_name, dataref, dataref_index, dataref_address, dataref_type, is_dataref_writable, dataref_value, xplane_update_min_value, xplane_update_max_value)
            message['message'] = 'the dataref value has been successfully obtained'
        else: # dataref_type == self.command_type
            self.xplane_server_append_to_command_address_for_state_id(state_id, dataref_name, dataref, dataref_address)
            message['message'] = 'the command has been successfully obtained'

        outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
        self.shared_data_container.outb += outgoing_message.encode('utf-8')                    

    def xplane_server_process_request_initialization_done(self):
        '''
        When the initialization is completed, inform the client that the server will start a thread for any update in x-plane dataref. 

        Context:
        As soon as we press a button in x-plane aircraft (dataref changes), send the value to Touch Portal. 
        The purpose of this is to have the same buttons state on both sides (airplane in X-Plane vs Touch-Portal panel).
        '''

        # once initialization is complete", create all quick access table
        self.quick_access_dataref_for_state_id_dictionary = {item['state_id']: item for item in self.dataref_address_for_state_id_with_value_list}
        self.quick_access_command_for_state_id_dictionary = {item['state_id']: item for item in self.command_address_for_state_id}

        message = {}
        message['command'] = self.response_initialization_done
        message['message'] = 'X-Plane server will now monitoring for updates from x-plane'
        outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
        self.shared_data_container.outb += outgoing_message.encode('utf-8')                    
        
        # Start the update process from x-plane dataref (just the dataref inside quick_access_dataref_for_state_id_dictionary)
        self.update_running.set()
        BUFFER_SIZE = BUFFER_SIZE_USUAL

    def xplane_server_is_valid_value(self, dataref_type, dataref_value):
        ''' 
        Validate the received dataref's value according to the dataref's type 
        '''
        if bool(dataref_type & xp.Type_Int):
            return self.is_int(dataref_value) 
        
        elif bool(dataref_type & xp.Type_Float):
            return self.is_float_or_double(dataref_value) 
        
        elif bool(dataref_type & xp.Type_Double):
            return self.is_float_or_double(dataref_value) 
        
        elif bool(dataref_type & xp.Type_FloatArray):
            return self.is_float_or_double(dataref_value) 
        
        elif bool(dataref_type & xp.Type_IntArray):
            return self.is_int(dataref_value) 

        else: 
            return False, None

    def xplane_server_write_a_dataref(self, dataref_address, dataref_type, dataref_index, dataref_value):
        ''' 
        Write a dataref according to it's address, type, index and value 
        '''
        if bool(dataref_type & xp.Type_Unknown):
            return False
        
        elif bool(dataref_type & xp.Type_Int):
            xp.setDatai(dataref_address,dataref_value) 
        
        elif bool(dataref_type & xp.Type_Float):
            xp.setDataf(dataref_address,dataref_value) 
        
        elif bool(dataref_type & xp.Type_Double):
            xp.setDatad(dataref_address,dataref_value) 
        
        elif bool(dataref_type & xp.Type_FloatArray):
            value = [dataref_value]
            xp.setDatavf(dataref_address, value, int(dataref_index), 1)
        
        elif bool(dataref_type & xp.Type_IntArray):
            value = [dataref_value]
            xp.setDatavi(dataref_address, value, int(dataref_index), 1)
        
        elif bool(dataref_type & xp.Type_Data):
            xp.setDatas(dataref_address, dataref_value)
        
        else:
            return False

        return True

    def xplane_server_process_request_update_from_touch_portal(self, state_id, value):
        '''
        Process Touch Portal client update command. 
        Update X-Plane by searching in a quick access array and obtaining its address.

        Context:
        If a user presses a button in Touch Portal, a command is sent to the xplane server to update his dataref for the corresponding state_id. 
        The purpose of this is to have the same buttons state on both sides (airplane in X-Plane vs Touch Portal).
        '''
        dataref_address, dataref_type, dataref_index = self.xplane_server_get_quick_access_dataref_for_state_id_dictionary(state_id)

        message = {}
        message['command'] = self.response_update_from_touch_portal
        message['state_id'] = state_id

        if dataref_address != None:
            is_valid, transform_value = self.xplane_server_is_valid_value(dataref_type,value)
            if is_valid:
                if self.xplane_server_write_a_dataref(dataref_address, dataref_type, dataref_index, transform_value):
                    message['message'] = 'successful dataref update for state_id'
                    self.xplane_server_update_quick_access_dataref_for_state_id_dictionary(state_id, transform_value)
                else:
                    message['message'] = 'unknown dataref\'s type'
            else:
                message['message'] = 'the dataref\'s value is wrong according to the dataref\'s type'

            outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
            self.shared_data_container.outb += outgoing_message.encode('utf-8')                    

    def xplane_server_process_request_command_for_touch_portal(self, state_id):
        '''
        Process Touch Portal client x-plane command. 
        Process the X-Plane command by searching in a quick access array and obtaining its address.
        '''

        command_address = self.xplane_server_get_quick_access_command_for_state_id_dictionary(state_id)

        message = {}
        message['command'] = self.response_command_for_touch_portal
        message['state_id'] = state_id

        if command_address != None:
            try:
                xp.commandOnce(command_address)

            except:
                message['message'] = 'cannot execute the command for dataref address'
            else:
                message['message'] = 'successful executed x-plane command'

            outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
            self.shared_data_container.outb += outgoing_message.encode('utf-8')                    

    def xplane_server_process_request_command_3_for_touch_portal(self, sinceLast, elapsedTime, counter, refCon): 
        '''
        Process Touch Portal client x-plane command hold. 
        This is the Flight Loop for command hold -> xp command "begin-end" purpose
        '''
        
        # Begin a command until 1.5 second is reach. This is to simulate a starter process or other command for about 3 seconds
        if not self.current_command_3_status['started']:
            xp.commandBegin(self.current_command_3_address);
            self.current_command_3_status['started'] = True
            return 1.5

        # Stop a command that is began before
        xp.commandEnd(self.current_command_3_address)

        self.current_command_3_status = {'started': False}

        # Stop the flight loop
        return 0

    def xplane_server_managing_received_data(self, client_socket, message_decode):
        '''
        Process the received data packet from the x-plane server client
        '''

        try:
            message_object = json.loads(message_decode)

        except json.JSONDecodeError as e:            
            xp.log(f"==> ERROR ->")
            xp.log(f"==> ERROR -> =================================================================")
            xp.log(f"==> ERROR -> JSON decode error: {e} for message: {message_decode}")
            xp.log(f"==> ERROR -> =================================================================")
            self.xplane_client_socket_die(client_socket)

        except Exception as e:            
            xp.log(f"==> ERROR ->")
            xp.log(f"==> ERROR -> =================================================================")
            xp.log(f"==> ERROR -> Unexpected error: {e} for message: {message_decode}")
            xp.log(f"==> ERROR -> =================================================================")
            self.xplane_client_socket_die(client_socket)

        keys = list(message_object.keys())

        # Process a request from the x-plane server client for the initialization part
        if message_object['command'] == self.request_state_id_value and set(keys) == set(self.request_state_id_value_paquet):
            self.xplane_server_process_request_state_id_value(message_object['state_id'], message_object['dataref'], message_object['xplane_update_min_value'], message_object['xplane_update_max_value'])

        # Process a request from the x-plane server client when the initialization part is finish
        elif message_object['command'] == self.request_initialization_done and set(keys) == set(self.request_initialization_done_paquet):
            xp.log("==> Initialization done by the client")
            self.xplane_server_process_request_initialization_done()
        
        # Process a request for the x-plane server client when a dataref value has been updated in Touch Portal.
        # This following does nothing if the plugin publishing the dataRef is disabled, the dataRef is invalid, 
        # or the dataRef is not writable
        elif message_object['command'] == self.request_update_from_touch_portal and set(keys) == set(self.request_update_from_touch_portal_paquet):
            self.xplane_server_process_request_update_from_touch_portal(message_object['state_id'], message_object['value'])
        
        elif message_object['command'] == self.response_update_from_x_plane  and set(keys) == set(self.response_update_from_x_plane_paquet):
            pass
        
        # Process a request for the x-plane server client when a command has been ask for in Touch Portal.
        elif message_object['command'] == self.request_command_for_touch_portal and set(keys) == set(self.request_command_for_touch_portal_paquet):
            self.xplane_server_process_request_command_for_touch_portal(message_object['state_id'])
        
        # Process a request for the x-plane server client when a 3_seconds_command has been ask for in Touch Portal.
        elif message_object['command'] == self.request_command_3_for_touch_portal and set(keys) == set(self.request_command_3_for_touch_portal_paquet):
            command_address = self.xplane_server_get_quick_access_command_for_state_id_dictionary(message_object['state_id'])
            self.current_command_3_address = command_address
            # Start a Flight Loop for Command_3 type
            xp.scheduleFlightLoop(self.xplane_server_process_request_command_3_for_touch_portal_id, -1)
        else:
            command = message_object['command']
            xp.log(f'==> ERROR -> This response is not part of the communication chart between the \n X-Plane client and the X-Plane server.\nThe following command has been rejected\n{command} \nWith key: \n{keys}' )

    def xplane_server_die(self, client_socket):
        '''
        Close connections and remove this client socket objects from selector
        '''
        xp.log(f'==> A client close a socket, Closing client connection to {client_socket.getpeername()}')
        self.selector.unregister(client_socket)
        client_socket.close()
        self.client_socket_list.remove(client_socket)

    def xplane_server_accept_wrapper(self, server_socket):
        ''' 
        Accept connection from client
        '''
        client_socket, client_address = self.server_socket.accept()  # Should be ready to read
        client_socket.setblocking(False)
        self.client_socket_list.append(client_socket)
        xp.log(f'==> X-Plane client connected: connection {client_address}')

        # keep the client address in the connection information package or session data container for TCP/IP exchange
        self.shared_data_container.addr = client_address
        self.selector.register(client_socket, selectors.EVENT_READ | selectors.EVENT_WRITE, data=self.shared_data_container)        

    def xplane_server_find_value_according_step_value(self, actual_dataref_value, min_val, max_val, step):
        ''' 
        Return a new actual_dataref_value according the minimum value, the maximum value and the step
        
        Example:
            - min_val = 0
            - max_val = 1
            - step = 0.25
            - possible_values = [0, 0.25, 0.50, 0.75, 1]
        Another example:
            - min_val = 0
            - max_val = 0.8
            - step = 0.25
            - possible_values = [0, 0.25, 0.50, 0.75, 0.8] -> include the max_value all the time
        '''

        # Generate possible values
        # Inclure the max_val all the time.
        possible_values = [min_val + i * step for i in range(int((max_val - min_val) / step) + 1)]

        if max_val not in possible_values:
            possible_values.append(max_val)

        # Find the nearest value inside the possible_values
        nearest_value = min(possible_values, key=lambda x: abs(x - actual_dataref_value))
        
        return nearest_value

    def xplane_server_calculate_increment(self, min_value, max_value, steps=4):
        '''
        This calculate the increment needed to divide the range from min_value to max_value into 'steps' equal parts.. 
        '''
        increment = (max_value - min_value) / steps

        return increment

    def xplane_server_monitoring_dataref_updates_from_xplane(self, client_socket):
        '''
        This is the process for updates from X-Plane. 
        When a user presses a key or a command in the simulated aircraft, the dataref associated with that key is updated. 
        We then check, in this loop, if any changes have been made to the datarefs. Send any update to the Touch Portal client.
        '''
        if self.update_running.is_set():

            for state_id, dataref_item in self.quick_access_dataref_for_state_id_dictionary.items():

                dataref_value = self.xplane_server_read_a_dataref(dataref_item['address'], dataref_item['type'], dataref_item['index'])

                # if the last value contained in the dataref's list is not equal 
                # to the x-plane dataref's value, this means a user has pressed a command on the x-plane side. 
                # Send this new value to Touch-Portal

                if dataref_item['xplane_update_min_value'] != '':
                    min_value = float(dataref_item['xplane_update_min_value'])
                    max_value = float(dataref_item['xplane_update_max_value'])
                    step = self.xplane_server_calculate_increment(min_value, max_value)
                    nearest_value = self.xplane_server_find_value_according_step_value(dataref_value, min_value, max_value, step)

                    if dataref_item['value'] != nearest_value:
                        dataref_value = nearest_value
                    else:
                        dataref_value = dataref_item['value'] # force skip next condition 
                
                # IMPORTANT: we send the value, only if it is different
                if dataref_item['value'] != dataref_value: 
                    # update the dataref's in quick_access_dataref_for_state_id_dictionary array  
                    with self.quick_access_dataref_for_state_id_dictionary_lock:            
                        dataref_item['value'] = dataref_value

                    # returning the new value as a string to the X-Plane client for Touch Portal
                    message = {}
                    message['command'] = self.request_update_from_x_plane
                    message['state_id'] = dataref_item['state_id']
                    message['value'] = str(dataref_value)
                    outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
                    self.shared_data_container.outb += outgoing_message.encode('utf-8')                    

    def xplane_server_is_client_socket_available(self, client_socket_to_search):
        '''
        Before trying sending something, check if client socket is ready for that
        '''
        for client_socket in list(self.client_socket_list):
            if client_socket_to_search == client_socket:
                return True
                break

        return False


    def xplane_server_service_connection(self, key, mask):
        '''
        Manage Read event for selectors and receive ingoing data
        Also, monitoring dataref updates from x-plane
        '''
        client_socket = key.fileobj
        data = key.data # data is a reference to the self.shared_data_container object

        if mask & selectors.EVENT_READ:
            try:
                ingoing_message = client_socket.recv(BUFFER_SIZE)  # Should be ready to read
            except BlockingIOError:
                pass                                     # Resource temporarily unavailable (errno EWOULDBLOCK)
            except ConnectionResetError:
                xp.log('==> ERROR -> ConnectionResetError !!!')
                self.xplane_server_die(client_socket)
            except:
                raise                                    # No connection
            else:
                if ingoing_message:
                    data.inb += ingoing_message
                    # Each command contain a MESSAGE_DELIMITER at the end. Easy for separate commands
                    while MESSAGE_DELIMITER.encode('utf-8') in data.inb:
                        pos = data.inb.index(bytes(MESSAGE_DELIMITER, 'utf-8'))
                        message_bytes  = data.inb[:pos]  # The first message
                        data.inb = data.inb[pos+len(MESSAGE_DELIMITER):]  # Remove the first message from data.inb (message+'#') 
                        message_decode = message_bytes.decode('utf-8') 
                        if not message_decode:
                            continue # probably catch only the delimiter
                        else: 
                            self.xplane_server_managing_received_data(client_socket, message_decode)
                else:
                    xp.log('==> ERROR -> No ingoing_message')
                    self.xplane_server_die(client_socket)

        if mask & selectors.EVENT_WRITE:
            try:
                if self.xplane_server_is_client_socket_available(client_socket):
                    if data.outb:
                        while data.outb:
                            if len(data.outb) <= BUFFER_SIZE and data.outb[-1] == ord('#'):
                                sent = client_socket.send(data.outb)  # Send the entire buffer
                                data.outb = data.outb[sent:]
                            else:
                                send_chunk = data.outb[:BUFFER_SIZE]
                                if send_chunk[-1] == ord('#'):
                                    sent = client_socket.send(send_chunk)
                                    data.outb = data.outb[sent:]
                                else:
                                    last_hash_index = send_chunk.rfind(ord('#'))
                                    if last_hash_index != -1:
                                        send_chunk = data.outb[:last_hash_index+1]
                                        sent = client_socket.send(send_chunk)
                                        data.outb = data.outb[sent:]
                                    else:
                                        # No delimiter found
                                        xp.log(f"==> ERROR -> Problem: Sending message without #")
                                        xp.log(f"==> ERROR -> message = {data.outb}")
                                        self.xplane_server_die(client_socket) # possibly the client socket is close and the server try to send something 
                    else:    
                        self.xplane_server_monitoring_dataref_updates_from_xplane(client_socket) # This is the process for updates from X-Plane.
                else:
                    data.outb = b'' # clear variable data.outb
            except (BrokenPipeError, ConnectionResetError, socket.error) as e:
                    xp.log(f"==> ERROR -> Sending Error: {e}")
                    self.xplane_server_die(client_socket) # possibly the client socket is close and the server try to send something 

    def xplane_server_main_loop(self, sinceLast, elapsedTime, counter, refCon): 
        '''
        This is the Flight Loop for server purpose
        '''
        for key, mask in self.selector.select(timeout=0):
            if key.data is None:
                self.xplane_server_accept_wrapper(key.fileobj)
            else:
                self.xplane_server_service_connection(key, mask)

        return 0.5

    def xplane_server_shutting_down(self):
        '''
        Processing the server closure procedure
        '''

        # going through the client socket,  in case there are some unclosed
        for client_socket in list(self.client_socket_list):
            self.selector.unregister(client_socket)
            client_socket.close()
            self.client_socket_list.remove(client_socket)

        self.selector.close()

    def xplane_server_prepare_configuration(self):
        ''' 
        Prepare X-Plane server configuration
        '''
        # X-Plane server configuration

        self.host = HOST
        self.port = PORT
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
