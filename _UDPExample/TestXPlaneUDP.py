import time
import XPlaneUPD as XPlaneUPD

try:
  xpUDP = XPlaneUPD.XPlaneUdp() #instance
  xpUDP.defaultFreq = 10
  
  beacon = xpUDP.FindIp()
  print(beacon)
  print()
  
  xpUDP.AddDataRef("AirbusFBW/OHPLightSwitches[7]") # strobe
  xpUDP.AddDataRef("AirbusFBW/APUAvail") #apu avail
  xpUDP.AddDataRef("AirbusFBW/ElecOHPArray[3]") # ext power
  
  #while True:
  try:
    values = xpUDP.GetValues()
    print(values["AirbusFBW/ElecOHPArray[3]"])
    xpUDP.WriteDataRef("AirbusFBW/ElecOHPArray[3]",1)
    xpUDP.WriteDataRef("AirbusFBW/OHPLightSwitches[7]",1)
    values = xpUDP.GetValues()
    print(values["AirbusFBW/ElecOHPArray[3]"])
    time.sleep(5)
    xpUDP.WriteDataRef("AirbusFBW/OHPLightSwitches[7]",2)
      
  except xpUDP.XPlaneTimeout:
    print("XPlane Timeout")
    exit(0)

except xpUDP.XPlaneVersionNotSupported:
  print("XPlane Version not supported.")
  exit(0)

except xpUDP.XPlaneIpNotFound:
  print("XPlane IP not found. Probably there is no XPlane running in your local network.")
  exit(0)
