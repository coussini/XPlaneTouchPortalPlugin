class Event(object):

	def __init__(self):
		self.__eventhandlers = []

	def __iadd__(self, handler):
		self.__eventhandlers.append(handler)
		return self

	def __isub__(self, handler):
		self.__eventhandlers.remove(handler)
		return self

	def __call__(self, *args, **keywargs):
		for eventhandler in self.__eventhandlers:
			eventhandler(*args, **keywargs)
				
class Police(object):
	def __init__(self, policeTelephoneNo):
		self._telephone = policeTelephoneNo
	
	def CallPolice(self):
		print ("police have been informed")

class Owner(object):
	def __init__(self, ownerMobile):
		self.__mobile = ownerMobile
	
	def Message(self):
		print ("owner has been messaged about the possible theft")
		
class Alarm(object):
	
	def StartAlarm(self):
		print ("Alarm has started")
		
# LockClass

class Lock(object):
	
	def __init__(self):
		self.OnLockBroken = Event()
		
	def LockBroken(self):
		# This function will be executed once a lock is broken and will 
		# raise an event
		self.OnLockBroken()
		
	def AddSubscribersForLockBrokenEvent(self,objMethod):
		self.OnLockBroken += objMethod
		
	def RemoveSubscribersForLockBrokenEvent(self,objMethod):
		self.OnLockBroken -= objMethod

def Simulation(): 
	# In the simulation we have a lock 
	# which will be broken and the object of Police 
	# owner and Alarm classes which are 
	# to be notified as soon as lock is broke
	
	# Required objects
	godrejLockObj = Lock()
	localPoliceObj = Police(100)
	ownerObj = Owner(99999999)
	mainDoorAlarmObj = Alarm()
	
	# Setting these objects to receive the events from lock
	godrejLockObj.AddSubscribersForLockBrokenEvent(localPoliceObj.CallPolice)
	godrejLockObj.AddSubscribersForLockBrokenEvent(ownerObj.Message)
	godrejLockObj.AddSubscribersForLockBrokenEvent(mainDoorAlarmObj.StartAlarm)
	
	# Now the Lock is broken by some burglar
	# thus LockBroken function will be called
	godrejLockObj.LockBroken()
	
	# All three notifications must be printed 
	# as soon as Lock is broken now
	
	# You can also remove any receiver by 
	# calling the RemoveSubscribersForLockBrokenEvent
	godrejLockObj.RemoveSubscribersForLockBrokenEvent(mainDoorAlarmObj.StartAlarm)
if __name__ == "__main__":		 
	Simulation()
