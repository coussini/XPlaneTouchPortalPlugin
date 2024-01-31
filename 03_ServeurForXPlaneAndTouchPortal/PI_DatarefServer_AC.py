import xp
import socket
import select
from threading import Thread

class PythonInterface:

    def acceptConnexion():
        print("running in thread")
        while True:
            self.ServerSocket.listen(10)
            address = self.ServerSocket.accept()
            print("{} connected".format( address ))    
    ''' 
    [0]
    '''
    def __init__(self):
        xp.log("__init__") 
        self.Name = "DatarefServer_AC"
        self.Sig = "dataref.server.ac.xppython3"
        self.Desc = "Serv thread)"
        
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
        self.ServerSocket.listen()

        self.FlightLoopID = xp.createFlightLoop(self.flight_loop, phase=1, refCon=None)
        xp.log(f"(FlightLoopID Adress: {self.FlightLoopID})") 
        # scheduleFlightLoop with parameter 1 to start only when the plane is loaded
        xp.scheduleFlightLoop(self.FlightLoopID, interval=1, relativeToNow=1)

        return self.Name, self.Sig, self.Desc

    def flight_loop(self, sinceLast, elapsedTime, counter, refCon):
        xp.log(f"(Flight loop: {elapsedTime}, {counter})") 

        thread = Thread(target = self.acceptConnexion)
        thread.start()
        xp.log("Main thread will wait here for thread to exit") 
        print("Main thread will wait here for thread to exit")
        thread.join()
        xp.log("thread finished...exiting") 

        return 1.0

    '''
    [2]
    '''
    def XPluginEnable(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginEnable") 
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