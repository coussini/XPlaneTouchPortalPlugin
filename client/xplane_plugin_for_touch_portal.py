import sys 
import os
import platform
from traceback import format_exc # to catch more information concerning exception error
import functools
import TouchPortalAPI as TP_API
import TouchPortalAPI.logger as TP_API_LOG # TouchPortalAPI.logger.Logger
import selectors
import socket
import json
import threading
import queue # this is only to pass exception from the secondary thread to the main thread
import types
import time
import math

PLUGIN_ID = 'xplane_plugin_for_touch_portal'
LOG_FILE = f'./{PLUGIN_ID}.log'
        
# Get OS where python is running.
IS_WINDOWS = True if (platform.system() == 'Windows') else False
IS_LINUX = True if (platform.system() == 'Linux') else False
IS_MACOS = True if (platform.system() == 'Darwin') else False

MESSAGE_DELIMITER = '#'
BUFFER_SIZE_USUAL = 1024
BUFFER_SIZE_INIT = 10240
BUFFER_SIZE = BUFFER_SIZE_INIT

'''
                  =================================  
                  N A M I N G   C O N V E N T I O N  
                  =================================  

Prefix for a method or a function
    -custom_json_           (concerning the "custom JSON" process)
    -touch_portal_client_   (concerning the touch program client process)
    -xplane_client_         (concerning the X-Plane Client process for the X-Plane Server. This server is meant to be used for state_id value and command exchange.)

Prefix for exception class
    -CustomErrorPlugin      (regarding the exception around this plugin and this program in general)
    -CustomErrorJson        (regarding the exception around the custom JSON)
    -CustomErrorXPlane      (regarding the exception in the exchange between the X-Plane Client and the X-Plane Server)

Important touch portal state
    -xplane_plugin_for_touch_portal.CONNEXION.main_status
       '0': Initial status 
       '1': Plugin error  
       '2': Connected to Touch Portal
       '3': Custom JSON error
       '4': Custom JSON Loaded
       '5': X-Plane Client or Server error
       '6': X-Plane Client connected to X-Plane server AND
            when the X-Plane client receives the current state_id values from the X-Plane server (initialization)

                  =======================  
                  P R O G R A M   F L O W   
                  =======================  

-Connecting to the Touch Portal server
-Extract dataref information from a customized JSON file. Validate the JSON contains and keys

        # --------------------------------------------- 
        # A sample of dataref information without index
        # ---------------------------------------------
        # "id": "sim/cockpit2/gauges/indicators/altitude_ft_pilot",
        # "desc": "Altitude current (pilot)",
        # "group": "Avionics",
        # "dataref": "sim/cockpit2/gauges/indicators/altitude_ft_pilot",
        # "touch_portal_format" :"",
        # "xplane_update_min_value" :"",
        # "xplane_update_max_value" :"",
        # "accelerated_control" :"",
        # "comment": "Altitude current (height, MSL, in feet, pilot)"
        # 
        # ------------------------------------------ 
        # A sample of dataref information with index
        # ------------------------------------------ 
        # "id": "sim/cockpit2/engine/actuators/throttle_ratio[0]", -> [0] -> mean index 0
        # "desc": "Throttle Ratio",
        # "group": "Engine",
        # "dataref": "sim/cockpit2/engine/actuators/throttle_ratio[0]",
        # "touch_portal_format" :"",
        # "xplane_update_min_value" :"0",
        # "xplane_update_max_value" :"1",
        # "accelerated_control" :"",
        # "comment": "Throttle Ratio: 0.0 = Low Throttle, 0.25, 0.50, 0.75, 1 = High Throttle"
        # 
        # --------------------------------------- 
        # A sample of dataref with formating data (See details in "DATA FORMATTING CONCERNING THIS PROGRAM" section, little further bellow)
        # ---------------------------------------
        # "id": "sim/cockpit2/radios/actuators/com1_frequency_hz_833",
        # "desc": "Com1 frequency",
        # "group": "Radio",
        # "dataref": "sim/cockpit2/radios/actuators/com1_frequency_hz_833",
        # "touch_portal_format" :"D3", -> Transfor integer X-Plane value in the format : three decimal : 126400 -> 126.400
        # "xplane_update_min_value" :"",
        # "xplane_update_max_value" :"",
        # "accelerated_control" :"com",
        # "comment": "Com1 frequency (int value with decimal inside)"
        # 
        # ---------------------- 
        # A sample for a command
        # ----------------------
        # "id": "sim/flight_controls/landing_gear_down[CMD]", -> [CMD] -> mean "commandOnce" in X-Plane
        # "desc": "Gear Down",
        # "group": "Command",
        # "dataref": "sim/flight_controls/landing_gear_down[CMD]",
        # "touch_portal_format" :"",
        # "xplane_update_min_value" :"",
        # "xplane_update_max_value" :"",
        # "accelerated_control" :"",
        # "comment": "A command for Gear Down"
        # 
        # --------------------------- 
        # A sample for a COMMAND_3 (simulate for example the engine starter)
        # ---------------------------
        # "id": "sim/ignition/engage_starter_1[3SECONDS_CMD]",  -> [3SECONDS_CMD] -> mean "commandOnce" + then about 3 seconds to execute it + "commandEnd" in X-Plane
        # "desc": "Engage Starter 1 Hold",
        # "group": "command_3",
        # "dataref": "sim/ignition/engage_starter_1[3SECONDS_CMD]",
        # "touch_portal_format" :"",
        # "xplane_update_min_value" :"",
        # "xplane_update_max_value" :"",
        # "accelerated_control" :"",
        # "comment": "A command for Engage Starter 1 Hold"
        #
        # --------------------------- 
        # A sample for an accelerated control category. 
        # By doing this, all accelerated control are grouped together by category, in this example this would be nav
        # ---------------------------
        #
        # "id": "sim/cockpit2/radios/actuators/nav2_left_frequency_hz",
        # "desc": "Nav2 left frequency",
        # "group": "Radio",
        # "dataref": "sim/cockpit2/radios/actuators/nav2_left_frequency_hz",
        # "touch_portal_format" :"D2", -> Transform integer X-Plane value in the format : two decimal : 11705 -> 117.05
        # "xplane_update_min_value" :"",
        # "xplane_update_max_value" :"",
        # "accelerated_control" :"degree",
        # "comment": "Nav2 left frequency (int value with decimal inside)"
                    

-Create touch portal states for each dataref, including its id, description, value, and group. 
    "id": Come from the customized JSON File
    description: The group and desc fields are merged to create the description. <-- x['group'] + ' - ' + x['desc']
    value: Was set to '0' at beginning.
    "group": Come from the JSON file, and allows dataref of the same group to be grouped together. 
             Within a group, it's easier to find dataref or command in a multiple choice area, when creating a Touch Portal page.


=======================
INTO THE ENTRY.TP FILE:
=======================
-The "xplane_plugin_for_touch_portal.PLUGIN.set_is_connected_to" action id, contains 
    a "valueChoices" field concerning the connexion status with Touch Portal (Yes or No). 
-The "xplane_plugin_for_touch_portal.PLUGIN.set_main_status_to" action id, contains 
    a field concerning the status of the Plugin (0 - 6). 
-The "xplane_plugin_for_touch_portal.PLUGIN.set_custom_dataref_json_file" action id, contains 
    a field concerning the full json file name (including json extension). 
-The "xplane_plugin_for_touch_portal.PLUGIN.start_communication_with_server" action id, contains 
    a "valueChoices" field concerning the connexion status with the X-Plane Server (The plugin status must be 6). 
-The "xplane_plugin_for_touch_portal.DATAREF.set_states" action id, contains 
    a "valueChoices" field concerning the dataref "full_description" field from the customized JSON file, which derives from the "group" and "desc" fields. 
-The "xplane_plugin_for_touch_portal.DATAREF.accelerated_degree" action id, contains 
    a "valueChoices" field concerning the dataref "full_description" field from the customized JSON file, which derives from the "group" and "desc" fields AND
    the adjustment mode ("increment","decrement") with an update mode ("now","as soon as you release the button"). The "valueChoices" field is populated with 
    entries from the JSON file that have the "accelerated_control" field set to "degree".
-The "xplane_plugin_for_touch_portal.DATAREF.accelerated_altitude" action id, contains 
    a "valueChoices" field concerning the dataref "full_description" field from the customized JSON file, which derives from the "group" and "desc" fields AND
    the adjustment mode ("increment","decrement") with an update mode ("now","as soon as you release the button"). The "valueChoices" field is populated with 
    entries from the JSON file that have the "accelerated_control" field set to "altitude". 
-The "DATAREF.slider_1 thru DATAREF.slider_12" connector id, contains
    a "valueChoices" field concerning the dataref "desc" field from the customized JSON file AND the current page (must be the main touch portal page name of your aircraft pages).
    The "valueChoices" field is populated with entries from the JSON file that have the "group" field set to "slider".
-The "xplane_plugin_for_touch_portal.COMMAND.execute" action id, contains
    a "valueChoices" field concerning the command "desc" field from the customized JSON file. The "valueChoices" field is populated with 
    entries from the JSON file that have the "[CMD]" string at the end of the dataref name.  
-The "xplane_plugin_for_touch_portal.COMMAND_3.execute" action id , contains
    a "valueChoices" field concerning the COMMAND_3 "desc" field from the customized JSON file. The "valueChoices" field is populated with 
    entries from the JSON file that have the "[CMD_3]" string at the end of the dataref name.  

========
PROCESS:
========
 We update the list of choices created previously from all JSON's dataref and command. 
-Initially, (in a secondary thread) the xplane client sends the list of datarefs and commands
 and receives from the X-Plane server the dataref values.
-The X-Plane server start a special process to check any update in theses dataref and send the values (per each second)
-We update the touch portal "dymanic states" with these new values.
-When a user press a button within a touch portal page within an associate dataref "desc" choice, 
 the action id "xplane_plugin_for_touch_portal.DATAREF.set_states" is specify as required and send the value to the X-Plane Server
 for updating dataref value and the "dynamic state"
-When a user press a button within a touch portal page within a associate command "desc" choice, 
 the action id "xplane_plugin_for_touch_portal.COMMAND.execute" is specify as required and send the command to the X-Plane Server
 for executing it
-When a user press a button within a touch portal page within a associate COMMAND_3 "desc" choice, 
 the action id "xplane_plugin_for_touch_portal.COMMAND_3.execute" is specify as required and send the command to the X-Plane Server
 for executing it
-When a user press a button within a touch portal page within a associate slider (connector) "desc" choice, 
 the connector id "xplane_plugin_for_touch_portal.DATAREF.slider" is specify as required and send the command to the X-Plane Server
 for executing it

                  =========================================================================  
                  D A T A   T R A N S F E R   C O N C E R N I N G   T O U C H   P O R T A L    
                  =========================================================================  

-IMPORTANT: The data transfert between the Touch Portal client and the Touch Portal server is always in string format
-The following Touch Portal methods (function) are used by this program and use strings as mentioned
-For more details see the url "https://killerboss2019.github.io/TouchPortal-API/TouchPortalAPI/client.html"

                  =========================================================================  
                  D A T A   T R A N S F E R   C O N C E R N I N G   T H I S   P R O G R A M    
                  =========================================================================  

-The data transfert between the X-Plane Client and the X-Plane Server is always in string format. This program
 uses the same approach as Touch Portal transfert. See the the chart for communication paquet, in this program

                  =============================================================================  
                  D A T A   F O R M A T T I N G   C O N C E R N I N G   T H I S   P R O G R A M    
                  =============================================================================  

-All data formatting, whether for server transfering or for displaying, is done on this side. The format code is comme from "touch_portal_format" field

-Format codes use (remembering that X-Plane server send float or double value with two decimal only)
                   --------------------------------------------------------------------------------

    D1 -> one decimal : 99.35 -> 99.3
    D2 -> integer to two decimal : 11705 -> 117.05
    D3 -> integer to three decimal : 126400 -> 126.400
    ND -> remove decimal dot (no decimal string like radio nav1) : 2312.99 -> 231299

'''

