import json
with open('Datarefs.json') as f:
    data = json.load(f)

for item in data['datarefs']:
    item['id'] = item['dataref']

with open('New_Datarefs.json', 'w') as f:
    json.dump(data, f, indent=4)