import xp
import socket
import select
import threading

# for x in dictio["datarefs"]:
#   whatIsType = xp.findDataRef(x["dataref"])
#   a = x["group"]

dictio = {
    "datarefs": [
        {
            "dataref": "AirbusFBW/ADIRUSwitchArray[0]",
            "desc": "Adirs IR1",
            "type": "int",
            "value": "0"
        },
        {
            "dataref": "AirbusFBW/ADIRUSwitchArray[1]",
            "desc": "Adirs IR2",
            "type": "int",
            "value": "0"
        }
    ]
}



class PythonInterface:

    def __init__(self):
        print("__init__") 
        self.Name = "PI_TCP_SERVER"
        self.Sig = "tcp.server.for.touchportal.and.xplane"
        self.Desc = "TCP Server for Touch Portal and X-Plane (non blocking)"
        
        # Create a TCP socket
        self.ServerSocketTCP = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.ServerSocketTCP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to the port
        self.HOST = socket.gethostbyname(socket.gethostname())
        self.PORT = 65432
        self.ServerSocketTCP.bind((self.HOST, self.PORT))
        self.ServerSocketTCP.listen(2)
        # Create a list of connections
        self.inputs = [self.ServerSocketTCP]
        self.outputs = []

    def XPluginStart(self):
        print("XPluginStart")
        self.FlightLoopID = xp.createFlightLoop(self.FlightLoopCallback,0,None)
        print(f"(FlightLoopID Adress: {self.FlightLoopID})") 
        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        print("XPluginStop") 

    def XPluginEnable(self):
        print("XPluginEnable")
        menuID = xp.createMenu("TPXPServer",handler=self.StartFlightLoop, refCon="Menu1")
        xp.appendMenuItem(menuID, "Start TPXP Server", refCon="StartXPServer")
        return 1

    def XPluginDisable(self):
        print("XPluginDisable") 
        xp.destroyFlightLoop(self.FlightLoopID)
        for connection in self.inputs:
            connection.close()
        #self.ServerSocketTCP.shutdown(socket.SHUT_RDWR)
        self.ServerSocketTCP.close()
        print("Server Closed") 

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass 

    def handle_client(self,client,address):
        request_bytes = client.recv(1024)
        if not request_bytes:
            print("Connection closed")
            client.close()
        request_str = request_bytes.decode()
        print(f"Data from client: {request_str}")
        msgFromServer = "Hello UDP Client"
        bytesToSend = str.encode(msgFromServer)
        client.sendall(bytesToSend)

    def StartFlightLoop(self,menuRefCon,itemRefCon):
        print("StartFlightLoop print UDP Server for Touch Portal and X-Plane up and listening")
        xp.speakString(f"Menu {menuRefCon} selected")
        print("ATTENTION ATTENTION ATTENTION")
        dataRef = xp.findDataRef("AirbusFBW/ADIRUSwitchArray")
        nb = xp.getDatavi(dataRef)
        values = []
        xp.getDatavi(dataRef, values, count=nb)
        print(values[0])
        print("ATTENTION ATTENTION ATTENTION")
        xp.scheduleFlightLoop(self.FlightLoopID,1,1)

    def FlightLoopCallback(self, sinceLast, elapsedTime, counter, refCon):
        print("inside FlightLoopCallback")
        readable, writable, exceptional = select.select(
        self.inputs, self.outputs, self.inputs, 0)
        for s in readable:
            if s is self.ServerSocketTCP:
                connection, client_address = s.accept()
                connection.setblocking(0)
                self.inputs.append(connection)
                threading.Thread(target=self.handle_client, args=(connection, client_address)).start()
        return 1.0