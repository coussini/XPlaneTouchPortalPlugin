import json
import TouchPortalAPI as TP
from TouchPortalAPI.logger import Logger

g_log = Logger(name = "XPlanePlugin")

# Setup callbacks and connection
TPClient = TP.Client("XPlanePlugin")

# This event handler will run once when the client connects to Touch Portal
@TPClient.on('info')
def onInfo(data):
    #print("")
    #print("Connected!")
    #print("TP returned")
    #print("-----------")
    #print("Data->", data)
    TPClient.createState("AirbusFBW_ElecOHPArray[3]","External Power","0")

# Action handlers, called when user activates one of this plugin's actions in Touch Portal.
@TPClient.on('action')
def onAction(data):
    #print("")
    #print("Action catch!")
    #print("TP returned")
    #print("-----------")
    #print("")
    #print("Event->", data["actionId"])
    Dataref_name = list(TPClient.getStatelist().keys())[0]
    Dataref_value = list(TPClient.getStatelist().values())[0]
    #print("Dataref->",Dataref_name)
    ###
    ### Create a method to dispatch actions, create method for each action   
    ###
    if data["actionId"] == "XPlanePlugin.Dataref.Set":
        #print("value will be->",data["data"][1]["value"])
        pass
    else:
        #print("Value was->",Dataref_value)
        pass
    #for i in Statelist:
    #    print("Field for this event->",i)
    #    print("Value (actual)      ->",Statelist[i])
# ListChange handlers, called when user activates one of this plugin's actions in Touch Portal.
@TPClient.on('listChange')
def onAction(data):
    pass
    #print("ListChange catch!")
    #print("TP returned")

# Shutdown handler, called when Touch Portal wants to stop your plugin.
@TPClient.on('closePlugin')
def onShutdown(data):
    #print("Got Shutdown Message! Shutting Down the Plugin!")
    # Terminates the connection and returns from connect()
    TPClient.disconnect()

def main():
    global TPClient, g_log
    ret = 0  # sys.exit() value

    try:
        # Connect to Touch Portal desktop application.
        # If connection succeeds, this method will not return (blocks) until the client is disconnected.
        TPClient.connect()
        g_log.info('TP Client closed.')
    except KeyboardInterrupt:
        g_log.warning("Caught keyboard interrupt, exiting.")
    except Exception:
        # This will catch and report any critical exceptions in the base TPClient code,
        # _not_ exceptions in this plugin's event handlers (use onError(), above, for that).
        from traceback import format_exc
        g_log.error(f"Exception in TP Client:\n{format_exc()}")
        ret = -1
    finally:
        # Make sure TP Client is stopped, this will do nothing if it is already disconnected.
        TPClient.disconnect()

    # TP disconnected, clean up.
    del TPClient

    g_log.info(f"{TP_PLUGIN_INFO['name']} stopped.")
    return ret