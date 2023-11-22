__copyright__ = """
    This file is part of the XPlane-API project.
    Copyright (c) XPlane-API Developers/Contributors
    Copyright (C) 2023 Coussini
    All rights reserved.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import socket
import selectors
import json
from threading import Event, Lock
from .logger import Logger
from typing import TextIO
import sys

__all__ = ['Xplane_client']

class Xplane_client():
    """
    A TCP/IP client for X-Plane API plugin integration.

    After an initial connection to a X-Plane desktop application "server," the client
    implements a send/receive event loop while maintaining the open sockets. Messages between
    TP and the plugin are exchanged asynchronously, with all sending methods possibly returning
    before the actual data is sent.

    """
    """ XPlane plugin server host IPv4 address. """
    TPHOST = socket.gethostbyname(socket.gethostname())
    """ Xplane plugin server host IPv4 port number. """
    TPPORT = 65432
    """ [B] incoming data buffer size. """
    RCV_BUFFER_SZ = 4096
    """ [B] maximum size of send data buffer (1MB). """
    SND_BUFFER_SZ = 32**4
    """ [s] maximum wait time for socket events (blocking timeout for selector.select()). """
    SOCK_EVENT_TO = 1.0

    def __init__(self, pluginId:str,
                 sleepPeriod:float = 0.01,
                 loggerName:str = None,
                 logLevel:str = "INFO",
                 logStream:TextIO = sys.stderr,
                 logFileName:str = None):
        """
        Creates an instance of the client.

        Args:
            `pluginId`: ID string of the TouchPortal plugin using this client. **Required.**
            `sleepPeriod`: Seconds to sleep the event loop between socket read events. Default: 0.01
            `loggerName`: Optional name for the Logger to be used by the Client.
                Default of `None` creates (or uses, if it already exists) the "root" (default) logger.
            `logLevel`: Desired minimum logging level, one of:
                "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG" (or equivalent Py `logging` module Level constants),
                or `None` to disable all logging. The level can also be set at runtime via `setLogLevel()` method.
                Default is "INFO".
            `logStream`: Set a stream to write log messages to, or `None` to disable stream (console) logging.
                The stream logger can also be modified at runtime via `setLogStream()` method.
                Default is `sys.stderr`.
            `logFileName`: A file name (with optional path) for log messages. Paths are relative to current working directory.
                Pass `None` or empty string to disable file logging. The log file is rotated once per day and the last 7
                logs are preserved (older ones are deleted). The file logger can also be modified at runtime via `setLogFile()` method.
                Default is `None` (file logging is disabled).
        """
        self.pluginId = pluginId
        self.sleepPeriod = sleepPeriod
        self.log = Logger(name=loggerName, level=logLevel, filename=logFileName, stream=logStream)
        self.client = None
        self.selector = None
        self.currentStates = {}
        self.currentSettings = {}
        self.choiceUpdateList = {}
        self.shortIdTracker = {}
        self.__heldActions = {}
        self.__stopEvent = Event()       # main loop inerrupt
        self.__stopEvent.set()           # not running yet
        self.__dataReadyEvent = Event()  # set when __sendBuffer has data
        self.__writeLock = Lock()        # mutex for __sendBuffer
        self.__sendBuffer = bytearray()
        self.__recvBuffer = bytearray()
        # explicitly disable logging if logLevel `None` was passed (Logger() c'tor ignores `None` log level)
        if not logLevel:
            self.log.setLogLevel(None)

    def __buffered_readLine(self):
        try:
            # Should be ready to read
            data = self.client.recv(self.RCV_BUFFER_SZ)
        except BlockingIOError:
            pass  # Resource temporarily unavailable (errno EWOULDBLOCK)
        except OSError:
            raise  # No connection
        else:
            if data:
                lines = []
                lines.append(data)
                return lines
            else:
                # No connection
                self.__raiseException("Peer closed the connection.", RuntimeError)
        return []

    def __processMessage(self, message: bytes):
        data = json.loads(message.decode())
        ## traiter la lecture ici
        if data:
            print(data) 

    def __write(self):
        if self.client and self.__sendBuffer and self.__getWriteLock():
            try:
                # Should be ready to write
                sent = self.client.send(self.__sendBuffer)
            except BlockingIOError:
                pass  # Resource temporarily unavailable (errno EWOULDBLOCK)
            except OSError:
                raise  # No connection
            else:
                del self.__sendBuffer[:sent]
            finally:
                if not self.__sendBuffer:
                    self.__dataReadyEvent.clear()
                self.__writeLock.release()

    ### Rouler __run dans un thread
    def __run(self):
        try:
            while not self.__stopEvent.is_set():
                events = self.selector.select(timeout=self.SOCK_EVENT_TO)
                if self.__stopEvent.is_set():  # may be set while waiting for selector events (unlikely)
                    break
                for _, mask in events:
                    if (mask & selectors.EVENT_READ):
                        for line in self.__buffered_readLine():
                            self.__processMessage(line)
                    if (mask & selectors.EVENT_WRITE):
                        self.__write()
                # Sleep for period or until there is data in the write buffer.
                # In theory if data is constantly avaiable, this could block,
                # in which case it may be better to self.__stopEvent.wait()
                if self.__dataReadyEvent.wait(self.sleepPeriod):
                    continue
                continue
        except Exception as e:
            self.__die(f"Exception in client event loop: {repr(e)}", e)

    def __open(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.selector = selectors.DefaultSelector()
            self.client.connect((self.TPHOST, self.TPPORT))
        except Exception:
            self.selector = self.client = None
            raise
        self.client.setblocking(False)
        self.selector.register(self.client, (selectors.EVENT_READ | selectors.EVENT_WRITE))
        self.__stopEvent.clear()

    def __close(self):
        self.log.info(f"{self.pluginId} Disconnected from TouchPortal")
        self.__stopEvent.set()
        if self.__writeLock.locked():
            self.__writeLock.release()
        self.__sendBuffer.clear()
        if not self.selector:
            return
        if self.selector.get_map():
            try:
                self.selector.unregister(self.client)
            except Exception as e:
                self.log.warning(f"Error in selector.unregister(): {repr(e)}")
        try:
            self.client.shutdown(socket.SHUT_RDWR)
            self.client.close()
        except OSError as e:
            self.log.warning(f"Error in socket.close(): {repr(e)}")
        finally:
            # Delete reference to socket object for garbage collection, socket cannot be reused anyway.
            self.client = None
        self.selector.close()
        self.selector = None
        # print("Xplane Client stopped.")

    def __die(self, msg=None, exc=None):
        if msg: self.log.info(msg)
        self.__close()
        if exc:
            self.log.critical(repr(exc))
            raise exc

    def __getWriteLock(self):
        if self.__writeLock.acquire(timeout=15):
            if self.__stopEvent.is_set():
                if self.__writeLock.locked(): self.__writeLock.release()
                return False
            return True
        self.__die(exc=RuntimeError("Send buffer mutex deadlock, cannot continue."))
        return False

    def __raiseException(self, message, exc = TypeError):
        self.log.error(message)
        raise exc(message)

    def isConnected(self):
        """
        Returns `True` if the Client is connected to Touch Portal, `False` otherwise.
        """
        return not self.__stopEvent.is_set()

    def setLogLevel(self, level):
        """ Sets the minimum logging level. `level` can be one of one of:
            "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG" (or equivalent Py `logging` module Level constants),
            or `None` to disable all logging.
        """
        self.log.setLogLevel(level)

    def setLogStream(self, stream):
        """ Set a destination for the StreamHandler logger. `stream` should be a file stream type (eg. os.stderr) or `None` to disable. """
        self.log.setStreamDestination(stream)

    def setLogFile(self, fileName):
        """ Set a destination for the File logger. `filename` should be a file name (with or w/out a path) or `None` to disable the file logger. """
        self.log.setFileDestination(fileName)

    def send(self, data):
        """
        This will try to send any arbitrary Python object in `data` (presumably something `dict`-like) to Touch Portal
        after serializing it as JSON and adding a `\n`. Normally there is no need to use this method directly, but if the
        Python API doesn't cover something from the TP API, this could be used instead.
        """
        if not self.isConnected():
            self.__raiseException("TP Client not connected to Touch Portal, cannot send commands.", Exception)
        if self.__getWriteLock():
            if len(self.__sendBuffer) + len(data) > self.SND_BUFFER_SZ:
                self.__writeLock.release()
                self.__raiseException("TP Client send buffer is full!", ResourceWarning)
            self.__sendBuffer += (json.dumps(data)+'\n').encode()
            self.__writeLock.release()
            self.__dataReadyEvent.set()

    def connect(self):
        """
        Initiate connection to TP Server.
        If successful, it starts the main processing loop of this client.
        Does nothing if client is already connected.

        **Note** that `connect()` blocks further execution of your script until one of the following occurs:
          - `disconnect()` is called in an event handler,
          - TP sends `closePlugin` message and `autoClose` is `True`
          - or an internal error occurs (for example Touch Portal disconnects unexpectedly)
        """
        if not self.isConnected():
            self.__open()
            self.send({"type":"pair", "id": self.pluginId})
            self.__run()  # start the event loop

    def disconnect(self):
        """
        This closes the connection to TP and terminates the client processing loop.
        Does nothing if client is already disconnected.
        """
        if self.isConnected():
            self.__close()

    @staticmethod
    def getActionDataValue(data:list, valueId:str=None):
        """
        Utility for processing action messages from TP. For example:
            {"type": "action", "data": [{ "id": "data object id", "value": "user specified value" }, ...]}

        Returns the `value` with specific `id` from a list of action data,
        or `None` if the `id` wasn't found. If a null id is passed in `valueId`
        then the first entry which has a `value` key, if any, will be returned.

        Args:
            `data`: the "data" array from a TP "action", "on", or "off" message
            `valueId`: the "id" to look for in `data`. `None` or blank to return the first value found.
        """
        if not data: return None
        if valueId:
            return next((x.get('value') for x in data if x.get('id', '') == valueId), None)
        return next((x.get('value') for x in data if x.get('value') != None), None)