# Create the (optional) global logger, an instance of `TouchPortalAPI::Logger` helper class.
try:
    logger = TP_API_LOG.Logger(name = PLUGIN_ID)
except Exception as e:
    sys.exit(f'==> Could not create a Touch Portal log file. Error was:\n{repr(e)}')

class CustomErrorPlugin(Exception): # sub class

    def __init__(self, message):
        '''
        Initialization of the exception class for handling plugin errors
        '''
        super().__init__(message)

class CustomErrorJson(Exception): # sub class

    def __init__(self, message):
        '''
        Initialization of the exception class for handling the custom JSON errors
        '''
        super().__init__(message)

class CustomErrorXPlane(Exception): # sub class

    def __init__(self, message):
        '''
        Initialization of the exception class for handling the communication between the X-Plane client and the X-Plane Server
        '''
        super().__init__(message)

class XPlanePluginStatus:
    '''
    This class is directly associated with the state "xplane_plugin_for_touch_portal.CONNEXION.main_status"
       '0': Initial status 
       '1': Plugin error  
       '2': Connected to Touch Portal
       '3': Custom JSON error
       '4': Custom JSON Loaded
       '5': X-Plane Client or Server error
       '6': X-Plane Client connected to X-Plane server AND
            when the X-Plane client receives the current state_id values from the X-Plane server (initialization)
    '''
    INITIAL_STATUS = '0'
    PLUGIN_ERROR = '1'
    CONNECTED_TO_TOUCH_PORTAL = '2'
    CUSTOM_JSON_ERROR = '3'
    CUSTOM_JSON_LOADED = '4'
    X_PLANE_CLIENT_OR_SERVER_ERROR = '5'
    X_PLANE_CLIENT_CONNECTED_TO_X_PLANE_SERVER = '6'

