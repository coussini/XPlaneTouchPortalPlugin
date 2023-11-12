import re

def is_dataref_has_basic_valid_syntax(dataref):
    
    #length_dataref = len(dataref)
    nb_open_braket = 0
    nb_close_braket = 0
        
    for x in dataref:

        if x == "[":
            nb_open_braket += 1
            continue

        if x == "]":
            nb_close_braket += 1
            continue

    
    print("nb [   = ",nb_open_braket)
    print("nb ]   = ",nb_close_braket)

    if nb_open_braket > 1 or nb_close_braket > 1:
        print("bad pattern dataref array")
        return
    
    if nb_open_braket == 1 and nb_close_braket == 1:
        dataref = dataref.replace("["," ")
        dataref = dataref.replace("]"," ")
        dataref = dataref.split()
        print(dataref)
        if len(dataref) == 2:
            if dataref[1].isnumeric():
                print("good pattern dataref array")
            else:
                print("bad pattern dataref array")
        else:
            print("bad pattern dataref array")
    else:
        dataref = dataref.split()
        if len(dataref) == 1 and nb_open_braket == 0 and nb_close_braket == 0:
            print("pattern single dataref")
        else:
            print("bad pattern single dataref")
     
is_dataref_has_basic_valid_syntax(input("Enter a dataset:"))