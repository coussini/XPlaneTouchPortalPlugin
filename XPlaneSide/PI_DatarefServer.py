import xp
import json
import socket
import struct
import threading

class PythonInterface:
    def __init__(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>__init__>>>>>>>>>>>>>>>>>>>>>>>>>") 
        self.Name = "DatarefServer"
        self.Sig = "dataref.server.xppython3"
        self.Desc = "Serv and receive dataref data"
        self.Host = socket.gethostbyname(socket.gethostname())
        self.Port = 65432
        self.all_threads = []

    def handle_client(conn, addr):
        xp.log(f">>>>>>>>>>>>>>>>>>>>>>>>>handle_client>>>>>>>>>>>>>>>>>>>>> {elapsedTime}, {counter}")
        xp.log(f">>>>>>>>>>>>>>>>>>>>>>>>>handle_client [thread] starting>>>>>>>>>>>>>>>>>>>>>")
        # Recv JSON
        data = recv_data(conn)
        text = data.decode()
        stock = json.loads(text)
        xp.log(f">>>>>>>>>>>>>>>>>>>>>>>>>recv actionID {stock.get('dataref')}")
        xp.log(f">>>>>>>>>>>>>>>>>>>>>>>>>recv wich value {stock.get('newValue')}")
        conn.close()
        xp.log(f">>>>>>>>>>>>>>>>>>>>>>>>>handle_client [thread] ending>>>>>>>>>>>>>>>>>>>>>")
        return 1.0

    def waiting_client(lastCall, elapsedTime, counter, refCon):
        xp.log(f">>>>>>>>>>>>>>>>>>>>>>>>>waiting_client>>>>>>>>>>>>>>>>>>>>> {elapsedTime}, {counter}")
        conn, addr = self.Server.accept() # receive a client host and address
        xp.log(f">>>>>>>>>>>>>>>>>>>>>>>>>client:>>>>>>>>>>>>>>>>>>>>> {addr}")
        one_thread = threading.Thread(target=handle_client, args=(conn, addr))
        one_thread.start()
        self.all_threads.append(one_thread)
        return 1.0

    def XPluginStart(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginStart>>>>>>>>>>>>>>>>>>>>>>>>>") 
        xp.log("Initialize Server Socket") 
        Server = socket.socket()
        Server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # solution for "[Error 89] Address already in use". Use before bind()
        Server.bind((self.Host, self.Port))
        Server.listen(1)
        myRefCon = {'data': []}
        self.FlightLoopID = xp.createFlightLoop(self.waiting_client, refCon=myRefCon)
        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginStop>>>>>>>>>>>>>>>>>>>>>>>>>") 
        pass

    def XPluginEnable(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginEnable>>>>>>>>>>>>>>>>>>>>>>>>>") 
        return 1

    def XPluginDisable(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginDisable>>>>>>>>>>>>>>>>>>>>>>>>>") 
        xp.destroyFlightLoop(self.FlightLoopID)

        pass

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginReceiveMessage>>>>>>>>>>>>>>>>>>>>>>>>>") 
        pass