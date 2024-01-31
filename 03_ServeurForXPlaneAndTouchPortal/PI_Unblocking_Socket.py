#####################################################
# How setting non blocking socket in python with xp #
#####################################################
'''
Run your synchronous calls in their own thread.
Use a flight loop callback to read values from X-Plane using the SDK.
Store these values in a structure that your synchronous calls thread knows where to find.
Add some state to it so it knows when valid data is here.
Use the SDK to figure when the plane is changed.

A typical session of the x-plane simulator might go like this:

The user starts the simulator.
The simulator (via the XPLM) loads the plugin and calls your XPluginStart().
Your plugin creates a menu item and registers a callback for it.
The simulator then calls your XPluginEnable() function to notify you that the plugin is now enabled.
The user clicks your menu item, so the simulator calls your XPLMMenuHandler_f callback.
Your callback function then does something—for example, it might write some data to a file.
The user quits the simulator.
The simulator calls your XPluginDisable() function and then your XPluginStop() function.
Your plugin DLL is unloaded and the simulator quits.

'''
import xp
import socket

class PythonInterface:

    def __init__(self):
    	# strings using for plugin signature
        self.Name = "PI_Unblocking_Socket"
        self.Sig = "unblocking.socket.xppython3"
        self.Desc = "a skeleton for unblocking socket under xppython3"

        # socket usage
        self.PORT = 65432
        self.HOST = socket.gethostbyname(socket.gethostname())

    def XPluginStart(self):
        # Required by XPPython3
        # Called once by X-Plane on startup (or when plugins are re-starting as part of reload)
        # You need to return three strings
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