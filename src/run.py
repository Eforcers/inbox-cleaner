import os
import sys

sys.path.insert(1, os.path.join(os.path.abspath('.'), 'lib'))
import inbox

from pipeline import handlers
import livecount