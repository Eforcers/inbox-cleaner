"""
Initialize Flask app

"""
import logging
import os

from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.debug import DebuggedApplication

import constants


def get_environment():
    """
    Returns the environment based on the OS variable, server name and version id
    :return: The current environment that the app is running on
    """
    # Auto-set settings object based on App Engine dev environ
    if os.getenv('FLASK_CONF') == 'TEST':
        return constants.ENV_TESTING
    elif 'SERVER_SOFTWARE' in os.environ:
        if os.environ['SERVER_SOFTWARE'].startswith('Google App Engine/'):
            #For considering an environment staging we assume the version id
            # contains -staging and the URL
            current_version_id = str(os.environ['CURRENT_VERSION_ID']) if (
                'CURRENT_VERSION_ID') in os.environ else ''
            if '-staging' in current_version_id:
                return constants.ENV_STAGING
            #If not local or staging then is production TODO: really?
            return constants.ENV_PRODUCTION
        elif (os.environ['SERVER_SOFTWARE'].startswith('Dev') or os.getenv(
                'FLASK_CONF') == 'DEV'):
            return constants.ENV_DEVELOPMENT
    logging.error('Unable to identify environment, returning Development')
    return constants.ENV_DEVELOPMENT

app = Flask('inbox')

env = get_environment()

if env == constants.ENV_DEVELOPMENT:
    # Monkey patch App Engine socket implementation
    # Needed to get ssl connections working on localhost
    import ssl_monkey_patch

    #development settings n
    app.config.from_object('inbox.settings.Development')
    # Flask-DebugToolbar (only enabled when DEBUG=True)
    toolbar = DebugToolbarExtension(app)

    # Google app engine mini profiler
    # https://github.com/kamens/gae_mini_profiler
    app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

    # from gae_mini_profiler import profiler, templatetags
    # @app.context_processor
    # def inject_profiler():
    #     return dict(profiler_includes=templatetags.profiler_includes())
    # app.wsgi_app = profiler.ProfilerWSGIMiddleware(app.wsgi_app)

elif constants.ENV_TESTING:
    app.config.from_object('inbox.settings.Testing')

elif constants.ENV_PRODUCTION:
    app.config.from_object('inbox.settings.Production')

elif constants.ENV_STAGING:
    app.config.from_object('inbox.settings.Staging')

else:
    logging.error('Unable to identify the environment, using default config')
    app.config.from_object('inbox.settings.Config')

app.config['CURRENT_ENV'] = env

# Enable jinja2 loop controls extension
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
app.jinja_env.add_extension('jinja2.ext.autoescape')
app.jinja_env.autoescape=True

# Pull in views
import views