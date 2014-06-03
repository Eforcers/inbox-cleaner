"""
decorators.py

Decorators for URL handlers

"""

from functools import wraps
import logging
from google.appengine.api import users
from inbox.models import Client
from flask import redirect, request, abort


def login_required(func):
    """Requires standard login credentials"""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not users.get_current_user():
            return redirect(users.create_login_url(request.url))
        return func(*args, **kwargs)
    return decorated_view


def admin_required(func):
    """Requires domain admin credentials"""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        current_user = users.get_current_user()
        if current_user:
            client = Client.get_instance()
            if not client:
                abort(500)  # Not installed yet
            if current_user.email() not in client.administrators:
                abort(403)  # Unauthorized
            return func(*args, **kwargs)
        return redirect(users.create_login_url(request.url))
    return decorated_view


def super_admin_required(func):
    """Requires App Engine admin credentials"""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if users.get_current_user():
            if not users.is_current_user_admin():
                abort(401)  # Unauthorized
            return func(*args, **kwargs)
        return redirect(users.create_login_url(request.url))
    return decorated_view
