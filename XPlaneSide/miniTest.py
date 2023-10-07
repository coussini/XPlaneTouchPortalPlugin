#Mini test
from XPPython3 import xp
dataref = xp.findDataRef('sim/aircraft/electrical/num_batteries')
print(xp.getDatai(dataref))
