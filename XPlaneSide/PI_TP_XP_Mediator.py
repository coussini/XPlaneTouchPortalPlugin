from XPPython3 import xp
import socket
import select
import json

class PythonInterface:
    ''' 
    [0]
    '''
    def __init__(self):
        xp.log("__init__") 
        self.Name = "PI_TP_XP_Mediator"
        self.Sig = "mediator.for.touchportal.and.xplane"
        self.Desc = "Mediator for Touch Portal and X-Plane (non blocking)"
        
        # Create a TCP/IP socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setblocking(False)
        # Bind the socket to the port
        self.HOST = socket.gethostbyname(socket.gethostname())
        self.PORT = 65432
        self.server_socket.bind((self.HOST, self.PORT))
        # List of sockets to be monitored by select
        self.sockets_to_monitor = [self.server_socket]

    ''' 
    [1]
    '''
    def XPluginStart(self):
        xp.log("XPluginStart")
        xp.log("Mediator PLugin Start") 

        self.server_socket.listen()
        xp.log(f"[LISTENING] Server is listening on {self.HOST}")
        self.FlightLoopID = xp.createFlightLoop(self.handle_connection,0,None)
        xp.log(f"(FlightLoopID Adress: {self.FlightLoopID})") 
        # scheduleFlightLoop with parameter 1 to start only when the plane is loaded
        #xp.scheduleFlightLoop(self.FlightLoopID,1,1)

        return self.Name, self.Sig, self.Desc

    def handle_connection(self, sinceLast, elapsedTime, counter, refCon):
        # Use select to get the list of sockets ready for reading
        ready_to_read, _, _ = select.select(self.sockets_to_monitor, [], [],0.5)

        for sock in ready_to_read:
            xp.log("")
            xp.log(f">>>>>>>>>>>>> ready_to_read : {ready_to_read}")
            xp.log("")
            if sock == self.server_socket:
                xp.log("===============PARTIE SERVEUR===================")
                xp.log(f"server_socket : {sock}")
                # A new client connection is ready to be accepted
                client_socket, client_address = self.server_socket.accept()
                xp.log(f"Connected to client {client_address}")
                self.sockets_to_monitor.append(client_socket)
            else:
                xp.log("")
                xp.log("===============PARTIE CLIENT===================")
                xp.log(f"client socket ? : {sock}")
                xp.log(f"server_socket ? : {self.server_socket}")
                # An existing client sent data or closed the connection
                data = sock.recv(1024)
                xp.log(f"received data ? : {data}")
                data_json = json.loads(data.decode())
                xp.log("")
                xp.log("===============DATA CLIENT===================")
                xp.log(f"client data dataref : {data_json['dataref']}")
                xp.log(f"client data type : {data_json['type']}")
                if data:
                    xp.log(f"Received data from client: {data}")
                    # echo send data to client
                    sock.sendall(data)
                else:
                    xp.log(f"Connection closed by client")
                    sock.close()
                    self.sockets_to_monitor.remove(sock)
        return 1

    '''
    [2]
    '''

    def StartFlightLoop(self,menuRefCon,itemRefCon):
        xp.scheduleFlightLoop(self.FlightLoopID,1,1)

    def XPluginEnable(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginEnable")
        menuID = xp.createMenu("TPXPServer",handler=self.StartFlightLoop, refCon="Menu1")
        xp.appendMenuItem(menuID, "Start TPXP Server", refCon="StartXPServer")
        return 1

    '''
    [3]
    '''
    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginReceiveMessage") 
        pass    

    '''
    [4]
    '''
    def XPluginDisable(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginDisable") 
        xp.destroyFlightLoop(self.FlightLoopID)
        self.server_socket.shutdown(socket.SHUT_RDWR)
        self.server_socket.close()        
        pass

    '''
    [5]
    '''
    def XPluginStop(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginStop") 
        pass