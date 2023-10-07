import xp
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
        xp.log("XPluginStart") 
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.HOST,self.PORT))
        server.listen()
        xp.log(f"[LISTENING] Server is listening on {self.HOST}")

        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        # Called once by X-Plane on quit (or when plugins are exiting as part of reload)
        # Return is ignored
        pass

    def XPluginEnable(self):
        # Required by XPPython3
        # Called once by X-Plane, after all plugins have "Started" (including during reload sequence).
        # You need to return an integer 1, if you have successfully enabled, 0 otherwise.
        return 1

    def XPluginDisable(self):
        # Called once by X-Plane, when plugin is requested to be disabled. All plugins
        # are disabled prior to Stop.
        # Return is ignored
        pass

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        # Called by X-Plane whenever a plugin message is being sent to your
        # plugin. Messages include MSG_PLANE_LOADED, MSG_ENTERED_VR, etc., as
        # described in XPLMPlugin module.
        # Messages may be custom inter-plugin messages, as defined by other plugins.
        # Return is ignored
        pass