class XPlanePlugin:

    class AcceleratedControl: # sub class
        '''
        Sub class to Simulate incrementation or decrementation when an event "on_hold_down" appears. Stop it when an event "onHold_up" appears
        This terminology clearly conveys that the button, when held down, repeats an action (like increasing a value) in an accelerated manner.
        '''
        def __init__(self, XPlanePlugin, timeout=20): # Timeout in second (usually a use can't hold more than 20 seconds)
            '''
            Class initialization. 
            '''
            self.XPlanePluginInstance = XPlanePlugin # Use the main class to obtain its objects
            self.timeout = timeout # for the timeout
            self.start_time = None # for the timeout
            self.change_acceleration_factor = 1.1
            self.thread = None
            self.keep_running = threading.Event()

        def start_adjustment(self, adjustment_mode, state_id, value, initial_change_rate, max_change_rate, update_mode):
            '''
            Start thread for this control
            '''
            self.adjustment_mode = adjustment_mode  # "increment" or "decrement"
            self.state_id = state_id
            self.value = value
            self.change_rate = initial_change_rate
            self.max_change_rate = max_change_rate
            self.update_mode = update_mode

            self.keep_running.set()  
            self.start_time = time.time() # for the timeout               
            self.thread = threading.Thread(target=self.adjustment_loop)
            self.thread.daemon = True # all daemon thread will shut down immediately when the program exits
            self.thread.start()
        
        def stop_adjustment(self):
            '''
            Stop thread regarding this control
            '''
            if self.thread:

                if self.update_mode == 'as soon as you release the button':

                    try:

                        self.update_state_only()
                        # update only when server up and running
                        if self.XPlanePluginInstance.keep_running.is_set() and self.XPlanePluginInstance.current_main_status == XPlanePluginStatus.X_PLANE_CLIENT_CONNECTED_TO_X_PLANE_SERVER:
                            self.update_x_plane_state_id()
                            time.sleep(0.1)  # pause between stateUpdate

                    except Exception as e:
                        raise # Bubbling up the exception

                self.keep_running.clear()  

                if self.thread.is_alive():
                    self.thread.join()

        def adjustment_loop_update_section(self):
            '''
            Thread part regarding the update value in states and or X-Plane dataref
            '''
            if self.update_mode == 'now':
                try:
                    self.update_state_only()
                    # update only when server up and running
                    if self.XPlanePluginInstance.keep_running.is_set() and self.XPlanePluginInstance.current_main_status == XPlanePluginStatus.X_PLANE_CLIENT_CONNECTED_TO_X_PLANE_SERVER:
                        self.update_x_plane_state_id()
                        time.sleep(0.1)  # pause between stateUpdate

                except Exception as e:
                    raise # Bubbling up the exception

            else:

                try:
                    self.update_state_only()

                except Exception as e:
                    raise # Bubbling up the exception


        def adjustment_loop(self):
            '''
            Thread regarding this control (to be define in inheritage sub classes)
            '''
            pass

        def adjust_change_rate(self):
            '''
            Thread regarding this control (to be define in inheritage sub classes)
            '''
            pass

        def update_state_only(self):

            try:
                if self.XPlanePluginInstance.tp_api.currentStates[self.state_id] != self.value:
                    self.XPlanePluginInstance.tp_api.stateUpdate(self.state_id, str(self.value)) 

            except BufferError:
                pass # skip any buffer error

            except Exception as e:
                error_report = format_exc()
                raise CustomErrorPlugin(f'stateUpdate error\nMessage: {e}\nError report: {error_report}')

        def update_x_plane_state_id(self):
            '''
            Request update from touch portal for this value
            '''
            message = {}
            message['command'] = self.XPlanePluginInstance.request_update_from_touch_portal
            message['state_id'] = self.state_id
            message['value'] = str(self.value)
            outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
            self.XPlanePluginInstance.shared_data_container.outb += outgoing_message.encode('utf-8')                    

    class DegreeControl(AcceleratedControl): # sub class with inheritage from AcceleratedControl
        '''
        Inheritage of the Sub class AcceleratedControl. 
        Degress value: 0 thru 359 -> OBS, HDG, HSI, VOR
        initial_change_rate value: 0.5
        '''

        def adjustment_loop(self):
            '''
            Perform the degree adjustment based on the adjustment_mode
            '''
            while self.keep_running.is_set():  

                current_time = time.time()

                # protection for this thread
                if current_time - self.start_time >= self.timeout:
                    self.keep_running.clear()  

                self.value = (self.value + self.change_rate if self.adjustment_mode == "increment" else self.value - self.change_rate) % 360
                self.value = round(self.value,3)
                time.sleep(0.2)  # Pause between increments or decrement

                # To check if a user click rapidly on a button (start-stop process)
                if self.keep_running.is_set():  
                    self.adjustment_loop_update_section()
                    self.adjust_change_rate()

        def adjust_change_rate(self):
            '''
            Adjust change rate with a natural acceleration behavior..
            '''
            elapsed_time = time.time() - self.start_time
            growth_factor = math.exp(elapsed_time / 10) - 1  # adjust to start slowly 
            self.change_rate = min(self.change_rate + growth_factor, self.max_change_rate)


    class AltitudeControl(AcceleratedControl): # sub class with inheritage from AcceleratedControl
        '''
        Inheritage of the Sub class AcceleratedControl. 
        Altitude value: 0 thru integer value
        '''

        def adjustment_loop(self):
            '''
            Perform the degree adjustment based on the adjustment_mode
            '''
            while self.keep_running.is_set():  

                current_time = time.time()

                # protection for this thread
                if current_time - self.start_time >= self.timeout:
                    self.keep_running.clear()  

                self.value = self.value + self.change_rate if self.adjustment_mode == "increment" else self.value - self.change_rate
                self.value = round(self.value,2)
                time.sleep(0.2)  # Smaller sleep time for smoother acceleration

                # To check if a user click rapidly on a button (start-stop process)
                if self.keep_running.is_set():  
                    self.adjustment_loop_update_section()
                    self.adjust_change_rate()

        def adjust_change_rate(self):
            '''
            Adjust change rate with a natural acceleration behavior..
            '''
            elapsed_time = time.time() - self.start_time
            growth_factor = int(elapsed_time / 10)  # Cap growth to prevent excessive speed
            self.change_rate = min(self.change_rate + growth_factor, self.max_change_rate)

    def __init__(self):
        '''
        Class initialization. 
        '''

        '''
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        | Concerning the "custom JSON" that contains dataref informations |
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        '''
        self.json_keys_first_level = 'datarefs'
        self.json_keys = ['id', 'desc', 'group', 'dataref', 'full_description', 'touch_portal_format', 'accelerated_control', 'xplane_update_min_value', 'xplane_update_max_value', 'comment']
        self.json_keys.sort()
        self.json_critical_keys = ['id', 'desc', 'group', 'dataref']
        self.json_critical_keys.sort()

        if IS_WINDOWS: self.touch_portal_xplane_json_folder = os.getenv('APPDATA') + '\\TouchPortal\\misc\\xplane\\';
        if IS_LINUX: self.touch_portal_xplane_json_folder = '\\TouchPortal\\misc\\xplane\\';
        if IS_MACOS: self.touch_portal_xplane_json_folder = '\\Documents\\TouchPortal\\misc\\xplane\\';

        self.json_folder_location = self.touch_portal_xplane_json_folder
        self.json_file_name = 'default.json' # Default Custom JSON file

        # Dictionnary to keep the shortConnectorId with desc. the desc is the key and shortConnectorId a value
        self.desc_with_short_connector_id = {}

        # keep states from JSON file
        self.states = []

        '''
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        | Concerning the Touch Portal API and Touch Portal Client |
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        '''
        try:
            self.tp_api = TP_API.Client(            # Create the Touch Portal API client instance
                pluginId = PLUGIN_ID,               # Required ID of this plugin
                sleepPeriod = 0.05,                 # Allow more time than default for other processes
                autoClose = True,                   # Automatically disconnect when TP sends 'closePlugin' message
                checkPluginId = True,               # Validate destination of messages sent to this plugin
                maxWorkers = 4,                     # Run up to 4 event handler threads
                updateStatesOnBroadcast = False     # Do not spam TP with state updates on every page change
            )
        except Exception as e:
            sys.exit(f'==> Could not create a Touch Portal API client instance, exiting. Error was:\n{repr(e)}')

        self.tp_api.setLogFile(LOG_FILE)
        self.tp_api.setLogStream(sys.stdout)
        self.tp_api.setLogLevel("INFO")

        # Event for the Touch Portal API
        self.on_connect = TP_API.TYPES.onConnect
        self.on_action = TP_API.TYPES.onAction
        self.on_hold_down = TP_API.TYPES.onHold_down
        self.on_hold_up = TP_API.TYPES.onHold_up
        self.on_connector_change = TP_API.TYPES.onConnectorChange
        self.shortConnectorIdNotification = TP_API.TYPES.shortConnectorIdNotification
        self.on_broadcast = TP_API.TYPES.onBroadcast
        self.on_error = TP_API.TYPES.onError
        self.on_shutdown = TP_API.TYPES.onShutdown

        # This list is for displaying all slider by page; slider number and description into log
        self.short_connector_id_notification_list_for_log = []
        '''
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        | Concerning the instance for the accelarated controls |
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        '''
        # these controls use daemon threads for increment/decrement processing on value
        self.DegreeControlInstance = self.DegreeControl(self) # DegreeControl sub class inherits from AccelerateControl sub class
        self.AltitudeControlInstance = self.AltitudeControl(self) # AltitudeControl sub class inherits from AccelerateControl sub class

        '''
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        | Concerning the X-Plane client for the X-Plane server |
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        '''
        self.custom_error_xplane_queue = queue.Queue() # keep the exception from the x-plane thread
        self.client_selectors = selectors.DefaultSelector()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = 65432
        
        self.keep_running = threading.Event()
        self.xplane_client_thread = None # For the instance of threading.Thread class

        self.init_phase_done = threading.Event()
        self.init_phase_running = threading.Event()

        # Set Plugin is_connected to 0 (Not connected)
        self.plugin_is_connected = 0

        # Current 'xplane_plugin_for_touch_portal.CONNEXION.main_status'
        self.current_main_status = XPlanePluginStatus.INITIAL_STATUS

        # Current page path for the main TP device
        self.current_page_path_main_device = None

        # Connection information package or session data container for TCP/IP exchange 
        # inb for receiving and outb for sending)
        self.shared_data_container = types.SimpleNamespace(inb=bytearray(),outb=bytearray()) 

        # keep the address in the connection information package or session data container for TCP/IP exchange
        self.shared_data_container.addr = (self.host,self.port)

        # Keep a state_id and format code for initialization and transfering to server
        self.state_id_and_format_list  = []

        # Keep a sorted state_id list that should be working on
        self.state_id_list = []
        self.nb_entries_state_id_list = 0

        # keep a state_id list that should be initialized
        self.state_id_list_initialized = []
        self.nb_entries_state_id_list_initialized = 0

        # Store state_id and their values from X-Plane in a dictionary for updating states in Touch Portal
        self.state_id_and_values_dictionary = {}
        '''
        ============================================================================
        This is the chart for communifcation paquet between the client and the server
        ============================================================================
        '''
        # Packet that asks this server for the current state_id value in x-plane (initialization part)  
        self.request_state_id_value = 'request_state_id_value'
        self.request_state_id_value_paquet = ['command', 'state_id', 'dataref', 'xplane_update_max_value', 'xplane_update_min_value']
        # Packet for response for the previous request  
        self.response_state_id_value = 'response_state_id_value'
        self.response_state_id_value_paquet = ['command', 'state_id', 'message', 'value']

        # Packet that explains to this server that the initialization part is completed  
        self.request_initialization_done = 'request_initialization_done'
        self.request_initialization_done_paquet = ['command']
        # Packet for response for the previous request  
        self.response_initialization_done = 'response_initialization_done'
        self.response_initialization_done_paquet = ['command', 'message']

        # Packet that explains to this server that a state_id value has been updated in Touch Portal  
        self.request_update_from_touch_portal = 'request_update_from_touch_portal'
        self.request_update_from_touch_portal_paquet = ['command', 'state_id', 'value']
        # Packet for response for the previous request  
        self.response_update_from_touch_portal = 'response_update_from_touch_portal'
        self.response_update_from_touch_portal_paquet = ['command', 'state_id', 'message']

        # Packet that explains to this server that a command must be executed on the x-plane side  
        self.request_command_for_touch_portal = 'perform_command_for_touch_portal'
        self.request_command_for_touch_portal_paquet = ['command', 'state_id']
        # Packet for response for the previous request  
        self.response_command_for_touch_portal = 'response_perform_command_for_touch_portal'
        self.response_command_for_touch_portal_paquet = ['command', 'state_id', 'message']

        # Packet that explains to this server that a command_3 must be executed on the x-plane side  
        self.request_command_3_for_touch_portal = 'perform_command_3_for_touch_portal'
        self.request_command_3_for_touch_portal_paquet = ['command', 'state_id']
        # Packet for response for the previous request  
        self.response_command_3_for_touch_portal = 'response_perform_command_3_for_touch_portal'
        self.response_command_3_for_touch_portal_paquet = ['command', 'state_id', 'message']

        # Packet that explains to the client that a state_id value has been updated in X-Plane  
        self.request_update_from_x_plane = 'request_update_from_x_plane'
        self.request_update_from_x_plane_paquet = ['command', 'state_id', 'value']
        # Packet for response for the previous request  
        self.response_update_from_x_plane = 'response_update_from_x_plane'
        self.response_update_from_x_plane_paquet = ['command', 'state_id', 'message']

    def process_with_error_handling(self, e, current_main_status):
        '''
        Process CustomErrorPlugin, CustomErrorJson or CustomErrorXPlane and other error
        for other error, do not update the current_main_status (generally outside the Touch Portal Process)
        '''
        logger.error(f'==> ERROR -> INSIDE {PLUGIN_ID}')
        
        if current_main_status == XPlanePluginStatus.PLUGIN_ERROR:
            logger.error(f'==> ERROR -> PLUGIN ERROR')
        
        elif current_main_status == XPlanePluginStatus.CUSTOM_JSON_ERROR:
            logger.error(f'==> ERROR -> CUSTOMIZED JSON ERROR')
        
        elif current_main_status == XPlanePluginStatus.X_PLANE_CLIENT_OR_SERVER_ERROR:
            logger.error(f'==> ERROR -> XPLANE SERVER COMMUNICATION')
        else:
            logger.error(f'==> ERROR -> OTHER ERROR')
        
        error_messages = str(e).encode('utf-8').decode('utf-8').split('\n')

        for error_message in error_messages:
            logger.error(f'==> ERROR -> {error_message}')
        
        if current_main_status:
            try:
                self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.CONNEXION.main_status', current_main_status)

            except Exception as e:
                error_report = format_exc()
                logger.error(f'==> CRITICAL ERROR -> stateUpdate error\nMessage: {e}\nError report: {error_report}')

    def with_error_handling(self, func):
        """
        A decorator that adds centralized error handling to functions handling Touch Portal events.

        This decorator catches and processes various specific and general exceptions,
        allowing for a uniform response to errors within the application context.

        Args:
            func (callable): The function to decorate.

        Returns:
            callable: The decorated function with error handling.

        Usage:
            @with_error_handling
            def event_handler(data):
                ...
        """        
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            try:
                return func(*args, **kwargs)

            except CustomErrorPlugin as e:
                self.process_with_error_handling(e,XPlanePluginStatus.PLUGIN_ERROR)

            except CustomErrorJson as e:
                self.process_with_error_handling(e,XPlanePluginStatus.CUSTOM_JSON_ERROR)

            except CustomErrorXPlane as e:
                self.process_with_error_handling(e,XPlanePluginStatus.X_PLANE_CLIENT_OR_SERVER_ERROR)

            except Exception as e:
                self.process_with_error_handling(e, None)

        return wrapper
    
    def custom_json_append_required_and_essential_dataref(self, states):
        '''
        Append required dataref to the states 
        '''

        # A required and essential element
        required_element = {
            "id":"DO_NOT_DELETE.sim/cockpit2/gauges/actuators/barometer_setting_in_hg_pilot",
            "desc": "Barometer setting (pilot)",
            "group": "Avionics",
            "dataref": "sim/cockpit2/gauges/actuators/barometer_setting_in_hg_pilot",
            "touch_portal_format" :"",
            "xplane_update_min_value" :"",
            "xplane_update_max_value" :"",
            "accelerated_control" :"",
            "comment": "The pilots barometer setting (29.90 * 33.8639 = 1013.2 (1013) STD)"
        }

        # Append this esssential element
        states['datarefs'].append(required_element)

        # A required and essential element
        required_element = {
            "id":"DO_NOT_DELETE.sim/cockpit2/gauges/actuators/barometer_setting_in_hg_copilot",
            "desc": "Barometer setting (co-pilot)",
            "group": "Avionics",
            "dataref": "sim/cockpit2/gauges/actuators/barometer_setting_in_hg_copilot",
            "touch_portal_format" :"",
            "xplane_update_min_value" :"",
            "xplane_update_max_value" :"",
            "accelerated_control" :"",
            "comment": "The co-pilots barometer setting (29.90 * 33.8639 = 1013.2 (1013) STD)"
        }

        # Append this esssential element
        states['datarefs'].append(required_element)

        # A required and essential element
        required_element = {
            "id":"DO_NOT_DELETE.sim/cockpit2/gauges/actuators/barometer_setting_in_hg_stby",
            "desc": "Barometer setting (standard)",
            "group": "Avionics",
            "dataref": "sim/cockpit2/gauges/actuators/barometer_setting_in_hg_stby",
            "touch_portal_format" :"",
            "xplane_update_min_value" :"",
            "xplane_update_max_value" :"",
            "accelerated_control" :"",
            "comment": "The standard barometer setting (29.90 * 33.8639 = 1013.2 (1013) STD)"
        }

        # Append this esssential element
        states['datarefs'].append(required_element)

        # A required and essential element
        required_element = {
            "id":"DO_NOT_DELETE.sim/aircraft/view/acf_descrip",
            "desc": "Aircraft Name Description",
            "group": "Miscellaneous",
            "dataref": "sim/aircraft/view/acf_descrip",
            "touch_portal_format" :"",
            "xplane_update_min_value" :"",
            "xplane_update_max_value" :"",
            "accelerated_control" :"",
            "comment": "Aircraft Name Description (full name)"
        }

        # Append this esssential element
        states['datarefs'].append(required_element)

        return states
    
    def custom_json_convert_keys_to_lowercase(self, states):
        '''
        Convert all keys from the JSON file to lowercase 
        '''
        if isinstance(states, dict):
            return {k.lower(): self.custom_json_convert_keys_to_lowercase(v) for k, v in states.items()}
        elif isinstance(states, list):
            return [self.custom_json_convert_keys_to_lowercase(element) for element in states]
        else:
            return states
    
    def custom_json_create_full_description_field(self, states):
        '''
        Create full description field
        '''
        for x in states['datarefs']:
            x['full_description'] = x['group'] + ' - ' + x['desc'] # -> create a new state variable for each state

        return states

    def custom_json_validate_keys(self):
        '''
        Validate the JSON file to ensure that all keys are listed 
        '''
        successful = True
        seen_ids = set()

        if not self.json_keys_first_level in self.states:
            successful = False
            raise CustomErrorJson(f'The first-level-key must be\n{self.json_keys_first_level}')
        else:
            for x in self.states['datarefs']:
                keys = list(x.keys())
                keys.sort()
            
                if keys != self.json_keys:
                    successful = False
                    raise CustomErrorJson(f'The second-level-key must be\n{self.json_keys}\nAnd not {keys}\nSecond-level keys with Error: {x}')

                # Check that critical keys are not empty
                for key, value in x.items():
                    if value == "" and key in self.json_critical_keys:
                        successful = False
                        raise CustomErrorJson(f"The value for the key '{key}' is an empty string.\nThe problematic entry is: {x}")
                    else:
                        if key == 'id':
                            id_value_normalized = value  
                            
                            if id_value_normalized in seen_ids:
                                successful = False
                                raise CustomErrorJson(f"Duplicate 'ID' value found: {value}\nThe problematic entry is: {x}")
                            
                            seen_ids.add(id_value_normalized)                            
                
                if not successful:
                    break
            
            return successful
    
    def custom_json_validate_datarefs_unique_descritions(self):
        '''
        Insure that id has unique full_description
        '''

        # Create a set to store unique concatenations
        successful = True
        concat_set = set()

        for x in self.states['datarefs']:
            # Check if the concatenation already exists in the set
            if x['full_description'] in concat_set:
                successful = False
                raise CustomErrorJson(f'There a duplicate "group - desc"\nSee the following\n{x['full_description']}\nThe problematic entry is: {x}"')
            else:
                # Add the concatenation to the set
                concat_set.add(x['full_description'])

        return successful

    def custom_json_get_dataref_and_set_state(self):
        '''
        Read the JSON file into a dictionary and set states for Touch Portal
        '''
        successful = False
        
        logger.info(f'==> Trying to load json file from: {self.json_folder_location}')

        try:
            json_file = self.json_folder_location + self.json_file_name
            file = open(json_file, 'r')
            states_read = json.load(file)
            file.close()
            logger.info(f'==> Datarefs info successfully loaded from {json_file}')
            # append required and essential dataref
            self.states = self.custom_json_append_required_and_essential_dataref(states_read)
            # convert all keys to lowercase
            self.states = self.custom_json_convert_keys_to_lowercase(self.states)
            # create full description field
            self.states = self.custom_json_create_full_description_field(self.states)
            # validate keys and contents
            successful = self.custom_json_validate_keys()
            # validate keys and contents
            successful = self.custom_json_validate_datarefs_unique_descritions()
        
        except CustomErrorJson:
            raise # Bubbling up the exception
        
        except FileNotFoundError:
            raise CustomErrorJson(f'{json_file} does not exist')
        
        except ValueError as e:
            raise CustomErrorJson(f'Syntax error in {json_file}\nMessage: {e}')
        
        except Exception as e:
            error_report = format_exc()
            raise CustomErrorJson(f'Other Error for {json_file}\nMessage: {e}\nError report: {error_report}' )
        
        finally:
            if successful:
                logger.info(f'==> The JSON file: {json_file} is valid')

        return successful

    def touch_portal_client_find_id_from_desc_in_states(self, value_from_slider, min_value, max_value):
        """
        Find an ID and ajust a slider value against the minimum and maximum value
        """
        for x in self.states['datarefs']:
            if x['desc'] == desc:
                message = {}
                message['command'] = self.request_command_3_for_touch_portal

        ajusted_value = (value_from_slider / 100) * (max_value - min_value) + min_value

        return ajusted_value

    def touch_portal_client_find_value_against_slider_values(self, value_from_slider, min_value, max_value):
        """
        Ajust a slider value against the minimum and maximum value
        """
        ajusted_value = (value_from_slider / 100) * (max_value - min_value) + min_value

        return ajusted_value

    def touch_portal_client_process_on_action_set_custom_dataref_json_file(self, data):
        '''
        Set the custom dataref JSON file name for the Touch Portal page purpose 
        Get the dataref informations from this custom dataref JSON file and put it in states
        '''
        successful = False
        
        self.json_file_name = data.get('data')[0]['value'].strip()
        
        # for debugging only
        #logger.info(f'Custom json file = {self.json_file_name}')

        if not self.json_file_name:
            error_report = format_exc()
            raise CustomErrorJson(f'The custom JSON file name, in the touch portal page, must not be empty\nSee inside the "Not Loaded json" button\nError report: {error_report}')

        else:
            # Get the JSON file name without extension to display in page
            json_file_name_without_extension = os.path.splitext(self.json_file_name)[0]
            
            try:
                # Set states from custom JSON files that contains dataref info
                successful = self.custom_json_get_dataref_and_set_state()
            
            except Exception as e:
                raise # Bubbling up the exception

            else:
                if successful:
                    try:
                        logger.info(f'==>')
                        logger.info(f'==> ==================================================')
                        logger.info(f'==> Slider list by page, slider number and description')
                        logger.info(f'==> ==================================================')

                        # Sort slider list for displaying
                        self.short_connector_id_notification_list_for_log.sort(key=lambda x: (x['page'], x['connector_id'], x['description']))

                        # Displaying all slider by page; slider number and description into log
                        for entry in self.short_connector_id_notification_list_for_log:
                            logger.info(f"==> Page = {entry['page']} ; Connector Id = {entry['connector_id']} ; Short Id = {entry['short_id']} ; Description = {entry['description']}")

                        logger.info(f'==>')

                        state_id = 'xplane_plugin_for_touch_portal.CONNEXION.custom_json_file_name'
                        self.tp_api.stateUpdate(state_id, json_file_name_without_extension)
                        
                        state_id = 'xplane_plugin_for_touch_portal.CONNEXION.main_status'
                        self.current_main_status = XPlanePluginStatus.CUSTOM_JSON_LOADED
                        self.tp_api.stateUpdate(state_id, self.current_main_status) 
                    
                    except Exception as e:
                        error_report = format_exc()
                        raise CustomErrorPlugin(f'stateUpdate error\nMessage: {e}\nError report: {error_report}')
        
                    else:
                        # for debugging only
                        #logger.info(f'======================================================================')
                        #logger.info(f'Create touch portal states for each state_id from the custom json file')
                        #logger.info(f'======================================================================')

                        commands_choices_list = []
                        three_seconds_command_choices_list = []
                        state_ids_choices_list = []
                        state_ids_degree_list = []
                        state_ids_altitude_list = []
                        state_ids_sliders_list = []
                        
                        # ------------------------------------- 
                        # example for one state for one dataref
                        # ------------------------------------- 
                        # "id": "sim/cockpit2/controls/flap_ratio",
                        # "desc": "Flaps deploy ratio",
                        # "group": "FlightControls",
                        # "dataref": "sim/cockpit2/controls/flap_ratio",
                        # "touch_portal_format" :"",
                        # "xplane_update_min_value" :"",
                        # "xplane_update_max_value" :"",
                        # "accelerated_control" :"",
                        # "comment": "(1.0 = FULL, 20 deg = 0.67, 10 deg = 0.33, UP = 0.0 --> Some aircraft 0.5 = Approach)"

                        # in this following loop, create a new state variable "full_decription" for each state
                        # "full_decription": "group" - "desc" -> this is the group, dash, and the desc
                        # 
                        #
                        # -Process each dataref found in "states" (python dictionnary). 
                        # -Create States data
                        # -Feed ValueChoices
                        try:
                            for x in self.states['datarefs']:
                                
                                state_id = x['id']
                                state_desc = x['desc']
                                state_group = x['group']
                                state_dataref = x['dataref']
                                state_touch_portal_format = x['touch_portal_format']
                                state_xplane_update_min_value = x['xplane_update_min_value']
                                state_xplane_update_max_value = x['xplane_update_max_value']
                                state_accelerated_control = x['accelerated_control'].lower()
                                state_description = x['full_description']
                                state_value = '0' # for initialization part only   

                                # Create dynamic states
                                self.tp_api.createState(state_id, state_description, state_value, state_group)   
                                
                                # for debugging only
                                #logger.info(f"Create State -> {state_id}, {state_description}, {state_value}, {state_group}")

                                # For this slider group, check if there are any ids for a connector using this state_desc. 
                                # If so, enter the state_id in table
                                if state_group.lower() == 'slider':
                                    
                                    # for debugging only
                                    #logger.info("PASS CHANGE SLIDER TO LOWER")
                                    if state_desc in self.desc_with_short_connector_id:
                                        # for debugging only
                                        #logger.info(f"----------->>>>>>>>> xplane_client_managing_received_data_for_connector -> {state_id}, {state_description}")
                                        self.desc_with_short_connector_id[state_desc]['state_id'] = state_id # add state_id info here
                                        #force the slider value to 10% (if the slider is at -1%, it means the slider processing was not performed correctly (that's A Touch Portal Bug around slider))
                                        result = self.xplane_client_managing_received_data_for_connector(state_id, '0.1', True)                                    
                                
                                if '[CMD]' in state_dataref:
                                    commands_choices_list.append(state_desc)
                                    # for debugging only
                                    #logger.info(f"Create command choice -> {state_desc}")
                                elif '[CMD_3]' in state_dataref:
                                    three_seconds_command_choices_list.append(state_desc)
                                    # for debugging only
                                    #logger.info(f"Create hold command choice -> {state_desc}")
                                elif 'altitude' in state_accelerated_control:
                                    state_ids_altitude_list.append(state_description)
                                    # for debugging only
                                    #logger.info(f"Create altitude dataref choice -> {state_description}")
                                    # This is usual state_id lists for button
                                    state_ids_choices_list.append(state_description)
                                    # for debugging only
                                    #logger.info(f"Create dataref choice -> {state_description}")
                                elif 'degree' in state_accelerated_control:
                                    state_ids_degree_list.append(state_description)
                                    # for debugging only
                                    #logger.info(f"Create degree dataref choice -> {state_description}")
                                    # This is usual state_id lists for button
                                    state_ids_choices_list.append(state_description)
                                    # for debugging only
                                    #logger.info(f"Create dataref choice -> {state_description}")
                                elif state_group.lower() == 'slider':
                                    state_ids_sliders_list.append(state_desc)
                                    # for debugging only
                                    #logger.info(f"Create slider dataref choice -> {state_desc}")
                                else:
                                    # This is usual state_id lists for button
                                    state_ids_choices_list.append(state_description)
                                    # for debugging only
                                    #logger.info(f"Create dataref choice -> {state_description}")
                                
                                self.state_id_list.append(state_id)
                                state_id_and_format_list = {'state_id': state_id, 'dataref': state_dataref, 'touch_portal_format': state_touch_portal_format, 'xplane_update_min_value': state_xplane_update_min_value, 'xplane_update_max_value': state_xplane_update_max_value}
                                self.state_id_and_format_list.append(state_id_and_format_list) 

                                if (state_id == 'DO_NOT_DELETE.sim/cockpit2/gauges/actuators/barometer_setting_in_hg_pilot' or 
                                    state_id == 'DO_NOT_DELETE.sim/cockpit2/gauges/actuators/barometer_setting_in_hg_copilot' or 
                                    state_id == 'DO_NOT_DELETE.sim/cockpit2/gauges/actuators/barometer_setting_in_hg_stby'):
                                   self.xplane_client_managing_received_data_for_hpa_barometer_values(state_id, '0', True)

                            # The following is for internally calculated hPa values.
                            self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.COMPUTED.current_pilot_hpa.value','0')
                            self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.COMPUTED.current_copilot_hpa.value','0')
                            self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.COMPUTED.current_standard_hpa.value','0')

                        except Exception as e:
                            error_report = format_exc()
                            raise CustomErrorPlugin(f'stateUpdate error\nMessage: {e}\nError report: {error_report}')

                        else:
                            logger.info(f'==> Touch Portal dynamic States Created within state_id info')
                            
                            # ==============================================================================
                            # Feed all valueChoices for several actionID for each state_id: ref entry.tp file
                            # ==============================================================================
                            commands_choices_list.sort() # Sort options for ease of use in Touch Portal apps
                            three_seconds_command_choices_list.sort() # Sort options for ease of use in Touch Portal apps
                            
                            state_ids_altitude_list.sort() # Sort options for ease of use in Touch Portal apps
                            state_ids_degree_list.sort() # Sort options for ease of use in Touch Portal apps
                            state_ids_sliders_list.sort() # Sort options for ease of use in Touch Portal apps
                            
                            state_ids_choices_list.sort() # Sort options for ease of use in Touch Portal apps

                            try:
                                if commands_choices_list != []:
                                    # for debugging only                                    
                                    #logger.info("Append commands_choices_list")
                                    self.tp_api.choiceUpdate('xplane_plugin_for_touch_portal.COMMAND.execute.name', commands_choices_list) # Update choice for command desc at runtime
                                
                                if three_seconds_command_choices_list != []:
                                    # for debugging only                                    
                                    #logger.info("Append three_seconds_command_choices_list")
                                    self.tp_api.choiceUpdate('xplane_plugin_for_touch_portal.COMMAND_3.execute.name', three_seconds_command_choices_list) # Update choice for command_3 desc at runtime

                                if state_ids_altitude_list != []:
                                    # for debugging only                                    
                                    #logger.info("Append state_ids_altitude_list")
                                    self.tp_api.choiceUpdate('xplane_plugin_for_touch_portal.DATAREF.accelerated_altitude.name', state_ids_altitude_list) # Update choice for dataref desc at runtime

                                if state_ids_degree_list != []:
                                    # for debugging only                                    
                                    #logger.info("Append state_ids_degree_list")
                                    self.tp_api.choiceUpdate('xplane_plugin_for_touch_portal.DATAREF.accelerated_degree.name', state_ids_degree_list) # Update choice for dataref desc at runtime

                                if state_ids_sliders_list != []:  # Sliders 1 to 12 are the only ones allocated for this program
                                    # for debugging only                                    
                                    #logger.info("Append state_ids_sliders_list")
                                    self.tp_api.choiceUpdate('DATAREF.slider_1.name', state_ids_sliders_list) # Update choice for dataref desc at runtime
                                    self.tp_api.choiceUpdate('DATAREF.slider_2.name', state_ids_sliders_list) # Update choice for dataref desc at runtime
                                    self.tp_api.choiceUpdate('DATAREF.slider_3.name', state_ids_sliders_list) # Update choice for dataref desc at runtime
                                    self.tp_api.choiceUpdate('DATAREF.slider_4.name', state_ids_sliders_list) # Update choice for dataref desc at runtime
                                    self.tp_api.choiceUpdate('DATAREF.slider_5.name', state_ids_sliders_list) # Update choice for dataref desc at runtime
                                    self.tp_api.choiceUpdate('DATAREF.slider_6.name', state_ids_sliders_list) # Update choice for dataref desc at runtime
                                    self.tp_api.choiceUpdate('DATAREF.slider_7.name', state_ids_sliders_list) # Update choice for dataref desc at runtime
                                    self.tp_api.choiceUpdate('DATAREF.slider_8.name', state_ids_sliders_list) # Update choice for dataref desc at runtime
                                    self.tp_api.choiceUpdate('DATAREF.slider_9.name', state_ids_sliders_list) # Update choice for dataref desc at runtime
                                    self.tp_api.choiceUpdate('DATAREF.slider_10.name', state_ids_sliders_list) # Update choice for dataref desc at runtime
                                    self.tp_api.choiceUpdate('DATAREF.slider_11.name', state_ids_sliders_list) # Update choice for dataref desc at runtime
                                    self.tp_api.choiceUpdate('DATAREF.slider_12.name', state_ids_sliders_list) # Update choice for dataref desc at runtime
                                
                                if state_ids_choices_list != []:
                                    # for debugging only                                    
                                    #logger.info("Append state_ids_choices_list")
                                    self.tp_api.choiceUpdate('xplane_plugin_for_touch_portal.DATAREF.set_states.name', state_ids_choices_list) # Update choice for dataref desc at runtime
                                    self.tp_api.choiceUpdate('xplane_plugin_for_touch_portal.DATAREF.slider.name', state_ids_choices_list) # Update choice for dataref desc at runtime
        
                            except Exception as e:
                                error_report = format_exc()
                                raise CustomErrorPlugin(f'choiceUpdate error\nMessage: {e}\nError report: {error_report}')

                            else:
                                logger.info(f'==> Touch Portal Choices have been updated for some action within state_id desc field')
                                self.state_id_list.sort() # Sorted statte_id will be use for comparaison
                                self.nb_entries_state_id_list = len(self.state_id_list) # Keep datarefs occurence count

    def touch_portal_client_process_on_action_start_communication_with_xplane_server(self):
        '''
        Start the communication with the X-Plane server 
        '''
        try:
            self.xplane_client_communicate_with_xplane_server()
    
        except Exception as e:
            raise # Bubbling up the exception


    def touch_portal_client_process_on_action_stop_communication_with_xplane_server(self):
        '''
        Stop the communication with the X-Plane server 
        '''
        try:
            self.xplane_client_stop_communicate_with_xplane_server()
    
        except Exception as e:
            raise # Bubbling up the exception

    def touch_portal_client_process_on_action_dataref_set_states(self, data):
        '''
        Set states value and send it to X-Plane server 
        '''
        full_description = data.get('data')[0]['value']
        new_value = data.get('data')[1]['value']

        for x in self.states['datarefs']:
            if x['full_description'] == full_description:
                state_id = x['id']
                
                try:
                    if self.tp_api.currentStates[state_id] != new_value:
                        self.tp_api.stateUpdate(state_id, new_value) # Update the value in Touch Portal State

                except BufferError:
                    break # skip any buffer error
                
                except Exception as e:
                    error_report = format_exc()
                    raise CustomErrorPlugin(f'stateUpdate error\nMessage: {e}\nError report: {error_report}')
                
                else: 
                    # for debugging only                       
                    #logger.info(f"===================")
                    #logger.info(f"State Update with : {state_id} with value {new_value}")
                    #logger.info(f"===================")
                    
                    message = {}
                    message['command'] = self.request_update_from_touch_portal
                    message['state_id'] = state_id
                    message['value'] = new_value
                    outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
                    self.shared_data_container.outb += outgoing_message.encode('utf-8')                    
                    break

    def touch_portal_client_process_on_action_command_execute(self, data):
        '''
        Send an X-Plane command to X-Plane server 
        '''
        desc = data.get('data')[0]['value']

        for x in self.states['datarefs']:
            if x['desc'] == desc:
                message = {}
                message['command'] = self.request_command_for_touch_portal
                message['state_id'] = x['id']
                outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
                self.shared_data_container.outb += outgoing_message.encode('utf-8')                    
                break

    def touch_portal_client_process_on_action_command_3_execute(self, data):
        '''
        Send an X-Plane command to X-Plane server 
        '''
        desc = data.get('data')[0]['value']

        for x in self.states['datarefs']:
            if x['desc'] == desc:
                message = {}
                message['command'] = self.request_command_3_for_touch_portal
                message['state_id'] = x['id']
                outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
                self.shared_data_container.outb += outgoing_message.encode('utf-8')                    
                break

    def touch_portal_client_process_on_hold_down_accelerated_degree(self, data):
        '''
        Proceed the Touch Portal 'on hold_down' event for DEGREE states 
        '''
        
        # do not allow this control's thread to be executed if it is currently running
        if self.DegreeControlInstance.thread and self.DegreeControlInstance.thread.is_alive():
            return

        full_description = data.get('data')[0]['value']
        adjustment_mode = data.get('data')[1]['value']
        update_mode = data.get('data')[2]['value']
        
        state_id = None
        
        for x in self.states['datarefs']:
            if x['full_description'] == full_description:
                state_id = x['id']
                break

        if state_id:
            self.DegreeControlInstance.start_adjustment(adjustment_mode, state_id, float(self.tp_api.currentStates[state_id]), 1, 30, update_mode)

    def touch_portal_client_process_on_hold_up_accelerated_degree(self, data):
        '''
        Proceed the Touch Portal 'on hold_up' event for DEGREE states 
        '''
        try:
            self.DegreeControlInstance.stop_adjustment()

        except Exception as e:
            raise # Bubbling up the exception

    def touch_portal_client_process_on_hold_down_accelerated_altitude(self, data):
        '''
        Proceed the Touch Portal 'on hold_down' event for ALTITUDE states 
        '''
        
        # do not allow this control's thread to be executed if it is currently running
        if self.AltitudeControlInstance.thread and self.AltitudeControlInstance.thread.is_alive():
            return

        full_description = data.get('data')[0]['value']
        adjustment_mode = data.get('data')[1]['value']
        update_mode = data.get('data')[2]['value']
        
        state_id = None
        
        for x in self.states['datarefs']:
            if x['full_description'] == full_description:
                
                state_id = x['id']
                break

        if state_id:
            self.AltitudeControlInstance.start_adjustment(adjustment_mode, state_id, float(self.tp_api.currentStates[state_id]), 100, 1000, update_mode)

    def touch_portal_client_process_on_hold_up_accelerated_altitude(self, data):
        '''
        Proceed the Touch Portal 'on hold_up' event for ALTITUDE states 
        '''
        try:
            self.AltitudeControlInstance.stop_adjustment()

        except Exception as e:
            raise # Bubbling up the exception

    def touch_portal_client_process_on_connect(self, data):
        '''
        Proceed the Touch Portal 'on connect' event 
        '''
        logger.info(f'==> Connected to Touch Portal Version {data.get("tpVersionString", "?????")} plugin v {data.get("pluginVersion", "?????")}')
        
        # Feed the current page path value to the slider control
        temp_current_page_path_main_device = data.get("currentPagePathMainDevice", "?????")
        self.current_page_path_main_device = temp_current_page_path_main_device.replace('\\','').replace('.tml','')

        self.current_main_status = XPlanePluginStatus.CONNECTED_TO_TOUCH_PORTAL

        try:
            self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.CONNEXION.main_status', self.current_main_status) 
            self.tp_api.choiceUpdate('DATAREF.slider_1.cur_page', [self.current_page_path_main_device]) 
            self.tp_api.choiceUpdate('DATAREF.slider_2.cur_page', [self.current_page_path_main_device]) 
            self.tp_api.choiceUpdate('DATAREF.slider_3.cur_page', [self.current_page_path_main_device]) 
            self.tp_api.choiceUpdate('DATAREF.slider_4.cur_page', [self.current_page_path_main_device]) 
            self.tp_api.choiceUpdate('DATAREF.slider_5.cur_page', [self.current_page_path_main_device]) 
            self.tp_api.choiceUpdate('DATAREF.slider_6.cur_page', [self.current_page_path_main_device]) 
            self.tp_api.choiceUpdate('DATAREF.slider_7.cur_page', [self.current_page_path_main_device]) 
            self.tp_api.choiceUpdate('DATAREF.slider_8.cur_page', [self.current_page_path_main_device]) 
            self.tp_api.choiceUpdate('DATAREF.slider_9.cur_page', [self.current_page_path_main_device]) 
            self.tp_api.choiceUpdate('DATAREF.slider_10.cur_page', [self.current_page_path_main_device]) 
            self.tp_api.choiceUpdate('DATAREF.slider_11.cur_page', [self.current_page_path_main_device]) 
            self.tp_api.choiceUpdate('DATAREF.slider_12.cur_page', [self.current_page_path_main_device]) 

        except Exception as e:
            error_report = format_exc()
            raise CustomErrorPlugin(f'stateUpdate error\nMessage: {e}\nError report: {error_report}')

    def touch_portal_client_process_short_connector_id_notification(self, data):
        '''
        Proceed the Touch Portal 'shortConnectorIdNotification' event 
        keep the ShortConnectorID and desc fields in a dictionnary for later use 
        when reading the custom JSON file and creating states 
        '''

        if data.get("pluginId") != PLUGIN_ID:
            return 

        substring_to_remove = 'pc_' + PLUGIN_ID + '_'
        short_id = data.get("shortId") 
        connector_id_info = data.get("connectorId") 

        parts = connector_id_info.split('|')

        desc = None
        connector_id = None 
        current_page_path_main_device = "???"

        for index, part in enumerate(parts):

            if index == 0:
                connector_id = part.replace(substring_to_remove, '')

            if index == 1:
                if '=' in part:
                    key, value = part.split('=',1)
                    desc = value 

            if index == 2:
                if '=' in part:
                    key, value = part.split('=',1)
                    current_page_path_main_device = value 

        if self.current_page_path_main_device == current_page_path_main_device:
            if desc in self.desc_with_short_connector_id:
                if connector_id not in self.desc_with_short_connector_id[desc]['connector_id']:
                    self.desc_with_short_connector_id[desc]['connector_id'].append(connector_id)
                if short_id not in self.desc_with_short_connector_id[desc]['short_id']:
                    self.desc_with_short_connector_id[desc]['short_id'].append(short_id)
                self.desc_with_short_connector_id[desc]['state_id'] = None # create a place for a state_id entry
            else:
                self.desc_with_short_connector_id[desc] = {
                    'connector_id': [connector_id],
                    'short_id': [short_id],
                    'state_id': None  # create a place for a state_id entry
                }

        self.short_connector_id_notification_list_for_log.append({"page": current_page_path_main_device, "connector_id": connector_id, "short_id": short_id, "description": desc})
        
        # use the following for debugging only
        #logger.info(f'==> SHORT CONNECTOR ID NOTIFICATION with CONNECTOR_ID: {connector_id} SHORT_ID: {short_id} IN PAGE: {current_page_path_main_device} WITH: {desc}')

    def touch_portal_client_process_on_action(self, data):
        '''
        Proceed the Touch Portal 'on action' event 
        '''

        # use the following for debugging only
        #logger.info(f'==> [ON_ACTION] : {data}')

        # Dispatch Touch Portal Action Id (see inside entry.tp for that)
        action_id = data.get('actionId')
        value = data.get('data')[0]['value']

        match action_id:

            case 'xplane_plugin_for_touch_portal.PLUGIN.set_is_connected_to':

                self.plugin_is_connected = value

                try:
                    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.CONNEXION.is_connected', self.plugin_is_connected)

                except Exception as e:
                    error_report = format_exc()
                    raise CustomErrorPlugin(f'stateUpdate error\nMessage: {e}\nError report: {error_report}')

            case 'xplane_plugin_for_touch_portal.PLUGIN.set_main_status_to':

                self.current_main_status = value

                try:
                    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.CONNEXION.main_status', self.current_main_status)

                except Exception as e:
                    error_report = format_exc()
                    raise CustomErrorPlugin(f'stateUpdate error\nMessage: {e}\nError report: {error_report}')

            case 'xplane_plugin_for_touch_portal.PLUGIN.set_custom_dataref_json_file':

                # use the following for debugging only
                #logger.info(f'====================================')
                #logger.info(f'ACTION: Proceed the custom JSON file')
                #logger.info(f'====================================')

                try:
                    self.touch_portal_client_process_on_action_set_custom_dataref_json_file(data)
                
                except Exception as e:
                    raise # Bubbling up the exception

            case 'xplane_plugin_for_touch_portal.PLUGIN.start_communication_with_server':

                start_communication_with_server = value
                
                if start_communication_with_server == 'Yes':
                    # use the following for debugging only
                    #logger.info(f'===================================================')
                    #logger.info(f'ACTION: start communication with the X-Plane server')
                    #logger.info(f'===================================================')
                    
                    try:
                        self.touch_portal_client_process_on_action_start_communication_with_xplane_server()
                
                    except Exception as e:
                        raise # Bubbling up the exception

                else:
                    # use the following for debugging only
                    #logger.info(f'==================================================')
                    #logger.info(f'ACTION: stop communication with the X-Plane server')
                    #logger.info(f'==================================================')

                    try:
                        self.touch_portal_client_process_on_action_stop_communication_with_xplane_server()
                
                    except Exception as e:
                        raise # Bubbling up the exception

            case 'xplane_plugin_for_touch_portal.DATAREF.set_states':

                # use the following for debugging only
                #logger.info(f'==================================================')
                #logger.info(f'ACTION: send a dataref value to the X-Plane server')
                #logger.info(f'==================================================')
                
                try:
                    self.touch_portal_client_process_on_action_dataref_set_states(data)
                
                except Exception as e:
                    raise # Bubbling up the exception

            case 'xplane_plugin_for_touch_portal.COMMAND.execute':

                # use the following for debugging only
                #logger.info(f'==========================================================')
                #logger.info(f'ACTION: send an X-Plane command to the X-Plane server')
                #logger.info(f'==========================================================')

                try:
                    self.touch_portal_client_process_on_action_command_execute(data)
                
                except Exception as e:
                    raise # Bubbling up the exception

            case 'xplane_plugin_for_touch_portal.COMMAND_3.execute':

                # use the following for debugging only
                #logger.info(f'===============================================================')
                #logger.info(f'ACTION: send an X-Plane command_3 to the X-Plane server')
                #logger.info(f'===============================================================')

                try:
                    self.touch_portal_client_process_on_action_command_3_execute(data)
                
                except Exception as e:
                    raise # Bubbling up the exception

            case _:
                '''
                Exception action id not found
                '''
                error_report = format_exc()
                raise CustomErrorPlugin(f'There is no action id like the following \n{action_id}\nError report: {error_report}')

    def touch_portal_client_process_on_hold_down(self, data):
        '''
        Proceed the Touch Portal 'on hold_down' event 
        '''
        
        # For debugging only
        #logger.info(f'==> [ON_HOLD_DOWN] : {data}')

        # Dispatch Touch Portal Action Id (see inside entry.tp for that)
        action_id = data.get('actionId')

        match action_id:

            case 'xplane_plugin_for_touch_portal.DATAREF.accelerated_degree':

                # use the following for debugging only
                #logger.info(f'====================================')
                #logger.info(f'ACTION: Proceed the accelarated control category "DEGREE"')
                #logger.info(f'====================================')

                try:
                    self.touch_portal_client_process_on_hold_down_accelerated_degree(data)
                    
                except Exception as e:
                    raise # Bubbling up the exception

            case 'xplane_plugin_for_touch_portal.DATAREF.accelerated_altitude':

                # use the following for debugging only
                #logger.info(f'====================================')
                #logger.info(f'ACTION: Proceed the accelarated control category "ALTITUDE"')
                #logger.info(f'====================================')

                try:
                    self.touch_portal_client_process_on_hold_down_accelerated_altitude(data)
                    
                except Exception as e:
                    raise # Bubbling up the exception

            case _:
                '''
                Exception action id not found
                '''
                error_report = format_exc()
                raise CustomErrorPlugin(f'There is no action id like the following \n{action_id}\nError report: {error_report}')

    def touch_portal_client_process_on_hold_up(self, data):
        '''
        Proceed the Touch Portal 'on hold_down' event 
        '''
        
        # for debugging only
        #logger.info(f'==> [ON_HOLD_UP] : {data}')

        # Dispatch Touch Portal Action Id (see inside entry.tp for that)
        action_id = data.get('actionId')

        match action_id:

            case 'xplane_plugin_for_touch_portal.DATAREF.accelerated_degree':

                # use the following for debugging only
                #logger.info(f'====================================')
                #logger.info(f'ACTION: Proceed the stop accelarated control category "DEGREE"')
                #logger.info(f'====================================')

                try:
                    self.touch_portal_client_process_on_hold_up_accelerated_degree(data)
                    
                except Exception as e:
                    raise # Bubbling up the exception

            case 'xplane_plugin_for_touch_portal.DATAREF.accelerated_altitude':

                # use the following for debugging only
                #logger.info(f'====================================')
                #logger.info(f'ACTION: Proceed the stop accelarated control category "ALTITUDE"')
                #logger.info(f'====================================')

                try:
                    self.touch_portal_client_process_on_hold_up_accelerated_altitude(data)
                    
                except Exception as e:
                    raise # Bubbling up the exception
                    
            case _:
                '''
                Exception action id not found
                '''
                error_report = format_exc()
                raise CustomErrorPlugin(f'There is no action id like the following \n{action_id}\nError report: {error_report}')

    def touch_portal_client_process_on_connector_change(self, data):
        '''
        Proceed the Touch Portal 'on connector change' event 
        '''
        
        # use the following for debugging only
        #logger.info(f'==> [ON_CONNECTOR_CHANGE] : {data}')

        # Dispatch Touch Portal Connector Id (see inside entry.tp for that)
        connector_id = data.get('connectorId')
        desc = data.get('data')[0]['value']
        value_from_slider = data.get('value')

        match connector_id:

            case 'DATAREF.slider_1' | \
                 'DATAREF.slider_2' | \
                 'DATAREF.slider_3' | \
                 'DATAREF.slider_4' | \
                 'DATAREF.slider_5' | \
                 'DATAREF.slider_6' | \
                 'DATAREF.slider_7' | \
                 'DATAREF.slider_8' | \
                 'DATAREF.slider_9' | \
                 'DATAREF.slider_10' | \
                 'DATAREF.slider_11' | \
                 'DATAREF.slider_12':

                for x in self.states['datarefs']:
                    if x['desc'] == desc:
                        
                        state_id = x['id']
                        min_value = float(x['xplane_update_min_value']) if x['xplane_update_min_value'] != '' else 0
                        max_value = float(x['xplane_update_max_value']) if x['xplane_update_max_value'] != '' else 1
                        
                        ajusted_value = self.touch_portal_client_find_value_against_slider_values(value_from_slider, float(min_value), float(max_value))
                        ajusted_value = str(ajusted_value)

                        try:
                            if self.tp_api.currentStates[state_id] != ajusted_value:
                                self.tp_api.stateUpdate(state_id, ajusted_value) # Update the state_id value in Touch Portal State

                        except BufferError:
                            break # skip any buffer error
                        
                        else:    
                            # use the following for debugging only
                            #logger.info(f"===================")
                            #logger.info(f"State Update with : {state_id} with value {ajusted_value}")
                            #logger.info(f"===================")
                            
                            message = {}
                            message['command'] = self.request_update_from_touch_portal
                            message['state_id'] = state_id
                            message['value'] = ajusted_value
                            outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
                            self.shared_data_container.outb += outgoing_message.encode('utf-8')                    
                            break

            case _:
                '''
                Exception connector id not found
                '''
                error_report = format_exc()
                raise CustomErrorPlugin(f'There is no connector id like the following \n{action_id}\nError report: {error_report}')

    def touch_portal_client_process_on_shutdown(self, data):
        '''
        Proceed the Touch Portal 'on shutdown' event. When Touch Portal tries to close plugin normally or on error
        '''

        # for debugging only
        #logger.info(f'==> [ON_SHUTDOWN] : {data}')
        pass
        
    def touch_portal_client_process(self):
        '''
        Proceed all Touch Portal events (Main process for Touch Portal)
        '''
        successful = False

        # Create an object concerning the Touch Portal API client for the following decorator @
        tp_api = self.tp_api

        # This event handler will run once when the client connects to Touch Portal
        @tp_api.on(self.on_connect)
        @self.with_error_handling 
        def onConnect(data):

            self.touch_portal_client_process_on_connect(data)

        # Immediatly after a on_connect event, there's a shortConnectorIdNotification if there's any define slider.
        @tp_api.on(self.shortConnectorIdNotification) 
        def shortConnectorIdNotification(data):

            self.touch_portal_client_process_short_connector_id_notification(data)
        
        # Action handlers, called when user activates one of this plugin's actions in Touch Portal.
        @tp_api.on(self.on_action)
        @self.with_error_handling 
        def onAction(data):

            self.touch_portal_client_process_on_action(data)

        # Hold Down handlers for Touch Portal.
        @tp_api.on(self.on_hold_down)
        @self.with_error_handling 
        def onHoldDown(data):

            self.touch_portal_client_process_on_hold_down(data)

        # Hold Up handlers for Touch Portal.
        @tp_api.on(self.on_hold_up)
        @self.with_error_handling 
        def onHoldUp(data):

            self.touch_portal_client_process_on_hold_up(data)

        # Connector Change handlers (sliders) for Touch Portal.
        @tp_api.on(self.on_connector_change) 
        @self.with_error_handling
        def onConnectorChange(data):
        
            # update only when server up and running
            if self.keep_running.is_set() and self.current_main_status == XPlanePluginStatus.X_PLANE_CLIENT_CONNECTED_TO_X_PLANE_SERVER:
                self.touch_portal_client_process_on_connector_change(data)

        # On error handler.
        @tp_api.on(self.on_error) 
        def onError(data):

            logger.info(f'==> [ON_ERROR HANDLER FROM TP SERVER] : {data}')

        # Shutdown handler, called when Touch Portal wants to stop your plugin.
        @tp_api.on(self.on_shutdown) 
        def onShutdown(data):

            self.touch_portal_client_process_on_shutdown(data)
        
        try:
            logger.info(f'==> Trying to connect to Touch Portal Apps')
            self.tp_api.connect()
        except KeyboardInterrupt:
            logger.warning('==> WARNING -> Caught keyboard interrupt, exiting.')
        except ConnectionRefusedError:
            logger.error(f'==> ERROR -> TOUCH PORTAL\nCannot connect to Touch Portal\nProbably it is not running')
        except Exception as e:
            error_report = format_exc()
            logger.error(f'==> ERROR -> TOUCH PORTAL\nMessage: {e}\nError report: {error_report}' )
        else:
            logger.info(f'==> TP Client Disconnected')
            successful = True
        finally:
            self.keep_running.clear()
            self.tp_api.disconnect()

        return successful

    def xplane_client_connect(self):
        '''
        Establish a connection between this client and the X-Plane server. 
        '''
        successful = True

        try:    
            self.client_socket.connect((self.host,self.port))
        except socket.error as e:
            error_report = format_exc()
            error_message = str(e).encode('utf-8').decode('utf-8')            
            self.custom_error_xplane_queue.put(f'\n*** X-Plane server is not running ***\n \nMessage: {e}\nError report: {error_report}')            
            self.keep_running.clear()
            successful = False

        return successful

    def xplane_client_managing_received_data_for_hpa_barometer_values(self, state_id:str, value:str, init = False):
        '''
        Process the received hpa barometer data update
        '''
        new_value = value

        match state_id:

            case 'DO_NOT_DELETE.sim/cockpit2/gauges/actuators/barometer_setting_in_hg_pilot':

                if init == False:
                    float_value = float(value)
                    new_value = str(round(float_value * 33.8639))

                if self.tp_api.currentStates[state_id] != new_value:
                    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.COMPUTED.current_pilot_hpa.value',new_value)

                if init == False:
                    if value == self.tp_api.currentStates['DO_NOT_DELETE.sim/cockpit2/gauges/actuators/barometer_setting_in_hg_stby']:
                        self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.TOGGLE.is_standard_barometer.value','Yes')
                    else:
                        self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.TOGGLE.is_standard_barometer.value','No')

            case 'DO_NOT_DELETE.sim/cockpit2/gauges/actuators/barometer_setting_in_hg_copilot':

                if init == False:
                    float_value = float(value)
                    new_value = str(round(float_value * 33.8639))

                if self.tp_api.currentStates[state_id] != new_value:
                    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.COMPUTED.current_copilot_hpa.value',new_value)

            case 'DO_NOT_DELETE.sim/cockpit2/gauges/actuators/barometer_setting_in_hg_stby':

                if init == False:
                    float_value = float(value)
                    new_value = str(round(float_value * 33.8639))

                if self.tp_api.currentStates[state_id] != new_value:
                    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.COMPUTED.current_standard_hpa.value',new_value)

    def xplane_client_managing_received_data_for_connector(self, state_id:str, value:str, init = False):
        '''
        Process the received connector data update
        '''
        connector_found = False

        for desc, info in self.desc_with_short_connector_id.items():

            if info['state_id'] == state_id:
                percent_value = int(float(value) * 100)
                matching_connector_ids = info['short_id']

                for short_id in matching_connector_ids:
                    # for debugging only
                    #logger.info(f"STATE ID = {state_id} AND CURRENT VALUE STATES[STATE_ID] {self.tp_api.currentStates[state_id]} WITH {percent_value}")
                    if int(self.tp_api.currentStates[state_id]) != percent_value or init:
                        try:
                            # for debugging only
                            #logger.info(f"UDATE CONNECTOR ID {short_id} WITH {percent_value}")
                            self.tp_api.shortIdUpdate(short_id, percent_value)  # update the short id with a value
                            self.tp_api.stateUpdate(state_id, str(percent_value))
                            connector_found = True
                        except Exception as e:
                            raise # Bubbling up the exception
                    #else:
                        # For debugging only
                        #logger.info(f"NO UPDATE FOR STATE_ID {state_id} AND SHORT CONNECTOR ID {short_id}")

                break

        return connector_found

    def xplane_client_treat_value_from_xplane_server(self, state_id, value, touch_portal_format):
        '''
        Reformat value depending the touch_portal_format
        '''
        try:
            if touch_portal_format.lower() == 'd1':
                value_str = str(value)
                point_pos = value_str.find('.')

                if point_pos != -1:
                    truncated_str = value_str[:point_pos + 2]
                    truncated_value = float(truncated_str)
                else:
                    truncated_value = float(value_str)

                str_value = str(truncated_value)
                value = str_value

            elif touch_portal_format.lower() == 'd2':
                int_value = int(value)
                value = "{:.2f}".format(int_value / 100)

            elif touch_portal_format.lower() == 'd3':
                int_value = int(value)
                value = "{:.3f}".format(int(value) / 1000)

            elif touch_portal_format.lower() == 'nd':
                float_value = float(value)
                int_value = int(float_value * 100)
                value = str(int_value)

        except Exception as e:
            error_report = format_exc()
            self.custom_error_xplane_queue.put(f'This state_id: "{state_id}" has a conversion issue with its value: "{value}" OR it simply refers to a non-existent state_id.\nMessage: {e}\nError report: {error_report}')  
            self.keep_running.clear()
        else:
            return value

    def xplane_client_managing_received_data(self, message_decode):
        '''
        Process the received data packet from the X-Plane server
        '''
        try:
            message_object = json.loads(message_decode)
            keys = list(message_object.keys())

            # Process a response for the current state_id value in X-Plane (initialization part)
            # N.B: update the states in Touch Portal later from theses ingoing state_id values
            if message_object['command'] == self.response_state_id_value and set(keys) == set(self.response_state_id_value_paquet):

                # for debugging only
                #logger.info(f'INITIALIZATION state_id: {message_object["state_id"]} and value: {message_object["value"]}')
                self.state_id_list_initialized.append(message_object['state_id'])
                self.state_id_and_values_dictionary.update({message_object['state_id']:message_object['value']})

            # Process a reponse in case the initialization part is completed  
            elif message_object['command'] == self.response_initialization_done and set(keys) == set(self.response_initialization_done_paquet):
                # for debugging only
                #logger.info(f'Message from the server: {message_object["message"]}')
                pass
            # Process a reponse in case a state_id value has been updated in Touch Portal 
            elif message_object['command'] == self.response_update_from_touch_portal and set(keys) == set(self.response_update_from_touch_portal_paquet):
                # for debugging only
                #logger.info(f'Message from the server: {message_object["message"]}')
                pass

            # Process a request from the server concerning because a state_id value has been updated in X-Plane    
            elif message_object['command'] == self.request_update_from_x_plane and set(keys) == set(self.request_update_from_x_plane_paquet):
                state_id = message_object['state_id']
                value = message_object['value']

                one_id = state_id
                one_value = value
                one_format = None
                connector_found = False

                for item in self.state_id_and_format_list:
                    if item['state_id'] == one_id:
                        one_format = item['touch_portal_format']
                        break

                try:
                    reformat_value = self.xplane_client_treat_value_from_xplane_server(one_id, one_value, one_format)
                    # Do a connectorUpdate if the state_id in inside self.desc_with_short_connector_id dictionnary
                    connector_found = self.xplane_client_managing_received_data_for_connector(state_id, reformat_value)                 
                    # Update the HPA barometer values
                    self.xplane_client_managing_received_data_for_hpa_barometer_values(state_id, reformat_value)                 
                except:
                    raise # Bubbling the exception

                if self.tp_api.currentStates[state_id] != reformat_value and not connector_found:
                    self.tp_api.stateUpdate(state_id,reformat_value)
                
                # Send a response to the server
                message = {}
                message['command'] = self.response_update_from_x_plane
                message['state_id'] = state_id
                message['message'] = 'States updated successfully'
                outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
                self.shared_data_container.outb += outgoing_message.encode('utf-8')                    

            # Process a reponse in case a command has been processed in Touch Portal 
            elif message_object['command'] == self.response_command_for_touch_portal and set(keys) == set(self.response_command_for_touch_portal_paquet):

                # for debugging only
                #logger.info(f'Message from the server: {message_object["message"]}')
                pass

            # Process a reponse in case a command_3 has been processed in Touch Portal 
            elif message_object['command'] == self.response_command_3_for_touch_portal and set(keys) == set(self.response_command_3_for_touch_portal_paquet):

                # for debugging only
                #logger.info(f'Message from the server: {message_object["message"]}')
                pass

            else:
                command = message_object['command']
                raise ValueError(f'This response is not part of the communication chart between the \n X-Plane client and the X-Plane server.\nThe following command has been rejected\n{command}' )

        except json.JSONDecodeError as e:            
            error_report = format_exc()
            self.custom_error_xplane_queue.put(f'There is JSON decode error in {message_decode}\nMessage: {e}\nError report: {error_report}')            
            self.keep_running.clear()
        except ValueError as e:
            self.custom_error_xplane_queue.put(str(e))            
            self.keep_running.clear()
            raise # Bubbling the exception
        except Exception as e:
            error_report = format_exc()
            self.custom_error_xplane_queue.put(f'There is exception in xplane_client_managing_received_data\nMessage: {e}\nError report: {error_report}')            
            self.keep_running.clear()

    def xplane_client_service_connection(self, key, mask):
        '''
        Managing sockets, selectors, received data and data to be sent.
        '''
        if self.init_phase_running.is_set():
            BUFFER_SIZE = BUFFER_SIZE_INIT
        else:
            BUFFER_SIZE = BUFFER_SIZE_USUAL

        server_socket = key.fileobj
        data = key.data #  data is a reference to the self.shared_data_container object 

        if mask & selectors.EVENT_READ:
            try:
                ingoing_message = server_socket.recv(BUFFER_SIZE)
            except BlockingIOError:
                pass  # Resource temporarily unavailable (errno EWOULDBLOCK)
            except:
                raise # Bubbling the exception
            else:
                if ingoing_message:
                    data.inb += ingoing_message
                    # Each command contain a MESSAGE_DELIMITER at the end. Easy for separate commands
                    while MESSAGE_DELIMITER.encode('utf-8') in data.inb:
                        pos = data.inb.index(bytes(MESSAGE_DELIMITER, 'utf-8'))
                        message_bytes  = data.inb[:pos]  # The first message
                        data.inb = data.inb[pos+len(MESSAGE_DELIMITER):]  # Remove the first message from data.inb (message+'#') 
                        message_decode = message_bytes.decode('utf-8') 
                        if not message_decode:
                            continue # probably catch only the delimiter
                        else: 
                            self.xplane_client_managing_received_data(message_decode)
                else:
                    raise # Bubbling the exception

        if mask & selectors.EVENT_WRITE:
            try:
                if data.outb:
                    while data.outb:
                        if len(data.outb) <= BUFFER_SIZE and data.outb[-1] == ord('#'):
                            sent = server_socket.send(data.outb)  # Send the entire buffer
                            data.outb = data.outb[sent:]
                        else:
                            send_chunk = data.outb[:BUFFER_SIZE]
                            if send_chunk[-1] == ord('#'):
                                sent = server_socket.send(send_chunk)
                                data.outb = data.outb[sent:]
                            else:
                                last_hash_index = send_chunk.rfind(ord('#'))
                                if last_hash_index != -1:
                                    send_chunk = data.outb[:last_hash_index+1]
                                    sent = server_socket.send(send_chunk)
                                    data.outb = data.outb[sent:]
                                else:
                                    # No delimiter found
                                    error_report = format_exc()
                                    self.custom_error_xplane_queue.put(f'Problem: Sending message without #: {data.outb}\nError report: {error_report}')            
                                    self.keep_running.clear()

            except Exception as e:
                error_report = format_exc()
                self.custom_error_xplane_queue.put(f'Sending Error\nMessage: {e}\nError report: {error_report}')            
                self.keep_running.clear()

    def xplane_client_treat_init_phase(self):
        '''
        Send each dataref + touch_portal_format that come from the JSON file to the X-Plane server for receiving it's value
        within or without format. By default, the value format for each float data is set with two decimal only
        '''
        if not self.init_phase_done.is_set():
            for item in self.state_id_and_format_list:
                # Prepare a request_state_id_value for the X-Plane server
                message = {}

                message['command'] = self.request_state_id_value
                message['state_id'] = item['state_id']
                message['dataref'] = item['dataref']
                message['xplane_update_min_value'] = item['xplane_update_min_value']
                message['xplane_update_max_value'] = item['xplane_update_max_value']
                outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
                self.shared_data_container.outb += outgoing_message.encode('utf-8')                    

            # Tell the server that the initialization commands have been completed. 
            # The server will then start a thread to check every second if the user press a command on the X-Plane side. 
            # Then, with this thread, the server will send the updated data to refresh the Touch Portal status and screen.  
            message = {}
            message['command'] = self.request_initialization_done
            outgoing_message = json.dumps(message) + MESSAGE_DELIMITER
            self.shared_data_container.outb += outgoing_message.encode('utf-8')                    

        else:
            # Make sure that every state_id from the state_id_list are initialized by the X-Plane server
            self.nb_entries_state_id_list_initialized = len(self.state_id_list_initialized) 
            if self.nb_entries_state_id_list_initialized == self.nb_entries_state_id_list:
                self.state_id_list_initialized.sort()
                if self.state_id_list_initialized == self.state_id_list:
                    # Every state_id passed through initialization
                    logger.info(f'==> Datarefs initialization processing was completed correctly')
                    # Update values that come from the X-Plane server for each state_id
                    for state_id in self.state_id_and_values_dictionary:
                        one_id = state_id
                        one_value = self.state_id_and_values_dictionary[state_id]
                        one_format = None
                        connector_found = False

                        for item in self.state_id_and_format_list:
                            if item['state_id'] == one_id:
                                one_format = item['touch_portal_format']
                                break

                        try:
                            reformat_value = self.xplane_client_treat_value_from_xplane_server(one_id, one_value, one_format)

                            connector_found = self.xplane_client_managing_received_data_for_connector(one_id, reformat_value)                 

                            self.xplane_client_managing_received_data_for_hpa_barometer_values(one_id, reformat_value)                 
                        except:
                            raise # Bubbling the exception

                        if self.tp_api.currentStates[state_id] != reformat_value and not connector_found:
                            self.tp_api.stateUpdate(state_id,reformat_value)

                    logger.info(f'==> State update completed for the initialization part')
                    
                    # X-Plane Client connected to X-Plane server AND
                    # when the X-Plane client receives the current state_id values from the X-Plane server (initialization)
                    self.current_main_status = XPlanePluginStatus.X_PLANE_CLIENT_CONNECTED_TO_X_PLANE_SERVER 
                    self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.CONNEXION.main_status', self.current_main_status) 
                    self.init_phase_running.clear()
                    BUFFER_SIZE = BUFFER_SIZE_USUAL
                else:
                    logger.error(f'==> ERROR -> There are initialization problem')
                    logger.error(f'==> ERROR -> Datarefs initialization processing was not completed correctly')
                    self.init_phase_running.clear()

        self.init_phase_done.set()

    def xplane_client_run(self):
        '''
        Handling selectors in communication with xplane server
        '''
        # The mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        try:
            for key, mask in self.client_selectors.select(timeout=0.1):
                if self.keep_running.is_set():
                    self.xplane_client_service_connection(key, mask)
                if self.init_phase_running.is_set():
                    self.xplane_client_treat_init_phase()

        except:
            raise # Bubbling the exception

    def xplane_client_shutting_down(self):
        '''
        Processing the client closure /procedure
        '''
        try:
            logger.info(f'==> shutting_down X-Plane Client')
            if self.client_selectors:
                self.client_selectors.unregister(self.client_socket)
                self.client_selectors.close()
            if self.client_socket: 
                self.client_socket.close()
        except:
            pass # skip any error here

    def xplane_client_thread_for_communication_with_xplane_server(self):

        '''
        Use a socket in non-blocking mode to establish a network connection with the X-Plane server. 
        Use a selector to allows monitoring multiple sockets to check their status and see if 
        they are ready for operations such as reading or writing.

        This allowing multi connection   
        '''
        try:
            self.keep_running.set()
            self.init_phase_running.set()

            if self.xplane_client_connect():
                logger.info(f'==> Connecting on {(self.host, self.port)} within the X-Plane server')
                # Unblocking socket
                self.client_socket.setblocking(False)
                # Register a file object for selection, monitoring it for I/O events
                self.client_selectors.register(self.client_socket, selectors.EVENT_READ | selectors.EVENT_WRITE, data=self.shared_data_container)

                while self.keep_running.is_set():
                    self.xplane_client_run()
        
        except Exception as e:
            self.keep_running.clear()
            raise            
        finally:
            logger.info('==> Ending X-Plane client thread')
            logger.info('==>')
            self.xplane_client_shutting_down()

    def xplane_client_stop_communicate_with_xplane_server(self):
        '''
        Stop a thread. This thread is used for network communication between the X-Plane plugin and the X-Plane server. 
        '''
        try:
            logger.info('==> Server communication shutdown and kill a thread within X-Plane server')

            self.keep_running.clear()
            
            # Rollback main status to custom JSON Loaded
            self.current_main_status = XPlanePluginStatus.CUSTOM_JSON_LOADED
            self.tp_api.stateUpdate('xplane_plugin_for_touch_portal.CONNEXION.main_status', self.current_main_status) 

        except Exception as e:
            error = 'something wrong when xplane client stop communicate with xplane server'
            raise CustomErrorXPlane(error)

    def xplane_client_communicate_with_xplane_server(self):
        '''
        Call a thread. This thread is used for network communication between the X-Plane plugin and the X-Plane server. 
        This thread will finish when the keep_running was cleared
        '''
        try:
            logger.info('==> Starting X-Plane client thread for communication within X-Plane server')

            self.xplane_client_thread = threading.Thread(target=self.xplane_client_thread_for_communication_with_xplane_server, args=())
            self.xplane_client_thread.start()
            self.xplane_client_thread.join()
            '''
            If an error is present in self.custom_error_xplane_queue (an error appears in the xplane_client_thread_for_communication_with_xplane_server), 
            it is retrieved and a new exception (self.CustomErrorXPlane) is raised with the error message.
            '''
            error = self.custom_error_xplane_queue.get_nowait()

            if error:
                raise CustomErrorXPlane(str(error))
            '''
            If no error is present, the exception queue.Empty is raised by get_nowait(), 
            indicating that the queue is empty. 
            This exception is caught by the except queue.Empty (no errors detected).
            '''
        except queue.Empty:
            error = 'Ending communication with X-Plane server'
            raise CustomErrorXPlane(error)

def main():
    
    # Create an instance from the XPlanePlugin class.
    XPlanePluginInstance = XPlanePlugin()

    successful = XPlanePluginInstance.touch_portal_client_process()

    del XPlanePluginInstance

    sys.exit(int(successful))

if __name__ == '__main__':
    main()