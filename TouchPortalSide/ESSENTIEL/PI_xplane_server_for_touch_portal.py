### Isoler la petite lenteur avant que le test de serveur fonctionne
### Une fois partie.... Il n'y a pas de lenteur quand on touche les boutons

import xp
import selectors
import socket
import json
import threading
import types

class PythonInterface:

    def __init__(self):
        self.name = 'Xplane Server For Touch Portal'
        self.sig = 'xplane.server.for.touch.portal'
        self.desc = 'An Xplane Server For Touch Portal'
        
        # keep the aircraft name to check if the user change the aircraft
        self.acf_ui_name  = None
        
        # Create an instance of a server for xplane
        host = socket.gethostbyname(socket.gethostname())
        port = 65432
        self.server_xp = ServerXP(host, port)
        self.server_loop_id = xp.createFlightLoop(self.server_xp.server_loop,0,None)

    def XPluginStart(self):
        return self.name, self.sig, self.desc

    def XPluginStop(self):
        pass

    def XPluginEnable(self): 
        return 1

    def XPluginDisable(self):
        del self.xpdh
        xp.destroyFlightLoop(self.server_loop_id)
        print('shutting down')
        self.server_xp.keep_running.clear()
        self.server_xp.shutting_down()
        del self.server_xp

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        if inMessage == xp.MSG_AIRPORT_LOADED and inParam == 0:
            # Create an instance for accessing X-Plane dataref
            self.xpdh = XPDatarefHandle()
            dataref_address,dataref_type,is_dataref_writable,dataref_value = self.xpdh.get_dataref_address_type_value(self.xpdh.dataref_name, self.xpdh.dataref_index)
            if self.acf_ui_name  != dataref_value:
                self.acf_ui_name  = dataref_value # keep the aircraft name to check if the user change the aircraft
                if self.server_xp.keep_running.is_set():
                    pass
                else:
                    print("------------------> here")
                    self.server_xp.keep_running.set()
                    self.server_xp.preparing_running()
                    xp.scheduleFlightLoop(self.server_loop_id,1,1)

class ServerXP:
    
    def __init__(self, host, port):
        self.server_selectors = selectors.DefaultSelector()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = host
        self.port = port
        self.keep_running = threading.Event()
        self.outgoing_data = types.SimpleNamespace()
        self.client_socket_list = []

    def preparing_running(self):
        self.server_socket.bind((self.host, self.port))
        print(f'Listening on {(self.host, self.port)}')
        # upto max 6 connection requests
        self.server_socket.listen(6)
        # unblocking socket
        self.server_socket.setblocking(False)
        # register a file object for selection, monitoring it for I/O events
        self.server_selectors.register(self.server_socket, selectors.EVENT_READ, data=None)

    def run(self):
        # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in self.server_selectors.select(timeout=0.1):
            if key.data is None:
                self.accept_wrapper()
            else:
                self.service_connection(key, mask)

    def accept_wrapper(self):
        client_socket, client_address = self.server_socket.accept()  # Should be ready to read
        self.client_socket_list.append(client_socket)
        print(f'X-Plane client connected: connection {client_address}')
        #client_socket.setblocking(False)
        setattr(self.outgoing_data,'outb',b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.server_selectors.register(client_socket, events, data=self.outgoing_data)

    def service_connection(self, key, mask):
        client_socket = key.fileobj
        self.outgoing_data = key.data # use the simple name spaces 'self.outgoing_data', created in accept wrapper

        if mask & selectors.EVENT_READ:
            try:
                # Should be ready to read
                ingoing_data = client_socket.recv(1024)
            except BlockingIOError:
                pass  # Resource temporarily unavailable (errno EWOULDBLOCK)
            except ConnectionResetError:
                self.socket_die(client_socket)
            except:
                raise  # No connection
            else:
                if ingoing_data:
                    self.managing_received_data(client_socket, ingoing_data)
                else:
                    self.socket_die(client_socket)

        if mask & selectors.EVENT_WRITE:
            if self.outgoing_data.outb:
                print(f'send_data = {self.outgoing_data.outb!r} to {client_socket.getpeername()}')
                # sent value is the length of the string that was sent
                sent = client_socket.send(self.outgoing_data.outb)  
                # remove the sent string from the self.outgoing_data.outb
                self.outgoing_data.outb = self.outgoing_data.outb[sent:]    

    def socket_die(self, client_socket):
        print(f'Closing connection to {client_socket.getpeername()}')
        self.server_selectors.unregister(client_socket)
        client_socket.close()
        self.client_socket_list.remove(client_socket)

    def shutting_down(self):
        # in case there are some unclosed client socket
        print('threat unclosed client socket')
        for client_socket in list(self.client_socket_list):
            self.server_selectors.unregister(client_socket)
            client_socket.close()
            self.client_socket_list.remove(client_socket)

        self.server_selectors.close()

    def managing_received_data(self, client_socket, ingoing_data):
        print(f'ingoing_data = {ingoing_data} to {client_socket.getpeername()}')
        # echoing data
        self.outgoing_data.outb += ingoing_data
    
    def server_loop(self, sinceLast, elapsedTime, counter, refCon):
        if self.keep_running.is_set():
            self.run()
            # call server_loop again after 1 second
            return 1

class XPDatarefHandle:
    
    def __init__(self):

        self.dataref_name = 'sim/aircraft/view/acf_ui_name'
        self.dataref_index = None

    def get_dataref_name_and_index(self, dataref):
        
        """
        receive a dataref from a JSON
        theres following examples of dataref names including or not an index
        'sim/aircraft/electrical/num_batteries'
        'sim/multiplayer/combat/team_status[3]' the index is 3
        """

        dataref_index = None 
        dataref_name = dataref.replace('[',' ')
        dataref_name = dataref_name.replace(']',' ')
        dataref_name = dataref_name.split()

        # it's a dataref with an index
        if len(dataref_name) == 2: 
            dataref_index = dataref_name[1]
            dataref_name = dataref_name[0]
        
        # it's not a dataref with an index
        else: 
            dataref_name = dataref_name[0]

        return dataref_name, dataref_index 

    def get_dataref_address_type_value(self, dataref_name, dataref_index):
        
        """ receive a dataref including or not an index """

        dataref_type = None
        is_dataref_writable = False
        dataref_value = None

        # comment from X-Plane: findDataRef function is relatively expensive; save the result. 
        # Do not repeat a lookup every time you need to read or write it.
        dataref_address = xp.findDataRef(dataref_name)
        
        if dataref_address != None:
            dataref_type = xp.getDataRefTypes(dataref_address)
            is_dataref_writable = xp.canWriteDataRef(dataref_address)
            dataref_value = self.read_a_dataref(dataref_address,dataref_type,dataref_index)
        
        return dataref_address,dataref_type,is_dataref_writable,dataref_value

    def read_a_dataref(self, dataref_address,dataref_type, dataref_index):

        """ read a dataref according to it's address, type and index """

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

    def write_a_dataref(self,dataref_address,dataref_type,dataref_index,dataref_value):

        """ write a dataref according to it's address, type, index and value """

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