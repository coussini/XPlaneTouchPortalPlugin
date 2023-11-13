import xp

class PythonInterface:

    def get_dataref_name_and_index(self,oneDataref):

        # receive a dataref from a JSON
        # As an example, here are the names of datarefs including or not an index
        # 'sim/aircraft/electrical/num_batteries'
        # 'sim/multiplayer/combat/team_status[3]' the index is 3
        
        datarefIndex = None 
        datarefName = oneDataref.replace("["," ")
        datarefName = datarefName.replace("]"," ")
        datarefName = datarefName.split()

        if len(datarefName) == 2: # it's an array
            index = datarefName[1]
            datarefName = datarefName[0]
        else: # it's not an array    
            datarefName = datarefName[0]

        return datarefName,datarefIndex 

    def get_dataref_address_type_value(self,datarefName,datarefIndex):

        # receive a dataref including or not an index

        datarefAddress = xp.findDataRef(datarefName)
        datarefType = xp.getDataRefTypes(datarefAddress)
        datarefValue = self.read_a_dataref(datarefAddress,datarefType,datarefIndex)
        
        return datarefAddress,datarefType,datarefValue

    def read_a_dataref(self,datarefAddress,datarefType,datarefIndex):

        # read a dataref accourding to itS name, type and index

        match datarefType:
            case 0:
                return None
            case 1:
                return xp.getDatai(datarefAddress)
            case 2:
                return xp.getDataf(datarefAddress)
            case 4:
                return xp.getDatad(datarefAddress)
            case 8:
                return xp.getDatavi(datarefAddress,datarefIndex)
            case 16:
                return xp.getDatavf(datarefAddress,datarefIndex)
            case 32:
                return xp.getDatas(datarefAddress)
            case _:
                return None

    def XPluginStart(self):
        return "Hello World", "xppython3.hello", "Simple Hello World"

    def XPluginEnable(self):
        xp.speakString("couseennee")
        oneDataref = "AirbusFBW/APUMaster"
        datarefName,datarefIndex = self.get_dataref_name_and_index(oneDataref)
        datarefAddress,datarefType,datarefValue = self.get_dataref_address_type_value(datarefName,datarefIndex)
        print(f"For dataref : {oneDataref} the type is : {datarefType} and the value is {datarefValue}")
        return 1