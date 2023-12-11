############ pourquoi on info passe pas par là...............

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

class ClientTPXP:
    def __init__(self):
        self.version = '1.0'
        self.plugin_id = 'XPlanePlugin'
        
        # Get OS where python is running.
        self.is_windows = True if (platform.system() == "Windows") else False
        self.is_linux = True if (platform.system() == "Linux") else False
        self.is_macos = True if (platform.system() == "Darwin") else False
        if self.is_windows: self.touch_portal_data_folder = os.getenv('APPDATA') + '\\TouchPortal\\plugins\\';
        if self.is_linux: self.touch_portal_data_folder = '\\TouchPortal\\plugins\\';
        if self.is_macos: self.touch_portal_data_folder = '\\Documents\\TouchPortal\\plugins\\';
        
        # Create the Touch Portal API client instance.
        try:
            self.tp_api = TP_API.Client(
                pluginId = self.plugin_id,      # required ID of this plugin
                sleepPeriod = 0.05,             # allow more time than default for other processes
                autoClose = True,               # automatically disconnect when TP sends 'closePlugin' message
                checkPluginId = True,           # validate destination of messages sent to this plugin
                maxWorkers = 4,                 # run up to 4 event handler threads
                updateStatesOnBroadcast = False # do not spam TP with state updates on every page change
            )
        except Exception as e:
            sys.exit(f'Could not create a Touch Portal API client instance, exiting. Error was:\n{repr(e)}')
        
        # Create the (optional) global logger, an instance of `TouchPortalAPI::Logger` helper class.
        try:
            self.logger = TP_API_LOG.Logger(name = self.plugin_id)
        except Exception as e:
            sys.exit(f'Could not create a Touch Portal API client instance, exiting. Error was:\n{repr(e)}')
        
        # Event for the Touch Portal API
        self.on_info = TP_API.TYPES.onConnect
        self.on_action = TP_API.TYPES.onAction
        self.on_close_plugin = TP_API.TYPES.onShutdown
        
        # states from json file
        self.json_file = 'datarefs.json'
        self.json_file_location = self.touch_portal_data_folder+ self.json_file

        self.states = None

    def get_dataref_values_from_json_file(self):
        
        successful = False
        states = None
        
        self.logger.info(f'Trying to load datarefs from:')
        self.logger.info(f'----------------------------')
        self.logger.info(f'{self.json_file_location}')
        self.logger.info(f'----------------------------')

        try:
            file = open(self.json_file, 'r')
            states = json.load(file)
            file.close()
            self.logger.info(f'Datarefs successfully loaded from {self.json_file}')
            successful = True
        except FileNotFoundError:
            self.logger.error(f'File {self.json_file} does not exist')
        except ValueError:
            self.logger.error(f'Invalid JSON syntax in {self.json_file}')
        except Exception as err:
            from traceback import format_exc
            self.logger.error(f'str({err})')

        return successful, states

    def treat_touch_portal_client(self):

        successful = False

        # Create an object concerning Touch Portal client
        client_tp = self.tp_api
        # Create some objects concerning Touch Portal API events
        on_info = self.on_info
        on_action = self.on_action
        on_close_plugin = self.on_close_plugin

        # This event handler will run once when the client connects to Touch Portal
        @client_tp.on(on_info) 
        def onStart(data):
            self.logger.info(f'Connected to Touch Portal Version {data.get("tpVersionString", "?")} plugin v {data.get("pluginVersion", "?")})')
            self.logger.info(f'=================')
            self.logger.info(f'SECTION on_info')
            self.logger.info(f'=================')
            self.logger.info(f'{data}')

        # Action handlers, called when user activates one of this plugin's actions in Touch Portal.
        @client_tp.on(on_action) 
        def onAction(data):
            self.logger.info(f'=================')
            self.logger.info(f'SECTION on_action')
            self.logger.info(f'=================')
            self.logger.info(f'{data}')

        # Shutdown handler, called when Touch Portal wants to stop your plugin.
        @client_tp.on(on_close_plugin) 
        def onShutdown(data):
            self.logger.info(f'=======================')
            self.logger.info(f'SECTION on_close_plugin')
            self.logger.info(f'=======================')
            self.logger.info(f'{data}')
            self.logger.info(f'Got Shutdown Message! Shutting Down the Plugin!')
            client_tp.disconnect()

        self.logger.info(f'Trying to connect to Touch Portal Apps')
        
        try:
            client_tp.connect()
        except KeyboardInterrupt:
            self.logger.warning("Caught keyboard interrupt, exiting.")
        except ConnectionRefusedError:
            self.logger.error(f'Cannot connect to Touch Portal, probably it is not running')
            return False
        except Exception:
            # This will catch and report any critical exceptions in the base client_tp code,
            # _not_ exceptions in this plugin's event handlers (use onError(), above, for that).
            from traceback import format_exc
            self.logger.error(f"Exception in TP Client:\n{format_exc()}")
            successful = False
        finally:
            self.logger.info(f'TP Client Disconnected')
            client_tp.disconnect()
            successful = True

        del client_tp

        return successful

class ClientXP:
    def __init__(self):
        self.client_selectors = selectors.DefaultSelector()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = 65432
        self.keep_running = threading.Event()
        self.outgoing_data = []
        self.random_msg1 = None # temporary
        self.random_msg2 = None # temporary

    def connect(self):
        try:    
            self.client_socket.connect((self.host,self.port))
        except socket.error:
            print(f'X-Plane server is not running')
            return False
        else:
            return True

    def preparing_running(self):
        print(f'Connecting on {(self.host, self.port)}')
        # unblocking socket
        self.client_socket.setblocking(False)
        # register a file object for selection, monitoring it for I/O events
        self.client_selectors.register(self.client_socket, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)

    def run(self):
        # the mask indicate wich kind of event should be waited (1 = EVENT_READ and 2 = EVENT_WRITE)
        for key, mask in self.client_selectors.select(timeout=0.1):
            self.service_connection(key, mask)
            self.put_some_random_message() # (1) run a class inside a thread... and from outside, feed class.outgoing with action message... (init...write...)

    # create some action to send to server
    def put_some_random_message(self):
        value = random.randint(1,7)
        print('value = ',value)
        if value == 5:
            print('generate message')
            message = json.dumps(self.random_msg1).encode()
            self.outgoing_data.append(message)
        elif value == 7:
            print('generate message')
            message = json.dumps(self.random_msg2).encode()
            self.outgoing_data.append(message)
        time.sleep(0.1)

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
                # No connection
                #raise Exception('X-Plane server closed suddenly')
                raise
            else:
                if ingoing_data:
                    self.managing_received_data(ingoing_data)
                else:
                    # No connection
                    #raise Exception('X-Plane server closed suddenly')
                    raise

        if mask & selectors.EVENT_WRITE:
            if self.outgoing_data:
                next_msg = self.outgoing_data.pop()
                server_socket.sendall(next_msg)

    def managing_received_data(self, ingoing_data):
        print(f'ingoing_data = {ingoing_data}')
        pass 

def main():
    
    # Create a mega instance that concern Touch Portal and X-Plane.
    client_tpxp = ClientTPXP() 
    # extract all datarefs from the JSON file.
    successful, client_tpxp.states = client_tpxp.get_dataref_values_from_json_file()

    if successful:
        successful = client_tpxp.treat_touch_portal_client()

    client_tpxp.logger.info(f'Return code = {successful}')
    sys.exit(successful)

if __name__ == '__main__':
    main()