import sys 
import os
import platform
import argparse # argparse.ArgumentParser
import TouchPortalAPI as TP_API
import TouchPortalAPI.logger as TP_API_LOG # TouchPortalAPI.logger.Logger
import selectors
import socket
import json
import time
import random
import threading

__plugin_id__ = 'xplane_touch_portal_client'
__log_file__ = f'./{__plugin_id__}.log'
        
# Get OS where python is running.
__is_windows__ = True if (platform.system() == 'Windows') else False
__is_linux__ = True if (platform.system() == 'Linux') else False
__is_macos__ = True if (platform.system() == 'Darwin') else False

# Create the (optional) global __logger__, an instance of `TouchPortalAPI::Logger` helper class.
try:
    __logger__ = TP_API_LOG.Logger(name = __plugin_id__)
except Exception as err:
    sys.exit(f'Could not create a Touch Portal log file. Error was:\n{repr(err)}')

# define an exception for the XPlane Plugin
class XPlanePluginException(Exception):
    pass

class XPlanePlugin:
    
    def __init__(self):

        self.version = '1.0'
        self.json_file = 'datarefs.json'
        self.json_keys_first_level = ['datarefs']
        self.json_keys = ['id', 'desc', 'group', 'type', 'value', 'dataref', 'comment']

        if __is_windows__: self.touch_portal_data_folder = os.getenv('APPDATA') + '\\TouchPortal\\plugins\\';
        if __is_linux__: self.touch_portal_data_folder = '\\TouchPortal\\plugins\\';
        if __is_macos__: self.touch_portal_data_folder = '\\Documents\\TouchPortal\\plugins\\';

        self.json_file_location = self.touch_portal_data_folder+ self.json_file

        # keep states from json file
        self.states = None

        # Create client_TP instance.
        self.client_TP = TouchPortal()

    def validate_keys_from_json_file(self, states):
        
        successful = True

        self.json_keys.sort()

        for x in states['datarefs']:
            keys = list(x.keys())
            keys.sort()
            if keys != self.json_keys:
                __logger__.error(f'json file keys must be {self.json_keys} and not {keys}')
                successful = False
                break

        return successful

    def get_dataref_values_from_json_file(self):
        
        successful = False
        states = None
        
        __logger__.info(f'Trying to load datarefs from: {self.json_file_location}')

        try:
            file = open(self.json_file, 'r')
            states = json.load(file)
            file.close()
            __logger__.info(f'Datarefs successfully loaded from {self.json_file} !')
        except FileNotFoundError as err:
            __logger__.error(f'File {self.json_file} does not exist')
        except ValueError as err:
            stack = traceback.extract_stack()
            filename, line, procname, text = stack[-1]
            __logger__.error(f'Invalid JSON syntax in {self.json_file}')
            __logger__.error(f'{err}')
        except Exception as err:
            from traceback import format_exc
            __logger__.error(f'str({err})')
        else:
            successful = self.validate_keys_from_json_file(states)

        if successful:
            __logger__.info(f'The json file: {self.json_file_location} is valid !')

        return successful, states
        
class TouchPortal:
   
    def __init__(self):
        
        # Create the Touch Portal API client instance.
        try:
            self.tp_api = TP_API.Client(
                pluginId = __plugin_id__,           # required ID of this plugin
                sleepPeriod = 0.05,                 # allow more time than default for other processes
                autoClose = True,                   # automatically disconnect when TP sends 'closePlugin' message
                checkPluginId = True,               # validate destination of messages sent to this plugin
                maxWorkers = 4,                     # run up to 4 event handler threads
                updateStatesOnBroadcast = False,    # do not spam TP with state updates on every page change
                logFileName = __log_file__          # For log messages. Paths are relative to current working directory     
            )
        except Exception as e:
            sys.exit(f'Could not create a Touch Portal API client instance, exiting. Error was:\n{repr(e)}')

        # Event for the Touch Portal API
        self.on_info = TP_API.TYPES.onConnect
        self.on_action = TP_API.TYPES.onAction
        self.on_close_plugin = TP_API.TYPES.onShutdown

