import time
import XPlaneUPD as XPlaneUPD

def AddDatarefString(xpUDP,dataref,size,freq):

  for i in range(0,size):
    THeDataref = dataref+"["+str(i)+"]"
    print(THeDataref)
    xpUDP.AddDataRef(THeDataref,freq=freq)


def GetDatarefString(xpUDP,dataref, size):

  string = ""
  values = xpUDP.GetValues()

  for i in range(0,size):
    THeDataref = dataref+"["+str(i)+"]"
    char = values[THeDataref]
    print(chr(int(char)))
    # string = string+chr(int(char))

  return string 

def main():
  try:
    xpUDP = XPlaneUPD.XPlaneUdp() #instance
    xpUDP.defaultFreq = 10
    
    beacon = xpUDP.FindIp()
    print(beacon)
    print()
    
    AddDatarefString(xpUDP,"sim/aircraft/view/acf_ui_name",250,1)
    print(GetDatarefString(xpUDP,"sim/aircraft/view/acf_ui_name",250))
    AddDatarefString(xpUDP,"sim/aircraft/view/acf_ui_name",250,0)
    
    #time.sleep(5)
        
  except xpUDP.XPlaneTimeout:
    print("XPlane Timeout")
    exit(0)

main()