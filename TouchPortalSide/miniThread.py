from time import sleep
from threading import Event, Thread

def foo():
    LOGGER.info(time.ctime())
    OLD = TPClient.getStatelist()
    NEW = XPUPD.GetValues()
    LOGGER.info(f"OLD = {OLD}")
    LOGGER.info(f"NEW = {NEW}")
    '''
    for key, value in NEW.items():
        if int(value) != int(OLD.get(key)):
            #LOGGER.info("il y a eu changement du cote de xplane")
            LOGGER.info(f"[NEW] Pour la cle {key} et la valeur {value}")
            LOGGER.info(f"[OLD] Pour la cle {key} et la valeur {int(OLD.get(key))}")

    
    if int(OLD.get("AirbusFBW/ElecOHPArray[3]")) != int(NEW.get("AirbusFBW/ElecOHPArray[3]")):
        LOGGER.info("il y a eu changement du cote de xplane")
        LOGGER.info(OLD.get("AirbusFBW/ElecOHPArray[3]"))
        LOGGER.info(NEW.get("AirbusFBW/ElecOHPArray[3]"))

    #LOGGER.info(f"OLD = {OLD}")
    #LOGGER.info(f"NEW = {NEW}")
    #LOGGER.info(f"NEW = {NEW_VALUE}")
    
    a = sorted(OLD_VALUE.items()) != sorted(NEW_VALUE.items())
    if a:
        LOGGER.info("il y a eu changement du cotÃ© de xplane")
        OLD_VALUE = NEW_VALUE
    ''' 
    threading.Timer(WAIT_SECONDS, foo()).start()