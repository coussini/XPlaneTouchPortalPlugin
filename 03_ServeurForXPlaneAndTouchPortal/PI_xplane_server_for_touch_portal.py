import xp
import selectors
import socket
import json
import threading
import types

MESSAGE_DELIMITER = '#'

class PythonInterface:

    def __init__(self):
        '''
        Class initialization. 
        '''
        self.name = 'Xplane Server For Touch Portal'
        self.sig = 'xplane.server.for.touch.portal'
        self.desc = 'An Xplane Server For Touch Portal'
        
        # host and port for the XPlane Server for Touch Portal
        host = socket.gethostbyname(socket.gethostname())
        port = 65432
        self.server_XP = XPlaneServer(host,port)
        
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
        self.xplane_server_main_loop_id = xp.createFlightLoop(self.server_XP.xplane_server_main_loop,0,self.server_XP)

    def XPluginStart(self):
        '''
        Called by X-Plane at startup, this is called for every plugin and each plugin returns its signature.
        '''
        print(f'############')
        print(f'XPluginStart')
        print(f'############')

        return self.name, self.sig, self.desc

    def XPluginStop(self):
        '''
        Called after all plugins are disabled so each plugin is able to save its state, close files, deallocate resources.
        '''
        print(f'###########')
        print(f'XPluginStop')
        print(f'###########')

        pass

    def XPluginEnable(self): 
        '''
        Once all plugins are started, X-Plane calls each plugin to register callbacks and other resources. 
        Each plugin returns 1 or 0 indicating it enabled properly.
        '''
        print(f'#############')
        print(f'XPluginEnable')
        print(f'#############')

        # Restart the X-Plane server at reload
        if xp.getCycleNumber() > 0: 
            self.start_xplane_server()

        return 1

    def XPluginDisable(self):
        '''
        Called at X-Plane termination so each plugin can unregister any callbacks and stop 'doing work'.
        '''
        print(f'##############')
        print(f'XPluginDisable')
        print(f'##############')
        self.server_XP.keep_running.clear()
        self.server_XP.update_running.clear()

        # Deactivate flight loops. Flight loops remains registered, but are not called
        xp.scheduleFlightLoop(self.xplane_server_main_loop_id,0)
        
        self.server_XP.xplane_server_shutting_down()
        
        # unregister instances
        del self.server_XP
        xp.destroyFlightLoop(self.xplane_server_main_loop_id)
        
        print('shutting down completed')

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        '''
        While running, X-Plane may send messages to all plugins such as 'PLANE_LOADED' or 'ENTERED_VR'. Plugins use this call to handle (or ignore) the message.
        '''
        print(f'##################################################################')
        print(f'XPluginReceiveMessage {inFromWho}, {inMessage}, {inParam}')
        print(f'##################################################################')
        # A new aircraft is loaded into X-Plane (xp.MSG_AIRPORT_LOADED = 103)
        if inMessage == xp.MSG_AIRPORT_LOADED and inParam == 0:
            self.start_xplane_server()

    def start_xplane_server(self):

        # get the aircraft name 
        dataref_address,dataref_type,is_dataref_writable,dataref_value = self.server_XP.xplane_server_get_dataref_address_type_value(self.dataref_name, self.dataref_index)

        if self.acf_ui_name  != dataref_value:
            self.acf_ui_name  = dataref_value # keep the aircraft name to check if the user change the aircraft
            if self.server_XP.keep_running.is_set():
                pass
            else:
                #print('------------------> here')
                self.server_XP.server_socket.bind((self.server_XP.host, self.server_XP.port))
                print(f'Listening on {(self.server_XP.host, self.server_XP.port)}')
                
                # upto max 6 connection requests
                self.server_XP.server_socket.listen(6)
                # unblocking socket
                self.server_XP.server_socket.setblocking(False)
                self.server_XP.keep_running.set()
                xp.scheduleFlightLoop(self.xplane_server_main_loop_id,-1)

