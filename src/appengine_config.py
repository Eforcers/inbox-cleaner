# -*- coding: utf-8 -*-
"""
App Engine specific config

"""

def namespace_manager_default_namespace_for_request():
    """
    Handles the namespace resolution based on the environment and the domain
    from the logged user. This let us test without touching production data
    while we are in staging
    :return: None if no user is logged in, staging-<domain> for staging,
    just the domain otherwise
    """
    from google.appengine.api import users

    user = users.get_current_user()
    if not user:
        return None
    domain = user.email().split('@', 1)[1]
    from inbox import constants, get_environment
    environment = get_environment()
    namespace = 'staging-%s' % domain if environment == constants.ENV_STAGING \
        else ''
    return namespace


def gae_mini_profiler_should_profile_production():
    """Uncomment the first two lines to enable GAE Mini Profiler on production
    for admin accounts"""
    from google.appengine.api import users
    return users.is_current_user_admin()
    return False


def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app
