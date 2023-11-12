def dataref_syntax_validation(dataref):
    
    nb_open_braket = 0
    nb_close_braket = 0
        
    for x in dataref:
        if x == "[":
            nb_open_braket += 1
            continue
        if x == "]":
            nb_close_braket += 1
            continue

    if nb_open_braket > 1 or nb_close_braket > 1:
        print("bad pattern dataref array")
        return False
    
    if nb_open_braket == 1 and nb_close_braket == 1:
        dataref = dataref.replace("["," ")
        dataref = dataref.replace("]"," ")
        dataref = dataref.split()
        if len(dataref) == 2:
            if dataref[1].isnumeric():
                print("good pattern dataref array")
            else:
                print("bad pattern dataref array")
                return False
        else:
            print("bad pattern dataref array")
            return False
    else:
        dataref = dataref.split()
        if len(dataref) == 1 and nb_open_braket == 0 and nb_close_braket == 0:
            print("pattern single dataref")
        else:
            print("bad pattern single dataref")
            return False
    return True
     
donnee_valide = dataref_syntax_validation(input('Enter a dataset:'))
print(f"Es-ce que ce dataref est valide ? {donnee_valide}")
