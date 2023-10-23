import xp
import json
import socket
import struct
import threading

SERVER = None

class PythonInterface:
    ''' 
    [0]
    '''
    def __init__(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>__init__>>>>>>>>>>>>>>>>>>>>>>>>>") 
        self.Name = "DatarefServer"
        self.Sig = "dataref.server.xppython3"
        self.Desc = "Serv and receive dataref data"
        
        self.Host = socket.gethostbyname(socket.gethostname())
        self.Port = 65432

    ''' 
    [1]
    Ceci est appelé lorsque le plugin est chargé pour la première fois. 
    Vous pouvez l'utiliser pour allouer des ressources permanentes et enregistrer 
    tous les autres rappels dont vous avez besoin. 
    C'est le bon moment pour configurer l'interface utilisateur. 
    Ce rappel renvoie également le nom, la signature et une description du plugin au XPLM.
    '''
    def XPluginStart(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginStart>>>>>>>>>>>>>>>>>>>>>>>>>") 
        xp.log("Initialize Server Socket") 
        self.Server = socket.socket()
        self.Server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # solution for "[Error 89] Address already in use". Use before bind()
        self.Server.bind((self.Host, self.Port))
        self.Server.listen(1)
        xp.log(f">>>>>>>>>>>>>>>>>>>>>>>>>Server Adress:>>>>>>>>>>>>>>>>>>>>> {self.Server}")
        self.FlightLoopID = xp.createFlightLoop(self.flight_loop, refCon=None)
        xp.log(f">>>>>>>>>>>>>>>>>>>>>>>>>FlightLoopID Adress:>>>>>>>>>>>>>>>>>>>>> {self.FlightLoopID}")
        # scheduleFlightLoop with parameter 1 to start only when the plane is loaded
        xp.scheduleFlightLoop(self.FlightLoopID, 10)
        return self.Name, self.Sig, self.Desc

    def send_data(self, conn, data):
        size = len(data)
        size_in_4_bytes = struct.pack('I', size)
        conn.send(size_in_4_bytes)
        conn.send(data)

    def recv_data(self, conn):
        size_in_4_bytes = conn.recv(4)
        size = struct.unpack('I', size_in_4_bytes)
        size = size[0]
        data = conn.recv(size)
        return data

    def handle_client(self, conn, addr):
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

    def flight_loop(self, sinceLast, elapsedTime, counter, refCon):
        xp.log(f">>>>>>>>>>>>>>>>>>>>>>>>>flight_loop>>>>>>>>>>>>>>>>>>>>> {elapsedTime}, {counter}")
        conn, addr = self.Server.accept() # receive a client host and address
        xp.log(f">>>>>>>>>>>>>>>>>>>>>>>>>client:>>>>>>>>>>>>>>>>>>>>> {addr}")
        one_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
        one_thread.start()
        return 1.0

    '''
    [2]
    Ceci est appelé lorsque le plugin est activé. 
    Vous n'avez rien à faire dans ce rappel, mais si vous le souhaitez, 
    nous pouvons allouer des ressources dont nous n'avons besoin que lorsqu'elles sont activées.
    '''
    def XPluginEnable(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginEnable>>>>>>>>>>>>>>>>>>>>>>>>>") 
        return 1

    '''
    [3]
    Ceci est appelé lorsqu'un plugin ou X-Plane envoie un message au plugin. 
    Voir l'article sur « Communication et messagerie interplugin » 
    pour plus d'informations. Le XPLM vous avertit lorsque des événements se produisent 
    dans le simulateur (comme l'écrasement de l'avion par l'utilisateur 
    ou la sélection d'un nouveau modèle d'avion) en appelant cette fonction.
    '''
    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginReceiveMessage>>>>>>>>>>>>>>>>>>>>>>>>>") 
        pass    

    '''
    [4]
    Ceci est appelé lorsque le plugin est désactivé. 
    Vous n'avez rien à faire dans ce rappel, mais si nous le souhaitons, 
    vous pouvez désallouer les ressources qui ne sont nécessaires que lorsqu'elles 
    sont activées. Une fois désactivé, le plugin peut ne pas fonctionner à nouveau 
    pendant très longtemps, vous devez donc fermer toutes les connexions réseau 
    qui pourraient autrement expirer.
    '''
    def XPluginDisable(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginDisable>>>>>>>>>>>>>>>>>>>>>>>>>") 
        xp.destroyFlightLoop(self.FlightLoopID)
        self.Server.close()
        pass

    '''
    [5]
    Ceci est appelé juste avant le déchargement du plugin. 
    Vous devez désenregistrer tous les rappels, libérer toutes les ressources, 
    fermer tous les fichiers et généralement nettoyer.
    '''
    def XPluginStop(self):
        xp.log(">>>>>>>>>>>>>>>>>>>>>>>>>XPluginStop>>>>>>>>>>>>>>>>>>>>>>>>>") 
        pass