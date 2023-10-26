# XPlaneTouchPortalPlugin

![Touch Portal Plugin](XPlaneTouchPortalPlugin.jpg "Xplane Touch Portal Plugin Logo")

###### TODO:  set the logo string "x-plane" in white

##### STEP FOR THIS MOMENT

- Explain to the XplaneTouchPortalPLugin user wich requierement are important to have (python, TouchPortal...)

- The states are use to store informations for x-plane DataRef. 

- Thats

- You can create your states into the "Datarefs.json"" file (already exist and contains an example) that you can use it.

- These are information for each states. 
  
  - id = Always beginning with "XplanePlugin.". You can take the description to complet the id. Do not put any spaces in it. 
  
  - desc = Description of the aircraft panel button.
  
  - group = Where you find the button in instruments panel. 
  
  - type = int or float. value = default value (usually 0). 
  
  - dataref = The full name of the dataref (including the index number if required). For an exemple "AirbusFBW/APUMaster" or  "AirbusFBW/OHPLightSwitches[2]"  where 2 is the index inside the variable AirbusFBW/OHPLightSwitches.
  
  - comment = Information allowing the panel's creator in Touch Portal to understand the values and wich corresponding

#####

##### STEP POUR LA COMPRÉHENSION DES DONNÉES

For example, it is a good idea to familiarize yourself with the dataref values corresponding to the buttons you want to use in Touch Portal. You can use the DatarefTool (see the html link in the folder to understand DataRefTool. You can also rely on the example file Datarefs.json (a simple text editor can allow you to see its content) in order to clearly identify your needs





1. id = An unique id for Touch Portal Usage

2. desc = This description can be use when a page builder use:
   
   1. Logic : If Statement (Advanced)
   
   2. Xplane - Dataref: Set Named Variable Value