class XPlane:
    
    def __init__(self):

        self.client_selectors = selectors.DefaultSelector()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = 65432
        self.keep_running = threading.Event()
        self.outgoing_data = []

    def connect(self):

        try:    
            self.client_socket.connect((self.host,self.port))
        except:
            raise RuntimeError('X-Plane server is not running')

    def treat_xplane_client(self):

        __logger__.info('starting X-Plane client thread')
        self.keep_running.set()
        xp_thread = threading.Thread(target=self.thread_function, args=())
        xp_thread.start()

    def thread_function(self):

        try:
            self.connect()
            try:
                self.preparing_running()
                while self.keep_running.is_set():
                    self.run()
            except:
                raise RuntimeError('[1] X-Plane server closed suddenly')
            else:
                __logger__.info('shutting down X-Plane client')
                self.shutting_down()
        except RuntimeError:
            pass

        return

    def preparing_running(self):

        __logger__.info(f'preparing x-plane to running')
        __logger__.info(f'Connecting on {(self.host, self.port)}')

        # unblocking socket
        self.client_socket.setblocking(False)
        # register a file object for selection, monitoring it for I/O events
        self.client_selectors.register(self.client_socket, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)

    def run(self):

        # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in self.client_selectors.select(timeout=0.1):
            self.service_connection(key, mask)

    def shutting_down(self):
        if self.client_selectors:
            self.client_selectors.unregister(self.client_socket)
            self.client_selectors.close()
        if self.client_socket: 
            self.client_socket.close()

    def service_connection(self, key, mask):

        server_socket = key.fileobj
    
        if mask & selectors.EVENT_READ:
            try:
                # Should be ready to read
                ingoing_data = server_socket.recv(1024) 
            except BlockingIOError:
                pass  # Resource temporarily unavailable (errno EWOULDBLOCK)
            except:
                raise
            else:
                if ingoing_data:
                    self.managing_received_data(ingoing_data)
                else:
                    raise

        if mask & selectors.EVENT_WRITE:
            if self.outgoing_data:
                next_msg = self.outgoing_data.pop()
                server_socket.sendall(next_msg)

    def managing_received_data(self, ingoing_data):

        __logger__.info(f'ingoing_data = {ingoing_data}')
        pass 

def treat_touch_portal_client(xplane_plugin):

    successful = False

    client_TP = xplane_plugin.client_TP 
    # Create some objects concerning Touch Portal API events
    on_info = xplane_plugin.client_TP.on_info
    on_action = xplane_plugin.client_TP.on_action
    on_close_plugin = xplane_plugin.client_TP.on_close_plugin

    # This event handler will run once when the client connects to Touch Portal
    @client_TP.on(on_info) 
    def onStart(data):

        __logger__.info(f'Connected to Touch Portal Version {data.get("tpVersionString", "?")} plugin v {data.get("pluginVersion", "?")})')
        __logger__.info(f'=================')
        __logger__.info(f'SECTION on_info')
        __logger__.info(f'=================')
        __logger__.info(f'{data}')
        list_choices = []
        for x in xplane_plugin.states['datarefs']:
            descrition = x['group'] + ' - ' + x['desc']
            client_TP.createState(x['id'],descrition,x['value'],x['group']) # create a TP State default value at runtime
            list_choices.append(x['desc'])
        list_choices.sort() # sort options for ease of use
        client_TP.choiceUpdate('xplane_touch_portal_client.dataref.toggle_two_states.choice',list_choices) # update action option at runtime
        client_TP.choiceUpdate('xplane_touch_portal_client.dataref.set_two_states.name',list_choices) # update action option at runtime
        __logger__.info(f'Touch Portal Choices of States Id have been updated !')
        # start a thread to treat xplane client.
        # Create client_XP instance.
        client_XP = XPlane()
        try:
            client_XP.treat_xplane_client()
        except RuntimeError:
            client_XP.keep_running.clear()
            client_TP.disconnect()
            del client_XP
            del client_TP
            return False 

    # Action handlers, called when user activates one of this plugin's actions in Touch Portal.
    @client_TP.on(on_action) 
    def onAction(data):

        __logger__.info(f'=================')
        __logger__.info(f'SECTION on_action')
        __logger__.info(f'=================')
        __logger__.info(f'{data}')

    # Shutdown handler, called when Touch Portal wants to stop your plugin.
    @client_TP.on(on_close_plugin) 
    def onShutdown(data):

        __logger__.info(f'=======================')
        __logger__.info(f'SECTION on_close_plugin')
        __logger__.info(f'=======================')
        __logger__.info(f'{data}')
        __logger__.info(f'Got Shutdown Message! Shutting Down the Plugin!')
        client_TP.disconnect()
    
    try:
        __logger__.info(f'Trying to connect to Touch Portal Apps')
        client_TP.connect()
    except KeyboardInterrupt:
        __logger__.warning('Caught keyboard interrupt, exiting.')
    except ConnectionRefusedError:
        __logger__.error(f'Cannot connect to Touch Portal, probably it is not running')
    except RuntimeError:        
        __logger__.error(f'Catch RuntimeError')
        pass
    except Exception:
        # This will catch and report any critical exceptions in the base client_TP code,
        # _not_ exceptions in this plugin's event handlers (use onError(), above, for that).
        from traceback import format_exc
        __logger__.error(f'Exception in TP Client:\n{format_exc()}')
    else:
        __logger__.info(f'TP Client Disconnected')
        successful = True
    finally:
        client_XP.keep_running.clear()
        client_TP.disconnect()
        del client_XP
        del client_TP

    return successful

def main():
    
    # Create a mega instance that concern the XPlane Plugin.
    xplane_plugin = XPlanePlugin()

    # extract all datarefs from the JSON file.
    successful, xplane_plugin.states = xplane_plugin.get_dataref_values_from_json_file()

    if successful:
        successful = treat_touch_portal_client(xplane_plugin)

    __logger__.info(f'Return code = {successful}')
    sys.exit(successful)

if __name__ == '__main__':
    main()