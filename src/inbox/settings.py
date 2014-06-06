"""
settings.py

Configuration for Flask app

Important: Place your keys in the secret_keys.py module, 
           which should be kept out of version control.

"""

import os

from secret_keys import CSRF_SECRET_KEY, SESSION_KEY, OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET, OAUTH2_CONSUMER_KEY, OAUTH2_CONSUMER_SECRET

class Config(object):
    # Set secret keys for CSRF protection
    SECRET_KEY = CSRF_SECRET_KEY
    CSRF_SESSION_KEY = SESSION_KEY
    OAUTH2_CLIENT_ID = OAUTH2_CLIENT_ID
    OAUTH2_CLIENT_SECRET = OAUTH2_CLIENT_SECRET
    OAUTH2_CONSUMER_KEY = OAUTH2_CONSUMER_KEY
    OAUTH2_CONSUMER_SECRET = OAUTH2_CONSUMER_SECRET
    # Flask-Cache settings
    CACHE_TYPE = 'gaememcached'


class Development(Config):
    DEBUG = True
    # Flask-DebugToolbar settings
    DEBUG_TB_PROFILER_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CSRF_ENABLED = True


class Testing(Config):
    TESTING = True
    DEBUG = True
    CSRF_ENABLED = True


class Staging(Config):
    DEBUG = True

class Production(Config):
    DEBUG = False
    CSRF_ENABLED = True