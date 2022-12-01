import TouchPortalAPI as TP

# Setup callbacks and connection
TPClient = TP.Client("XPlanePlugin")

# This event handler will run once when the client connects to Touch Portal
@TPClient.on('info')
def onInfo(data):
    print("Connected!")
    print("TP returned:")
    print(data)
    #TPClient.createState("Ext_power","External Power","AirbusFBW_ElecOHPArray3")

# Action handlers, called when user activates one of this plugin's actions in Touch Portal.
@TPClient.on('action')
def onAction(data):
    print("Action catch!")
    print("TP returned:")
    print(data)
    print(TPClient.currentStates)
    # stateId = data["data"][0]["value"]
    # print(stateId)

# ListChange handlers, called when user activates one of this plugin's actions in Touch Portal.
@TPClient.on('listChange')
def onAction(data):
    print("ListChange catch!")
    print("TP returned:")

# Shutdown handler, called when Touch Portal wants to stop your plugin.
@TPClient.on('closePlugin')
def onShutdown(data):
    print("Got Shutdown Message! Shutting Down the Plugin!")
    # Terminates the connection and returns from connect()
    TPClient.disconnect()

# First Method call
TPClient.connect()