import xp
import socket

class PythonInterface:
    ''' 
    [0]
    '''
    def __init__(self):
        xp.log("__init__") 
        self.Name = "PI_SERVER"
        self.Sig = "server.for.touchportal.and.xplane"
        self.Desc = "Server for Touch Portal and X-Plane (non blocking)"
        
        # Create a UDP socket
        self.ServerSocketUDP = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.ServerSocketUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ServerSocketUDP.settimeout(1)
        # Bind the socket to the port
        self.HOST = socket.gethostbyname(socket.gethostname())
        self.PORT = 65432
        self.ServerSocketUDP.bind((self.HOST, self.PORT))

    ''' 
    [1]
    '''
    def XPluginStart(self):
        xp.log("XPluginStart")
        xp.log("Mediator PLugin Start") 
        self.FlightLoopID = xp.createFlightLoop(self.handle_connection,0,None)
        xp.log(f"(FlightLoopID Adress: {self.FlightLoopID})") 
        return self.Name, self.Sig, self.Desc

    def handle_connection(self, sinceLast, elapsedTime, counter, refCon):
        try:
            bytesAddressPair = self.ServerSocketUDP.recvfrom(1024)
            self.ServerSocketUDP.settimeout(1)
        except socket.error:
            pass
        else:
            print(bytesAddressPair)
        try:
            bytesAddressPair = self.ServerSocketUDP.recvfrom(1024)
        except socket.error:
            pass
        else:
            message = bytesAddressPair[0]
            address = bytesAddressPair[1]
            clientMsg = "Message from Client:{}".format(message)
            clientIP  = "Client IP Address:{}".format(address)
            xp.log(clientMsg)
            xp.log(clientIP)
            # Sending a reply to client
            msgFromServer = "Hello UDP Client"
            bytesToSend = str.encode(msgFromServer)
            self.ServerSocketUDP.sendto(bytesToSend, address)

    '''
    [2]
    '''
    def StartFlightLoop(self,menuRefCon,itemRefCon):
        print("StartFlightLoop print UDP Server for Touch Portal and X-Plane up and listening")
        xp.log("xplog UDP Server for Touch Portal and X-Plane up and listening")
        xp.speakString(f"Menu {menuRefCon} selected")
        #xp.scheduleFlightLoop(self.FlightLoopID,1,1)


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
        
        pass

    '''
    [5]
    '''
    def XPluginStop(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginStop") 
        
        pass