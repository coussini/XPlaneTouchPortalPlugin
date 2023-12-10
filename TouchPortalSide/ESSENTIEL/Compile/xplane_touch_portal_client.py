import sys 
import os
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
        self.successful = True
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
    
    # Create object concerning Touch Portal API
    client_tp_api = client_tpxp.tp_api
    # Create object concerning Touch Portal API events
    on_info = client_tpxp.on_info
    on_action = client_tpxp.on_action
    on_close_plugin = client_tpxp.on_close_plugin

    # This event handler will run once when the client connects to Touch Portal
    @client_tp_api.on(on_info) 
    def onStart(data):
        print(f'Connected to Touch Portal Version {data.get("tpVersionString", "?")} plugin v {data.get("pluginVersion", "?")})')
        print(f'=================')
        print(f'SECTION on_info')
        print(f'=================')
        print(f'{data}')

    # Action handlers, called when user activates one of this plugin's actions in Touch Portal.
    @client_tp_api.on(on_action) 
    def onAction(data):
        print(f'=================')
        print(f'SECTION on_action')
        print(f'=================')
        print(f'{data}')

    # Shutdown handler, called when Touch Portal wants to stop your plugin.
    @client_tp_api.on(on_close_plugin) 
    def onShutdown(data):
        print(f'=======================')
        print(f'SECTION on_close_plugin')
        print(f'=======================')
        print(f'{data}')
        print(f'Got Shutdown Message! Shutting Down the Plugin!')
        client_tp_api.disconnect()

    print(f'Trying to connect to Touch Portal Apps')
    
    try:
        client_tp_api.connect()
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting.")
        client_tpxp.successful = False
    except ConnectionRefusedError:
        print(f'Cannot connect to Touch Portal, probably it is not running')
        client_tpxp.successful = False
        return
    except Exception:
        # This will catch and report any critical exceptions in the base client_tp_api code,
        # _not_ exceptions in this plugin's event handlers (use onError(), above, for that).
        from traceback import format_exc
        print(f"Exception in TP Client:\n{format_exc()}")
        client_tpxp.successful = False
        return
    finally:
        print(f'TP Client Disconnected')
        client_tp_api.disconnect()

    del client_tp_api

    print(f'Return code = {client_tpxp.successful}')
    sys.exit(client_tpxp.successful)

if __name__ == '__main__':
    main()