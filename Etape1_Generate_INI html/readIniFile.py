# readIniFile.py
import configparser

PLUGIN_ID = "XPlanePlugin"
filename = "file.ini"

# Writing Data
config = configparser.ConfigParser()
config.read(filename)

section = PLUGIN_ID+"00"
config.add_section(section)
config.set(section, "id", PLUGIN_ID+"00")
config.set(section, "description", "Ext Power")
config.set(section, "value", "0")
config.set(section, "dataref", "AirbusFBW/ElecOHPArray[3]")

with open(filename, "w") as config_file:
    config.write(config_file)

# Reading Data
config.read(filename)
keys = [
    "id",
    "description",
    "value",
    "dataref"
]
for key in keys:
    try:
        value = config.get(section, key)
        print(f"{key}:", value)
    except configparser.NoOptionError:
        print(f"No option '{key}' in section 'SETTINGS'")