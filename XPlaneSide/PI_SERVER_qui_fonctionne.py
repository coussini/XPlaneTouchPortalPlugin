import xp
import socket
import os

class PythonInterface:

    def XPluginStart(self):
        xp.log("XPluginStart")
        xp.log("Mediator PLugin Start") 
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
        xp.registerFlightLoopCallback(self.FlightLoopCallback, 1.0, 0)         
        #self.FlightLoopID = xp.createFlightLoop(self.handle_connection,0,None)
        #xp.log(f"(FlightLoopID Adress: {self.FlightLoopID})")
        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        # Unregister the callback
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginStop") 
        xp.unregisterFlightLoopCallback(self.FlightLoopCallback, 0)        
        self.ServerSocketUDP.close()

    def XPluginEnable(self):
        return 1

    def XPluginDisable(self):
        pass 

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass 

    def FlightLoopCallback(self, sinceLast, elapsedTime, counter, refCon):
        print("inside FlightLoopCallback")
        try:
            bytesAddressPair = self.ServerSocketUDP.recvfrom(1024)
            self.ServerSocketUDP.settimeout(1)
        except socket.error:
            print("nothing")
        else:
            print(bytesAddressPair)
            # Return 1.0 to indicate that we want to be called again in 1 second.
        return 1.0
        '''
        if not bytesAddressPair:
            print("No data")
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
            #self.ServerSocketUDP.sendto(bytesToSend, address)
        '''