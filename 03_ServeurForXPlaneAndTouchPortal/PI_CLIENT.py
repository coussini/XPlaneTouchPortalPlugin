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
        self.Name = "PI_CLIENT"
        self.Sig = "client.for.touchportal.and.xplane"
        self.Desc = "Client for Touch Portal and X-Plane (non blocking)"
        
        # Create a TCP/IP socket
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client.setblocking(False)
        # Bind the socket to the port
        self.HOST = socket.gethostbyname(socket.gethostname())
        self.PORT = 65432
        # List of sockets to be monitored by select
        self.text = ""

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
            raw = self.client.recv(1024)
        except BlockingIOError:
            pass # No new data. Reuse old data
        else:
            self.text = raw.decode("utf-8") # New data has arrived. Use it
        if self.text != "":
            print(f"le texte est {self.text}")
        
        return 1

    '''
    [2]
    '''

    def StartFlightLoop(self,menuRefCon,itemRefCon):
        # scheduleFlightLoop with parameter 1 to start only when the plane is loaded
        self.client.connect((self.HOST, self.PORT))
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
        
        pass

    '''
    [5]
    '''
    def XPluginStop(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginStop") 
        
        pass