import sys

from google.appengine.tools.devappserver2.python import sandbox
sandbox._WHITE_LIST_C_MODULES += ['_ssl', '_socket']

from lib import patched_socket

sys.modules['socket'] = patched_socket
socket = patched_socket