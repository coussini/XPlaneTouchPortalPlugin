import xp
import socket

class PythonInterface:

    def __init__(self):
        self.Name = "PI_MiniTest"
        self.Sig = "minitest.xppython3"
        self.Desc = "test rapide"
        self.PORT = 65432
        self.HOST = socket.gethostbyname(socket.gethostname())
        self.FORMAT = 'utf-8'
        self.FlightLoopID = None
        self.Conn = None
        self.addr = None
        self.S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.S.setblocking(0)

    def handle_client(lastCall, elapsedTime, counter, refCon):
        xp.log(f">>>>>>>>>>>>>>>>>>>>>>>>>[HANDLE CLIENT] {elapsedTime}, {counter}")
        return 1.0

    def XPluginStart(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginStart>>>>>>>>>>>>>>>>>>>>>>>>>") 
        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginStop>>>>>>>>>>>>>>>>>>>>>>>>>") 
        xp.destroyFlightLoop(self.FlightLoopID)

    def XPluginEnable(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginEnable>>>>>>>>>>>>>>>>>>>>>>>>>") 
        myRefCon = {'data': []}
        self.FlightLoopID = xp.createFlightLoop(self.handle_client, refCon=myRefCon)
        return 1

    def XPluginDisable(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginDisable>>>>>>>>>>>>>>>>>>>>>>>>>") 

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass
