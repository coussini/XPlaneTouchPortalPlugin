import socket

class PythonInterface:
    def __init__(self):
        self.Name = "XPDatarefSocketIO"
        self.Sig = "xp.dataref.socket.io"
        self.Desc = "Interface that allows updating or reading dataref through a socket"
        self.PORT = 65432
        self.HOST = socket.gethostbyname(socket.gethostname())
        self.FORMAT = 'utf-8'

    def XPluginStart(self):
        # Required by XPPython3
        # Called once by X-Plane on startup (or when plugins are re-starting as part of reload)
        # You need to return three strings
        print("XPluginStart") 
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.HOST,self.PORT))
        server.listen()
        print(f"[LISTENING] Server is listening on {self.HOST}")

        return self.Name, self.Sig, self.Desc
    
essai = PythonInterface()
essai.XPluginStart()