# Python program to read
# json file

import json

# Opening JSON file
f = open('Datarefs.json')

# returns JSON object as 
# a dictionary
data = json.load(f)
print(data)
# Iterating through the json
# list

# Closing file
f.close()
