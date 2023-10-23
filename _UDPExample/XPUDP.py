import pyxpudpserver as XPUDP

XPUDP.pyXPUDPServer.initialiseUDP(('127.0.1.1',49008), ('192.168.1.107',49000), 'DESKTOP-SVJ06Q2')
# where ('127.0.0.1',49008) is the IP and port this class is listening on (configure in the Net connections in XPlane)

# and ('192.168.1.1',49000) is the IP and port of XPlane

# 'MYPC' is the name of the computer XPlane is running on

# You can also initialise from an XML configuration file:

# XPUDP.pyXPUDPServer.initialiseUDPXMLConfig('UDPSettings.xml')

XPUDP.pyXPUDPServer.start() # start the server which will run an infinite loop

nb = 0
while True: # infinite loop - for a real application plan for a 'proper' way to exit the programme and break this loop

	#value = XPUDP.pyXPUDPServer.getData((17,3)) # read the value sent by XPlane for datagroup 17, position 4 (mag heading)

	APUMaster = XPUDP.pyXPUDPServer.getData("AirbusFBW/NDrangeCapt[0]") # gets the value of this dataref in XPlane
	if nb == 4:
		break
	else:
		print("S = ",{APUMaster})
		nb = nb + 1

XPUDP.pyXPUDPServer.quit() # exit the server thread and close the sockets