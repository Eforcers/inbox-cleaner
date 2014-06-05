import sys

from google.appengine.tools.devappserver2.python import sandbox

from lib import patched_socket

sandbox._WHITE_LIST_C_MODULES += ['_ssl', '_socket']

sys.modules['socket'] = patched_socket
socket = patched_socket