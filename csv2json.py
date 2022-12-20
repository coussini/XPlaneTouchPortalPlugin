import csv
import json

csvfile = open('datarefs.csv', 'r')
jsonfile = open('datarefs.json', 'w')

fieldnames = ("Description","Dataref")
reader = csv.DictReader( csvfile, fieldnames)
for row in reader:
    json.dump(row, jsonfile)
    jsonfile.write('\n')