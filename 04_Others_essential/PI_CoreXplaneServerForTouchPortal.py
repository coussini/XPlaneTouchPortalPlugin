import xp
import selectors
import socket
import json
import threading
import types

class PythonInterface:

    def __init__(self):
        self.name = 'Core Xplane Server For Touch Portal'
        self.sig = 'core.xplane.server.for.touch.portal'
        self.desc = 'An Xplane Server For Touch Portal'
        self.acf_ui_name  = None
        self.start_program = False
        # Create an instance of a server for xplane
        host = socket.gethostbyname(socket.gethostname())
        port = 65432
        self.serv_xp = ServerXP(host, port)
        self.serv_xp.keep_running.set()

    def XPluginStart(self):
        return self.name, self.sig, self.desc

    def XPluginStop(self):
        pass

    def XPluginEnable(self): 
        return 1

    def XPluginDisable(self):
        pass

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        if inMessage == xp.MSG_AIRPORT_LOADED and inParam == 0:
            dataref_name = 'sim/aircraft/view/acf_ui_name'
            dataref_index = None
            dataref_address,dataref_type,is_dataref_writable,dataref_value = self.get_dataref_address_type_value(dataref_name,dataref_index)
            if self.acf_ui_name  != dataref_value:
                self.acf_ui_name  = dataref_value # keep the aircraft name to check if the user change the aircraft
                self.start_program = self.start_the_program(self.acf_ui_name)

class ServerXP:
    
    def __init__(self, host, port):
        self.sel = selectors.DefaultSelector()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.host = socket.gethostbyname(socket.gethostname())
        #self.port = 65432
        self.host = host
        self.port = port
        self.keep_running = threading.Event()
        # self.namespace_data will contain the key.data for a client socket,  
        self.namespace_data = types.SimpleNamespace()

    def setup(self):
        self.sock.bind((self.host, self.port))
        # queue upto max 6 connection requests
        self.sock.listen(6)
        print(f'Listening on {(self.host, self.port)}')
        self.sock.setblocking(False)
        self.sel.register(self.sock, selectors.EVENT_READ, data=None)

    def run(self):
        # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in self.sel.select(timeout=0.1):
            if key.data is None:
                # from the listening socket 
                self.accept_wrapper()
            else:
                # from the client socket 
                self.service_connection(key, mask)

    def accept_wrapper(self):
        conn, addr = self.sock.accept()  # Should be ready to read
        print(f'Accepted connection from {addr}')
        conn.setblocking(False)
        setattr(self.namespace_data,'addr',addr)
        setattr(self.namespace_data,'inb',b'')
        setattr(self.namespace_data,'outb',b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=self.namespace_data)

    def service_connection(self, key, mask):
        # client socket
        #
        # ATTENTION, LE sock  PEUT ÊTRE LE CONN LORS DE L'ACCEPT (on peut le mettre dans les attributs de la classe genre self.conn)
        #
        sock = key.fileobj
        self.namespace_data = key.data # use the simple name spaces 'self.namespace_data', created in accept wrapper
        
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                self.managing_received_data(recv_data)
            else:
                print(f'Closing connection to {self.namespace_data.addr}')
                self.sel.unregister(sock)
                sock.close()
        
        if mask & selectors.EVENT_WRITE:
            if self.namespace_data.outb:
                print(f'Echoing {self.namespace_data.outb!r} to {self.namespace_data.addr}')
                # sent value is the length of the string that was sent
                sent = sock.send(self.namespace_data.outb)  
                # remove the sent string from the self.namespace_data.outb
                self.namespace_data.outb = self.namespace_data.outb[sent:]    

    def shutting_down(self):
        self.sel.close()

    def managing_received_data(self, recv_data):
        # transforming byte to json format
        recv_data_json = json.loads(recv_data.decode())
        # process the received information
        send_data = self.reception(recv_data_json)
        # prepare the answer to the client by transforming json to byte format
        send_data_byte = json.dumps(send_data).encode()
        self.namespace_data.outb += send_data_byte

    def reception(self, data):
        send_data = None
        command = data['command']
        
        match command:
            case 'init':
                send_data = self.init_command(data)
            case 'write':
                send_data = self.write_command(data)
            case 'update':
                pass
                # start a thread to read
                #send_data = self.update_command(data)
            case _:
                print('This command is not recognized by the server')

        return send_data

    def init_command(self, data):

        print('--> INIT section')
        for x in data['datarefs']:
            dataref_name,dataref_index = self.get_dataref_name_and_index(x['dataref'])
            print(f'Dataref name = {dataref_name} and dataref index = {dataref_index}')
            x['value'] = str(random.randrange(0,5))

        return data

    def write_command(data):
        print('--> WRITE section')

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

        return dataref_name,dataref_index 

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

    def read_a_dataref(self,dataref_address,dataref_type,dataref_index):

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

    def start_the_program(self,aircraft_name):

        print(f'')
        print(f'Load Aircraft name:{aircraft_name}')

        # Adirs IR1, BAT1, Strobe
        dataref_list = [
        'AirbusFBW/ElecOHPArray[5]',
        'AirbusFBW/ElecOHPArray[6]',
        'AirbusFBW/ElecOHPArray[3]',
        'AirbusFBW/PanelFloodBrightnessLevel',
        'sim/flightmodel/position/elevation',
        'AirbusFBW/RMP3Lights[0]',
        'AirbusFBW/OHPLightSwitches[7]'
        ]
        
        for dataref in dataref_list:
            dataref_name,dataref_index = self.get_dataref_name_and_index(dataref)
            dataref_address,dataref_type,is_dataref_writable,dataref_value = self.get_dataref_address_type_value(dataref_name,dataref_index)
            #print(dataref_type,dataref_value)
            if (dataref_type is None and dataref_value is None):
                print(f'')
                print(f'The {self.acf_ui_name} does not correspond to your touch portal page!')
                print(f'')
                return False
            #print(f'For dataref : {dataref} the type is {dataref_type}, the value is {dataref_value} and is writable ? {is_dataref_writable}')
            #return_value = self.write_a_dataref(dataref_address,dataref_type,dataref_index,1)
        print(f'')
        print(f'The {self.acf_ui_name} is ready for your touch portal page!')
        print(f'')
        return True
