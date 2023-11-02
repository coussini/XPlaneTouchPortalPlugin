# SuperFastPython.com
# example of returning a value from a thread
from time import sleep
from threading import Thread
 
# custom thread
class CustomThread(Thread):
    # constructor
    def __init__(self):
        # execute the base constructor
        Thread.__init__(self)
        # GET ALL VALUE FROM X-PLANE IN THE BEGINNING
        # BOUCLE DANS LES STATES
        #   XPUPD.WriteDataRef(dataref,1)
        # OLD = XPUPD.GetValues()
        # BOUCLE POUR INITIALISER LES VALEUR DANS LES STATES
        # for key, value in OLD.items():
        #   TPClient.stateUpdate(key,value)
        self.condition = Event()
        self.value = None
        self.stopped = false
 
    # When a start method is use, the following is done 
    def run(self):
        while self.condition.is_set():
        # block for a moment
        sleep(0.100)
        # NEW = XPUPD.GetValues()
        # BOUCLE POUR INITIALISER LES VALEUR DANS LES STATES
        # if NEW != OLD
        #    for key, value in OLD.items():
        #       TPClient.stateUpdate(key,value)
        # GET ALL VALUE FROM X-PLANE IN THE BEGINNING
        self.value = 'Hello from a new thread'
 
# create a new thread
thread = CustomThread()
# start the thread
thread.start()
# wait for the thread to finish
thread.join()
# get the value returned from the thread
data = thread.value


thread.condition.set()  # End while loop.

print(data)