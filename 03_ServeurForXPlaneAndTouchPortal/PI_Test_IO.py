import xp
import socket

class PythonInterface:

    def __init__(self):
        self.Name = "PI_Test_IO"
        self.Sig = "test.xppython3"
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
        self.Conn, self.addr = self.S.accept()
        xp.log(f"{elapsedTime}, {counter}")
        return 1.0

    def XPluginStart(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginStart>>>>>>>>>>>>>>>>>>>>>>>>>") 
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>[STARTING] server is starting...")
        self.S.bind((self.HOST, self.PORT))
        self.S.listen()
        xp.log(f">>>>>>>>>>>>>>>>>>>>>>>>>[LISTENING] Server is listening on {self.HOST}")
        myRefCon = {'data': []}
        self.FlightLoopID = xp.createFlightLoop(self.handle_client, refCon=myRefCon)
        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginStop>>>>>>>>>>>>>>>>>>>>>>>>>") 
        self.Conn.close()
        xp.destroyFlightLoop(self.FlightLoopID)

    def XPluginEnable(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginEnable>>>>>>>>>>>>>>>>>>>>>>>>>") 
        return 1

    def XPluginDisable(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginDisable>>>>>>>>>>>>>>>>>>>>>>>>>") 

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass
