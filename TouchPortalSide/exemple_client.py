import TouchPortalAPI as TP

__version__ = "1.0"
PLUGIN_ID = "ExamplePlugin"

# Setup callbacks and connection
TPClient = TP.Client(PLUGIN_ID)

# This event handler will run once when the client connects to Touch Portal
@TPClient.on(TP.TYPES.onConnect) # Or replace TYPES.onConnect with 'info'
def onStart(data):
    print("SECTION ONSTART")
    print("Connected!", data)
    # Create Touch Portal State at runtime    
    TPClient.createState("ExampleState","Example State","None")    
    # Update a state value in TouchPortal
    TPClient.stateUpdate("ExampleState", "Connected!")

# Action handlers, called when user activates one of this plugin's actions in Touch Portal.
@TPClient.on(TP.TYPES.onAction) # Or 'action'
def onAction(data):
    print("SECTION ONACTION")
    print(data)
    # do something based on the action ID and the data value
    if data['actionId'] == "ExampleAction":
      # get the value from the action data (a string the user specified)
      action_value = TPClient.getActionDataValue(data.get('data'), 'ExampleTextData')
      print(action_value)
      # We can also update our ExampleStates with the Action Value
      TPClient.stateUpdate("ExampleState", str(action_value))

# Shutdown handler, called when Touch Portal wants to stop your plugin.
@TPClient.on(TP.TYPES.onShutdown) # or 'closePlugin'
def onShutdown(data):
    print("Got Shutdown Message! Shutting Down the Plugin!")
    # Terminates the connection and returns from connect()
    TPClient.disconnect()

# After callback setup like we did then we can connect.
# Note that `connect()` blocks further execution until
# `disconnect()` is called in an event handler, or an
# internal error occurs.
try:
    TPClient.connect()
except ConnectionRefusedError:
    print("Cannot connect to Touch Portal, probably the apps in not running")
except Exception:
    # This will catch and report any critical exceptions in the base TPClient code,
    # _not_ exceptions in this plugin's event handlers (use onError(), above, for that).
    from traceback import format_exc
    print(f"Exception in TP Client")
    print(f"\n{format_exc()}")
    ret = -1
del TPClient
