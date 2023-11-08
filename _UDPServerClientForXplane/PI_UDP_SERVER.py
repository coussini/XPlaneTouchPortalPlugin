import xp
import socket
import os

class PythonInterface:

    def __init__(self):
        xp.log("__init__") 
        self.Name = "PI_UDP_SERVER"
        self.Sig = "udp.server.for.touchportal.and.xplane"
        self.Desc = "UDP Server for Touch Portal and X-Plane (non blocking)"
        
        # Create a UDP socket
        self.ServerSocketUDP = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.ServerSocketUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ServerSocketUDP.settimeout(0)
        # Bind the socket to the port
        self.HOST = socket.gethostbyname(socket.gethostname())
        self.PORT = 65432
        self.ServerSocketUDP.bind((self.HOST, self.PORT))

    def XPluginStart(self):
        xp.log("XPluginStart")
        self.FlightLoopID = xp.createFlightLoop(self.FlightLoopCallback,0,None)
        xp.log(f"(FlightLoopID Adress: {self.FlightLoopID})") 
        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginStop") 

    def XPluginEnable(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginEnable")
        menuID = xp.createMenu("TPXPServer",handler=self.StartFlightLoop, refCon="Menu1")
        xp.appendMenuItem(menuID, "Start TPXP Server", refCon="StartXPServer")
        return 1

    def XPluginDisable(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginDisable") 
        xp.destroyFlightLoop(self.FlightLoopID)
        self.ServerSocketUDP.close()

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass 

    def StartFlightLoop(self,menuRefCon,itemRefCon):
        print("StartFlightLoop print UDP Server for Touch Portal and X-Plane up and listening")
        xp.log("xplog UDP Server for Touch Portal and X-Plane up and listening")
        xp.speakString(f"Menu {menuRefCon} selected")
        xp.scheduleFlightLoop(self.FlightLoopID,1,1)

    def FlightLoopCallback(self, sinceLast, elapsedTime, counter, refCon):
        print("inside FlightLoopCallback")
        try:
            bytesAddressPair = self.ServerSocketUDP.recvfrom(1024)
            self.ServerSocketUDP.settimeout(0)
        except socket.error:
            print("nothing")
        else:
            message = bytesAddressPair[0]
            address = bytesAddressPair[1]
            clientMsg = "Message from Client:{}".format(message)
            clientIP  = "Client IP Address:{}".format(address)
            print(clientMsg)
            print(clientIP)
            # Sending a reply to client
            msgFromServer = "Hello UDP Client"
            bytesToSend = str.encode(msgFromServer)
            self.ServerSocketUDP.sendto(bytesToSend, address)
        return 1.0