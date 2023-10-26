import time
import XPlaneUPD as xplib

try:
  xp = xplib.XPlaneUdp()
  xp.defaultFreq = 10
  
  beacon = xp.FindIp()
  print(beacon)
  print()
  
  xp.AddDataRef("AirbusFBW/OHPLightSwitches[7]") # strobe
  xp.AddDataRef("AirbusFBW/APUAvail") #apu avail
  xp.AddDataRef("AirbusFBW/ElecOHPArray[3]") # ext power
  
  #while True:
  try:
    values = xp.GetValues()
    print(values["AirbusFBW/ElecOHPArray[3]"])
    xp.WriteDataRef("AirbusFBW/ElecOHPArray[3]",1)
    xp.WriteDataRef("AirbusFBW/OHPLightSwitches[7]",1)
    values = xp.GetValues()
    print(values["AirbusFBW/ElecOHPArray[3]"])
    time.sleep(5)
    xp.WriteDataRef("AirbusFBW/OHPLightSwitches[7]",2)
      
  except xp.XPlaneTimeout:
    print("XPlane Timeout")
    exit(0)

except xp.XPlaneVersionNotSupported:
  print("XPlane Version not supported.")
  exit(0)

except xp.XPlaneIpNotFound:
  print("XPlane IP not found. Probably there is no XPlane running in your local network.")
  exit(0)
