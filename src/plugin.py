import TouchPortalAPI as TP

# Setup callbacks and connection
TPClient = TP.Client("XPlanePlugin")

# This event handler will run once when the client connects to Touch Portal
@TPClient.on('info')
def onInfo(data):
    print("")
    print("Connected!")
    print("TP returned")
    print("-----------")
    print(data)
    TPClient.createState("AirbusFBW_ElecOHPArray[3]","External Power","0")

# Action handlers, called when user activates one of this plugin's actions in Touch Portal.
@TPClient.on('action')
def onAction(data):
    print("")
    print("Action catch!")
    print("TP returned")
    print("-----------")
    print("Data->", data)
    print("Event->", data["actionId"])
    actionId = data["actionId"]
    print("-----------")
    Statelist = TPClient.getStatelist()
    for i in Statelist:
        print("Field for this event->",i)
        print("Value (actual)      ->",Statelist[i])
    if actionId == "XPlanePlugin.Dataref.SetVariable":
        print("value for event:",actionId,"will be->",data["data"][1]["value"])
# ListChange handlers, called when user activates one of this plugin's actions in Touch Portal.
@TPClient.on('listChange')
def onAction(data):
    print("ListChange catch!")
    print("TP returned")

# Shutdown handler, called when Touch Portal wants to stop your plugin.
@TPClient.on('closePlugin')
def onShutdown(data):
    print("Got Shutdown Message! Shutting Down the Plugin!")
    # Terminates the connection and returns from connect()
    TPClient.disconnect()

# First Method call
TPClient.connect()