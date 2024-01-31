import xp
import threading
import socket
import select

class PythonInterface:
    ''' 
    [0]
    '''
    def __init__(self):
        xp.log("__init__") 
        self.Name = "DatarefServer_NB"
        self.Sig = "dataref.server.nb.xppython3"
        self.Desc = "Serv and receive dataref data (non blocking)"
        
        self.Host = socket.gethostbyname(socket.gethostname())
        self.Port = 65432

    ''' 
    [1]
    '''
    def XPluginStart(self):
        xp.log("XPluginStart") 
        xp.log("(Initialize Server Socket)") 

        self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ServerSocket.setblocking(False)
        self.ServerSocket.bind((self.Host, self.Port))

        # List of sockets to be monitored by select
        self.SocketsToMonitor = [self.ServerSocket]

        return self.Name, self.Sig, self.Desc

    def handle_connection(self):
        while True:
            # Use select to get the list of sockets ready for reading
            ready_to_read, _, _ = select.select(self.SocketsToMonitor, [], [])
            for sock in ready_to_read:
                print("")
                print(f">>>>>>>>>>>>> ready_to_read : {ready_to_read}")
                print("")
                if sock == self.ServerSocket:
                    print("===============PARTIE SERVEUR===================")
                    print(f"server_socket : {sock}")
                    # A new client connection is ready to be accepted
                    self.client_socket, self.client_address = self.ServerSocket.accept()
                    print(f"Connected to client {self.client_address}")
                    sockets_to_monitor.append(self.client_socket)
                else:
                    print("")
                    print("===============PARTIE CLIENT===================")
                    print(f"client socket ? : {sock}")
                    print(f"server_socket ? : {self.ServerSocket}")
                    # An existing client sent data or closed the connection
                    data = sock.recv(1024)
                    print("")
                    print("===============DATA CLIENT===================")
                    print(f"client data ? : {data}")
                    if data:
                        print(f"Received data from client {self.client_address}: {data}")
                        # echo send data to client
                        #sock.sendall(data)
                    else:
                        print(f"Connection closed by client {self.client_address}")
                        sock.close()
                        self.SocketsToMonitor.remove(sock)

    def flight_loop(self,refCon):
        while True:
            # Use select to get the list of sockets ready for reading
            ready_to_read, _, _ = select.select(self.SocketsToMonitor, [], [])
            for sock in ready_to_read:
                print("")
                print(f">>>>>>>>>>>>> ready_to_read : {ready_to_read}")
                print("")
                if sock == self.ServerSocket:
                    print("===============PARTIE SERVEUR===================")
                    print(f"server_socket : {sock}")
                    # A new client connection is ready to be accepted
                    self.client_socket, self.client_address = self.ServerSocket.accept()
                    print(f"Connected to client {self.client_address}")
                    self.SocketsToMonitor.append(self.client_socket)
                else:
                    print("")
                    print("===============PARTIE CLIENT===================")
                    print(f"client socket ? : {sock}")
                    print(f"server_socket ? : {self.ServerSocket}")
                    # An existing client sent data or closed the connection
                    data = sock.recv(1024)
                    print("")
                    print("===============DATA CLIENT===================")
                    print(f"client data ? : {data}")
                    if data:
                        print(f"Received data from client {self.client_address}: {data}")
                        # echo send data to client
                        sock.sendall(data)
                    else:
                        print(f"Connection closed by client {self.client_address}")
                        sock.close()
                        self.SocketsToMonitor.remove(sock)

        return 1.0

    '''
    [2]
    '''

    def MyMenu(self,menuRefCon,itemRefCon):
        xp.speakString(f"Menu {menuRefCon} selected")

    def XPluginEnable(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginEnable")
        menuID = xp.createMenu(handler=self.MyMenu, refCon="Menu1")
        xp.appendMenuItem(menuID, "Item 1", refCon="Item1")
        #menuID = xp.createMenu("My Menu", handler=self.flight_loop, refCon=[])
        '''
        xp.log("(Server is ready to accept connections...)") 

        self.ServerSocket.listen()
        print(f"[LISTENING] Server is listening on {self.Host} and {self.Port}")

        self.FlightLoopID = xp.createFlightLoop(self.flight_loop, phase=1, refCon=None)
        xp.log(f"(FlightLoopID Adress: {self.FlightLoopID})") 
        # scheduleFlightLoop with parameter 1 to start only when the plane is loaded
        xp.scheduleFlightLoop(self.FlightLoopID, interval=1, relativeToNow=1)

        '''
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
        self.ServerSocket.close()
        pass

    '''
    [5]
    '''
    def XPluginStop(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginStop") 
        pass