class XPlaneServer:

    def __init__(self, host, port):
        '''
        Class initialization 
        '''
        self.server_selectors = selectors.DefaultSelector()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = host
        self.port = port
        self.keep_running = threading.Event()
        self.update_running = threading.Event()

        # Connection information package or session data container for TCP/IP exchange 
        # inb for receiving and outb for sending)
        self.shared_data_container = types.SimpleNamespace(inb=bytearray(),outb=bytearray()) 

        # keep the address in the connection information package or session data container for TCP/IP exchange
        self.shared_data_container.addr = (self.host,self.port)

        self.outgoing_data = types.SimpleNamespace()
        self.client_socket_list = []
        
        '''
        This following variable "self.dataref_address_and_value_list" is an important internal reference python list. 
        This list contains several python dictionary.
            
            1) Initially, the server receives all datarefs that will be processed by Touch Portal.
               The server searches for the values of these datarefs from X-Plane side, and builds the list
               The values are transmitted to Touch Portal
            
            2) When a value of dataref is modified on the Touch Portal, the server receive it.
               The server searches for this datarefs in the list and update the value in the list
               The value is update on the x-plane side
            
            3) The server compares in its main loop, the datarefs from the list with the datarefs from x-plane.
               If there are changes, we update the list, then the values are transmitted to Touch Portal     

        Example of list:
        ---------------

        self.dataref_address_and_value_list = [
            {
                'name': 'AirbusFBW/ADIRUSwitchArray', 
                'full_name': 'AirbusFBW/ADIRUSwitchArray[0]', 
                'index': '0', 
                'address': <capsule object "XPLMDataRef" at 0x000002B768F650E0>, 
                'type': 16, 
                'is_writable': True, 
                'value': 0
            }, 
            {
                'name': 'AirbusFBW/EnableExternalPower', 
                'full_name': 'AirbusFBW/EnableExternalPower', 
                'index': None, 
                'address': <capsule object "XPLMDataRef" at 0x000002B768F64360>, 
                'type': 1, 
                'is_writable': True, 
                'value': 1
            }.... 
        ]   

        '''
        self.dataref_address_and_value_list = [] 
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

    def xplane_server_get_dataref_name_and_index(self, dataref):
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
        '''
        if bool(dataref_type & xp.Type_Unknown):
            return None
        
        elif bool(dataref_type & xp.Type_Int):
            return xp.getDatai(dataref_address) 
        
        elif bool(dataref_type & xp.Type_Float):
            return xp.getDataf(dataref_address) 
        
        elif bool(dataref_type & xp.Type_Double):
            return xp.getDatad(dataref_address) 
        
        elif bool(dataref_type & xp.Type_FloatArray):
            values = []
            xp.getDatavf(dataref_address, values, int(dataref_index), 1)
            return values[0]
        
        elif bool(dataref_type & xp.Type_IntArray):
            values = []
            xp.getDatavi(dataref_address, values, int(dataref_index), 1)
            return values[0]
        
        elif bool(dataref_type & xp.Type_Data):
            return xp.getDatas(dataref_address) # Data
        
        else:
            return None

    def xplane_server_get_dataref_address_type_value(self, dataref_name, dataref_index):
        ''' 
        The following data will be obtained within dataref name and dataref index:
            -The address of the dataref read: we'll keep this address for greater access efficiency.  
            -The type of dataref: can be Int, Float, Double, FloatArray, IntArray and Data.
            -Whether or not if this dataref is writable.
            -The value of the dataref
        '''

        dataref_type = None
        is_dataref_writable = False
        dataref_value = None

        # Note: findDataRef function is relatively expensive. For this reason, we'll save the dataref address in an array 
        dataref_address = xp.findDataRef(dataref_name)
        
        if dataref_address != None:
            dataref_type = xp.getDataRefTypes(dataref_address)
            is_dataref_writable = xp.canWriteDataRef(dataref_address)
            dataref_value = self.xplane_server_read_a_dataref(dataref_address,dataref_type,dataref_index)
        
        return dataref_address,dataref_type,is_dataref_writable,dataref_value

    def xplane_server_append_to_dataref_address_and_value_list(self, dataref_name, dataref, dataref_index, dataref_address, dataref_type, is_dataref_writable, dataref_value):
        '''
        Initialization of internal list dataref_address_and_value_list
        '''
        
        # make a python list within data
        append_dataref = {
            'name': dataref_name, 
            'full_name': dataref, 
            'index': dataref_index,
            'address': dataref_address, 
            'type': dataref_type,
            'is_writable': is_dataref_writable, 
            'value': dataref_value
        }  

        # append this dataref to the internal list  
        self.dataref_address_and_value_list.append(append_dataref)

        '''
        print(f'')
        print(f'')
        print(f'append_dataref = {append_dataref}')
        print(f'')
        print(f'table interne = {self.dataref_address_and_value_list}')
        print(f'')
        '''

    def xplane_server_get_dataref_address_type_and_index(self, full_name):
        '''
        Get the dataref's address and type
        '''
        
        dataref_address = None
        dataref_type = None 
        dataref_index = None 

        # search in the associative array for the dataref's address
        for dataref in self.dataref_address_and_value_list:
            if dataref['full_name'] == full_name:
                dataref_address = dataref['address']
                dataref_type = dataref['type']
                dataref_index = dataref['index']
                break

        return dataref_address, dataref_type, dataref_index 

    def xplane_server_update_dataref_address_and_value_list(self, full_name, value):
        '''
        Update the internal list with the new dataref's value
        '''
        # search in the associative array for the dataref's address
        for dataref in self.dataref_address_and_value_list:
            if dataref['full_name'] == full_name:
                print(f">>>>>xplane_server_update_dataref_address_and_value_list for {full_name} and value {value}<<<<<")
                dataref['value'] = value
                break
    
    def xplane_server_process_request_dataref_value(self, dataref):
        '''
        Next, the program will store the dataref's data in a python list, wich will used during the update. 
        The update will use the dataref's address (stored during initialization) to update its value.
        Send the value to the x-plane server client

        Context:
        As soon as we display a Touch Portal page and its buttons, we need to obtain the button values (associated with a dataref). 
        The purpose of this is to have the same buttons state on both sides (airplane in X-Plane vs Touch Portal panel).
        '''
        #print('xplane_server_process_request_dataref_value')
        dataref_name,dataref_index = self.xplane_server_get_dataref_name_and_index(dataref)
        #print(f'dataref_name & dataref_index {dataref_name} & {dataref_index}')
        dataref_address,dataref_type,is_dataref_writable,dataref_value = self.xplane_server_get_dataref_address_type_value(dataref_name,dataref_index)
        #print(f'dataref_value {dataref_value}')
        #print(f'')

        message = {}
        message['command'] = self.response_dataref_value
        message['dataref'] = dataref
        message['value'] = str(dataref_value)

        if dataref_address != None:
            self.xplane_server_append_to_dataref_address_and_value_list(dataref_name, dataref, dataref_index, dataref_address, dataref_type, is_dataref_writable, dataref_value)
            message['message'] = 'the dataref value has been successfully obtained'
        else:
            message['message'] = 'dataref is not found'

        outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
        self.shared_data_container.outb += outgoing_message.encode('utf-8')                    

    def xplane_server_process_request_initialization_done(self):
        '''
        When the initialization is completed, start a thread for any update in x-plane dataref. 

        Context:
        As soon as we press a button in x-plane aircraft (dataref chages), send the value to Touch Portal. 
        The purpose of this is to have the same buttons state on both sides (airplane in X-Plane vs Touch-Portal panel).
        '''
        #print('xplane_server_process_request_initialization_done')
        message = {}
        message['command'] = self.response_initialization_done
        message['message'] = 'X-Plane server will now monitoring for updates from x-plane'
        outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
        self.shared_data_container.outb += outgoing_message.encode('utf-8')                    
        
        # Start the update process from x-plane dataref (just the dataref inside dataref_address_and_value_list)
        self.update_running.set()

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
        print("xplane_server_write_a_dataref")
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

    def xplane_server_process_request_update_from_touch_portal(self, dataref, value):
        '''
        Process Touch Portal client update command. 
        Update X-Plane by searching in the associative array and obtaining its address.

        Context:
        If a user presses a button in Touch Portal, a command is sent to the xplane server to update his dataref. 
        The purpose of this is to have the same buttons state on both sides (airplane in X-Plane vs Touch Portal).
        '''
        #print('xplane_server_process_request_update_from_touch_portal')

        dataref_address, dataref_type, dataref_index = self.xplane_server_get_dataref_address_type_and_index(dataref)

        message = {}
        message['command'] = self.response_update_from_touch_portal

        if dataref_address != None:
            is_valid, transform_value = self.xplane_server_is_valid_value(dataref_type,value)
            if is_valid:
                if self.xplane_server_write_a_dataref(dataref_address,dataref_type,dataref_index,transform_value):
                    message['message'] = 'successful dataref update'
                    self.xplane_server_update_dataref_address_and_value_list(dataref,transform_value)
                else:
                    message['message'] = 'unknown dataref\'s type'
            else:
                message['message'] = 'the dataref\'s value is wrong according to the dataref\'s type'

            outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
            self.shared_data_container.outb += outgoing_message.encode('utf-8')                    

    def xplane_server_managing_received_data(self, message_decode):
        '''
        Process the received data packet from the x-plane server client
        '''
        message_object = json.loads(message_decode)
        print(f'message_object = {message_object}')
        keys = list(message_object.keys())
        keys.sort()

        # Process a request from the x-plane server client for the initialization part
        if message_object['command'] == self.request_dataref_value and keys == self.request_dataref_value_paquet:
            self.xplane_server_process_request_dataref_value(message_object['dataref'])

        # Process a request from the x-plane server client when the initialization part is finish
        elif message_object['command'] == self.request_initialization_done and keys == self.request_initialization_done_paquet:
            self.xplane_server_process_request_initialization_done()
        
        # Process a request fron the x-plane server client when a dataref value has been updated in Touch Portal.
        # This following does nothing if the plugin publishing the dataRef is disabled, the dataRef is invalid, 
        # This following does nothing if the plugin publishing the dataRef is disabled, the dataRef is invalid, 
        # or the dataRef is not writable
        elif message_object['command'] == self.request_update_from_touch_portal and keys == self.request_update_from_touch_portal_paquet:
            self.xplane_server_process_request_update_from_touch_portal(message_object['dataref'],message_object['value'])
        
        elif message_object['command'] == self.response_update_from_x_plane  and keys == self.response_update_from_x_plane_paquet:
            print(f'response_update_from_x_plane_paquet {message_object["message"]}')

        else:
            command = message_object['command']
            print(f'This response is not part of the communication chart between the \n X-Plane client and the X-Plane server.\nThe following command has been rejected\n{command}' )

    def xplane_server_socket_die(self, client_socket):
        '''
        Close connections and remove socket objects from selectors
        '''
        print(f'A client close a socket, Closing client connection to {client_socket.getpeername()}')
        self.server_selectors.unregister(client_socket)
        client_socket.close()
        self.client_socket_list.remove(client_socket)

    def xplane_server_accept_wrapper(self):
        ''' 
        Accept connection from client
        '''
        client_socket, client_address = self.server_socket.accept()  # Should be ready to read
        self.client_socket_list.append(client_socket)
        # Unblocking socket
        self.client_socket.setblocking(False)
        # Register a file object for selection, monitoring it for I/O events
        self.client_selectors.register(self.client_socket, selectors.EVENT_READ | selectors.EVENT_WRITE, data=self.shared_data_container)
        print(f'X-Plane client connected: connection {client_address}')

    def xplane_server_monitoring_dataref_updates_from_xplane(self, client_socket):
        '''
        This is the process for updates from X-Plane. 
        When a user presses a key or a command in the simulated aircraft, the dataref associated with that key is updated. 
        We then check, in this loop, if any changes have been made to the datarefs. Send any update to the Touch Portal client.
        '''
        if self.update_running.is_set():
            
            for dataref in self.dataref_address_and_value_list:
                dataref_value = self.xplane_server_read_a_dataref(dataref['address'],dataref['type'],dataref['index'])

                # if the last value contained in the dataref's list is not equal 
                # to the x-plane dataref's value, this means a user has pressed a command on the x-plane side. 
                # Send this new value to Touch-Portal
                if dataref['value'] != dataref_value:
                    # update the dataref's associative array  
                    dataref['value'] = dataref_value

                    print(f'{datetime.now()}')
                    print(f'update_loop a value change for {dataref["full_name"]}')
                    # returning the new value to the X-Plane client for Touch Portal
                    message = {}
                    message['command'] = self.request_update_from_x_plane
                    message['dataref'] = dataref['full_name']
                    message['value'] = str(dataref_value)
                    outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
                    self.shared_data_container.outb += outgoing_message.encode('utf-8')                    

    def xplane_server_service_connection(self, key, mask):
        '''
        Manage Read event for selectors and receive ingoing data
        Also, monitoring dataref updates from x-plane
        '''
        client_socket = key.fileobj
        data = key.data # data is a reference to the self.shared_data_container object

        if mask & selectors.EVENT_READ:
            try:
                ingoing_message = client_socket.recv(1024)  # Should be ready to read
            except BlockingIOError:
                pass                                     # Resource temporarily unavailable (errno EWOULDBLOCK)
            except ConnectionResetError:
                print('ConnectionResetError !!!')
                self.xplane_server_socket_die(client_socket)
            except:
                raise                                    # No connection
            else:
                if ingoing_message:
                    data.inb += ingoing_message
                    # Each command contain a MESSAGE_DELIMITER at the end. Easy for separate commands
                    while MESSAGE_DELIMITER.encode('utf-8') in data.inb:
                        pos = data.inb.index(bytes(MESSAGE_DELIMITER, 'utf-8'))
                        message_bytes  = data.inb[:pos]  # The first message
                        data.inb = data.inb[pos+1:]  # Remove the first message from data.inb (message+'#')
                        message_decode = message_bytes.decode('utf-8') 
                        self.xplane_server_managing_received_data(message_decode)
                else:
                    print('Else if ingoing_message')
                    self.xplane_server_socket_die(client_socket)

        if mask & selectors.EVENT_WRITE:
            try:
                if data.outb:
                    print(f"Send {data.outb} à {data.addr}")
                    sent = server_socket.send(data.outb)  
                    data.outb = data.outb[sent:]
                else:    
                    self.xplane_server_monitoring_dataref_updates_from_xplane(client_socket) # This is the process for updates from X-Plane.
            except socket.error:
                    self.xplane_server_socket_die(client_socket) # possibly the client socket is close and the server try to send something 

    def xplane_server_main_loop(self, sinceLast, elapsedTime, counter, refCon): 
        '''
        This is the Flight Loop for server purpose
        '''
        
        # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in self.server_selectors.select(timeout=0.1):
            if key.data is None:
                self.xplane_server_accept_wrapper()
            else:
                self.xplane_server_service_connection(key, mask)

        return 1

    def xplane_server_shutting_down(self):
        '''
        Processing the server closure procedure
        '''
        print('xplane_server_shutting_down: threat unclosed client socket')

        # going through the client socket,  in case there are some unclosed
        for client_socket in list(self.client_socket_list):
            self.server_selectors.unregister(client_socket)
            client_socket.close()
            self.client_socket_list.remove(client_socket)

        self.server_selectors.close()