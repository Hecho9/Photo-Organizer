import warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.ERROR)
for lib in ["hachoir", "PIL", "pymediainfo", "pyexiv2", "exifread", "rawpy"]:
    logging.getLogger(lib).setLevel(logging.CRITICAL)

import sys
import os

class DevNull:
    def write(self, msg): pass
    def flush(self): pass

sys.stderr = DevNull()

if os.name == 'nt':
    os.system('')
