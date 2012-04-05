"""

PunkMoney 0.2 :: logging.py

Logging class.

"""

# Imports

import os
import re
import sys
import logging, logging.handlers
from config import SETTINGS, LOG_PATH

# Logging class

class Logging():

    # Set up logging
    def setupLogging(self):
    
        # Only call once, so starting module has control
        if len(logging.getLogger("log").handlers) > 0:
            return
    
        # Create logging object   
        x = logging.getLogger("log")
        x.setLevel(logging.DEBUG)
        
        # Create handler
        h1 = logging.FileHandler(LOG_PATH)
        f = logging.Formatter("%(levelname)s %(asctime)s %(message)s")
        h1.setFormatter(f)
        h1.setLevel(logging.DEBUG)
        
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter("%(levelname)s %(asctime)s %(message)s"))
        
        x.addHandler(console)
        x.addHandler(h1)
        
        self.log = logging.getLogger("log")
        
    # Log warning
    def logWarning(self, message):
        self.log.warning(message)
        
    # Log info
    def logInfo(self, message):
        self.log.info(message)
        
    # Log error
    def logError(self, message):
        self.log.error(message)
        
    # Log debug
    def logDebug(self, message):
        if SETTINGS.get('debug', False) is True:
            self.log.info('[Debug]: ' + message)
        
