# setup_logger.py
import logging

PLUGIN_ID = "XPlanePlugin"

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)8s: %(name)15s:  %(message)s",
                    filename="xplane_touch_portal_client.log",
                    filemode="w")
LOGGER = logging.getLogger(PLUGIN_ID)