#!/usr/bin/env python3
import json
import random  # temporary
import selectors
import socket
import threading
import types
import xp

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
        self.update_thread_keep_running = threading.Event()
        self.outgoing_data = types.SimpleNamespace()
        self.client_socket_list = []
        self.server_loop_id = xp.createFlightLoop(self.server_xp.server_loop,0,None)
        self.dataref_address_and_value = {}


    def socket_die(self, client_socket):
        '''
        Close connections and remove socket objects from selectors
        '''
        print(f'Closing connection to {client_socket.getpeername()}')
        self.server_selectors.unregister(client_socket)
        client_socket.close()
        self.client_socket_list.remove(client_socket)

    def separate_data_received(self, ingoing_data):
        '''
        Process and separate data received from touch portal client. 
        We can receive several commands in one data reception. 
        That's why we need to separate the commands and put them in ingoint_list
        '''
        new = ''
        ingoing_list = []

        for char in ingoing_data:
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

    def get_dataref_name_and_index(cls,dataref):
        """
        Separate name and index of received dataref string

        Exemple for a dataref parameter contaning "AirbusFBW/OHPLightSwitches[9]"
            dataref_name  = AirbusFBW/OHPLightSwitches
            dataref_index = 9

        Exemple for a dataref parameter contaning "AirbusFBW/PanelFloodBrightnessLevel"
            dataref_name  = AirbusFBW/PanelFloodBrightnessLevel
            dataref_index = None
        """
        dataref_index = None 
        dataref_name = dataref.replace("["," ")
        dataref_name = dataref_name.replace("]"," ")
        dataref_name = dataref_name.split()

        # it's a dataref with an index
        if len(dataref_name) == 2: 
            dataref_index = dataref_name[1]
            dataref_name = dataref_name[0]
        
        # it's not a dataref with an index
        else: 
            dataref_name = dataref_name[0]

        return dataref_name,dataref_index 

    def read_a_dataref(self,dataref_address,dataref_type,dataref_index):
        """ 
        Read a dataref according to it's address, type and index 
        """
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

    def is_int(self,dataref_value):
        """ 
        Validate the received dataref's value according to int

        """

        try:
            int(dataref_value)
            return True
        except ValueError:
            return False

    def is_float_or_double(self,dataref_value):
        """ 
        Validate the received dataref's value according to float or double
         
        """

        try:
            float(dataref_value)
            return True
        except ValueError:
            return False

    def is_valid_value(self,dataref_type,dataref_value):
        """ 
        Validate the received dataref's value according to the dataref's type 
        """
        if bool(dataref_type & xp.Type_Int):
            return is_int(dataref_value) 
        
        elif bool(dataref_type & xp.Type_Float):
            return is_float_or_double(dataref_value) 
        
        elif bool(dataref_type & xp.Type_Double):
            return is_float_or_double(dataref_value) 
        
        elif bool(dataref_type & xp.Type_FloatArray):
            return is_float_or_double(dataref_value) 
        
        elif bool(dataref_type & xp.Type_IntArray):
            return is_int(dataref_value) 

        else 
            return False


    def write_a_dataref(self,dataref_address,dataref_type,dataref_index,dataref_value):
        """ 
        Write a dataref according to it's address, type, index and value 
        """
        print(dataref_type,xp.Type_Unknown)
        
        if bool(dataref_type & xp.Type_Unknown):
            return False
        
        elif bool(dataref_type & xp.Type_Int):
            xp.setDatai(dataref_address,dataref_value) 
        
        elif bool(dataref_type & xp.Type_Float):
            xp.setDataf(dataref_address,dataref_value) 
        
        elif bool(dataref_type & xp.Type_Double):
            xp.setDatad(dataref_address,dataref_value) 
        
        elif bool(dataref_type & xp.Type_FloatArray):
            xp.setDatavf(dataref_address, [dataref_value], int(dataref_index), 1)
        
        elif bool(dataref_type & xp.Type_IntArray):
            xp.setDatavi(dataref_address, [dataref_value], int(dataref_index), 1)
        
        elif bool(dataref_type & xp.Type_Data):
            xp.setDatas(dataref_address) # Data
        
        else:
            return False

        return True

    def get_dataref_address_type_value(self,dataref_name,dataref_index):
        
        """ 
        The following data will be obtained within dataref name and dataref index:
            -The address of the dataref read: we'll keep this address for greater access efficiency.  
            -The type of dataref: can be Int, Float, Double, FloatArray, IntArray and Data.
            -Whether or not if this dataref is writable.
            -The value of the dataref
        """

        dataref_type = None
        is_dataref_writable = False
        dataref_value = None

        # Note: findDataRef function is relatively expensive. For this reason, we'll save the dataref address in an array 
        dataref_address = xp.findDataRef(dataref_name)
        
        if dataref_address != None:
            dataref_type = xp.getDataRefTypes(dataref_address)
            is_dataref_writable = xp.canWriteDataRef(dataref_address)
            dataref_value = self.read_a_dataref(dataref_address,dataref_type,dataref_index)
        
        return dataref_address,dataref_type,is_dataref_writable,dataref_value

    def process_init_command(self,dataref):
        '''
        Process touch portal client initialization command. 

        Next, the program will store the dataref's data in an associative array, wich will used during the update. 
        The update will use the dataref's address (stored during initialization) to update its value.

        Context:
        As soon as we display a touch-portal page and its buttons, we need to obtain the button values (associated with a dataref). 
        The purpose of this is to have the same buttons state on both sides (airplane in X-Plane vs Touch-Portal panel).
        '''
        print("init command")
        dataref_name,dataref_index = self.get_dataref_name_and_index(dataref)
        print(f"dataref_name & dataref_index {dataref_name} & {dataref_index}")
        dataref_address,dataref_type,is_dataref_writable,dataref_value = self.get_dataref_address_type_value(dataref_name,dataref_index)

        result = {}
        result["command"] = "result_init"
        result["dataref"] = dataref
        result["value"] = dataref_value

        if dataref_address != None:
            # add this dataref in internal associative array
            new_dataref = {
                'name': dataref_name, 
                'full_name': dataref, 
                'index': dataref_index,
                'address': dataref_address, 
                'type': dataref_type,
                'is_writable': is_dataref_writable, 
                'value': dataref_value
            }    
            self.dataref_address_and_value.append(new_dataref)

            result["message"] = "successful dataref update"
        else
            result["message"] = "dataref is not found"

        return result

    def thread_function(self):
       
        print("init_completed command")
        result = {}
        result["command"] = "result_init_completed"
        result["message"] = "X-Plane server thread will be started soon"
        self.outgoing_data.outb += json.dumps(result).encode()
        self.update_thread_keep_running.set()
        
        while self.update_thread_keep_running.is_set():
            for dataref in dataref_address_and_value:
                dataref_value = self.read_a_dataref(dataref['address'],dataref['type'],dataref['index'])

                # if the last value contained in the dataref's associative array is not equal 
                # to the x-plane dataref's value, this means a user has pressed a command on the x-plane side. 
                # Send this new value to Touch-Portal
                if dataref['value'] != dataref_value:
                    # returning the new value to the X-Plane client for Touch Portal
                    result = {}
                    result["command"] = "result_update"
                    result["dataref"] = dataref['full_name']
                    result["value"] = dataref_value
                    result["message"] = "X-Plane server update a value"
                    self.outgoing_data.outb += json.dumps(result).encode()
                    # update the dataref's associative array  
                    dataref['value'] = dataref_value

    def treat_update_from_here_for_xplane_client(self):
        '''
        Check every second if the user press a command on the X-plane side. 
        Then, send the updated data to refresh the Touch Portal status and screen.  

        Context:
        If a user presses a button in x-plane, a command is sent to the Xplane client for Touch Portal to update the Touch Portal states. 
        The purpose of this is to have the same buttons state on both sides (airplane in X-Plane vs Touch-Portal).
        '''

        print("starting X-Plane client thread")
        self.update_thread_keep_running.set()

        try:
            xp_thread = threading.Thread(target=self.thread_function, args=(), daemon=True)
            xp_thread.start()
        except:
            self.update_thread_keep_running.clear()
            print('something wrong with X-Plane server thread')


    def process_init_completed_command(self):
        '''
        The server will start a thread to check every second if the user press a command on the X-plane side. 
        '''

        # Start a thread to treat any update from the x-plane server. This thread will finish when X-Plane Server are close
        self.treat_update_from_here_for_xplane_client()

    def process_update_command(self,dataref,value):
        '''
        Process touch portal client update command. 
        Update X-Plane by searching in the associative array and obtaining its address.

        Context:
        If a user presses a button in touch portal, a command is sent to the xplane server to update his dataref. 
        The purpose of this is to have the same buttons state on both sides (airplane in X-Plane vs Touch-Portal).
        '''
        print("update command")
        dataref_name,dataref_index = self.get_dataref_name_and_index(dataref)

        dataref_address = None
        # search in the associative array for the dataref's address
        for dataref in dataref_address_and_value:
            if dataref['name'] == dataref_name and dataref['index'] == dataref_index:
                dataref_address = dataref['address']
                break

        result = {}
        result["command"] = "result_update"
        result["dataref"] = dataref

        if dataref_address != None:
            if self.is_valid_value(dataref_type,dataref_value)
                if self.write_a_dataref(dataref_address,dataref_type,dataref_index,dataref_value):
                    result["message"] = "successful dataref update"
                else:
                    result["message"] = "unkonw dataref's type"
            else
                result["message"] = "the dataref's value is wrong according to the dataref's type"

        return result
              
    def managing_received_data(self, client_socket, ingoing_data):
        '''
        Process the received data packet
        '''
        ingoing_data_paquet = self.separate_data_received(ingoing_data.decode())

        # Process each command coming from a data packet
        for one_ingoing in ingoing_data_paquet: 
            print(f'ingoing_data = {one_ingoing} to {client_socket.getpeername()}')
            print(f'')
            print(f'type one_ingoing {type(one_ingoing)}')
            one_ingoing_load = json.loads(one_ingoing)
            
            if one_ingoing_load["command"] == 'init':
                # Add the value for the outgoing data
                result = self.process_init_command(one_ingoing_load["dataref"])
            elif one_ingoing_load["command"] == 'init_completed':
                # The server will start a thread to check every second if the user press a command on the X-plane side. 
                # Then, with this thread, the server will send the updated data to refresh the Touch Portal status and screen.  
                pass
            elif one_ingoing_load["command"] == 'update':
                # This following does nothing if the plugin publishing the dataRef is disabled, the dataRef is invalid, 
                # or the dataRef is not writable
                result = self.process_update_command(one_ingoing_load["dataref"],one_ingoing_load["value"])
            
            # returning result of the command
            self.outgoing_data.outb += json.dumps(result).encode()

    def run(self):
        '''
        This is the master function for processing sockets, selectors, received data and data to be sent.
        '''
        
        # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in self.server_selectors.select(timeout=0.1):
            if key.data is None:
                client_socket, client_address = self.server_socket.accept()  # Should be ready to read
                self.client_socket_list.append(client_socket)
                print(f'X-Plane client connected: connection {client_address}')
                #client_socket.setblocking(False)
                setattr(self.outgoing_data,'outb',b'')
                events = selectors.EVENT_READ | selectors.EVENT_WRITE
                self.server_selectors.register(client_socket, events, data=self.outgoing_data)
            else:
                client_socket = key.fileobj
                self.outgoing_data = key.data # use the simple name spaces 'self.outgoing_data', created previously

                if mask & selectors.EVENT_READ:
                    try:
                        ingoing_data = client_socket.recv(4096)  # Should be ready to read
                    except BlockingIOError:
                        pass                                     # Resource temporarily unavailable (errno EWOULDBLOCK)
                    except ConnectionResetError:
                        self.socket_die(client_socket)
                    except:
                        raise                                    # No connection
                    else:
                        if ingoing_data:
                            self.managing_received_data(client_socket, ingoing_data)
                        else:
                            self.socket_die(client_socket)

                if mask & selectors.EVENT_WRITE:
                    if self.outgoing_data.outb:
                        sent = client_socket.send(self.outgoing_data.outb)  
                        self.outgoing_data.outb = self.outgoing_data.outb[sent:] # remove the sent string from the self.outgoing_data.outb    

    def shutting_down(self):
        '''
        Processing the server closure procedure
        '''
        print('threat unclosed client socket')

        # going through the client socket,  in case there are some unclosed
        for client_socket in list(self.client_socket_list):
            self.server_selectors.unregister(client_socket)
            client_socket.close()
            self.client_socket_list.remove(client_socket)

        self.server_selectors.close()

def main(): 
    '''
    X-plane Server processing for touch portal
    '''
    
    host = socket.gethostbyname(socket.gethostname())
    port = 65432
    
    server_xp = XPlaneServer(host,port)
    server_xp.keep_running.set()
    server_xp.preparing_running()
    server_xp.server_socket.bind((server_xp.host, server_xp.port))
    
    print(f'Listening on {(server_xp.host, server_xp.port)}')
    
    # upto max 6 connection requests
    server_xp.server_socket.listen(6)
    # unblocking socket
    server_xp.server_socket.setblocking(False)
    # register a file object for selection, monitoring it for I/O events
    server_xp.server_selectors.register(self.server_socket, selectors.EVENT_READ, data=None)

    try:
        while server_xp.keep_running.is_set():
            server_xp.run()
    except KeyboardInterrupt:
        server_xp.keep_running.clear()
        print('Caught keyboard interrupt, exiting')
    finally:
        print('shutting down')
        server_xp.shutting_down()

if __name__ == '__main__':
    main()
