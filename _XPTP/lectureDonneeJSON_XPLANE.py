import xp 

def get_dataref_name_and_index(oneDataref):

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

def get_dataref_type_and_value(datarefName,datarefIndex):

    # receive a dataref including or not an index

    datarefType = xp.getDataRefTypes(datarefName)
    datarefValue = read_a_dataref(datarefName,datarefType,datarefIndex)
    
    return datarefType,datarefValue

def read_a_dataref(datarefName,datarefType,datarefIndex):
 
    # match against dataref type
    
    '''
    Type
    0 Unknown
    1 Int
    2 Float
    4 Double
    8 Float Array
    16 Int Array
    32 Data
    '''
    match datarefType:
        case 0:
            return None
        case 1:
            return xp.getDatai(datarefName)
        case 2:
            return xp.getDataf(datarefName)
        case 4:
            return xp.getDatad(datarefName)
        case 8:
            return xp.getDatavi(datarefName,datarefIndex)
        case 16:
            return xp.getDatavf(datarefName,datarefIndex)
        case 32:
            return xp.getDatas(datarefName)
        case _:
            return None

oneDataref = "sim/aircraft/view/acf_descrip"
datarefName,datarefIndex = get_dataref_name_and_index(oneDataref)
datarefType,datarefValue = get_dataref_type_and_value(datarefName,datarefIndex)
print(f"For dataref : {oneDataref} the type is : {datarefType} and the value is {datarefValue}")