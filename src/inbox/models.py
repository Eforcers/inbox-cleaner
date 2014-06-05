"""
models.py

App Engine NDB datastore models

"""
import re

from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext import ndb
from google.appengine.api import memcache

from inbox import constants


def validate_email(prop, value):
    value = value if value else None
    if value is None:
        return value
    elif not re.match(constants.EMAIL_REGEXP, value):
        raise BadValueError
    return value.lower()


class CleanUserProcess(ndb.Model):
    name = ndb.StringProperty(required=True)
    #Authenticated account, owner of the process
    owner_email = ndb.StringProperty(required=True, validator=validate_email)
    #IMAP credentials
    source_email = ndb.StringProperty(required=True, validator=validate_email, indexed=False)
    source_password = ndb.StringProperty(required=True,
                                         validator=validate_email, indexed=False)
    destination_message_email = ndb.StringProperty(required=True,
                                                   validator=validate_email, indexed=False)
    search_criteria = ndb.StringProperty(required=True)
    # OAuth credentials and token for the domain domain
    credentials = ndb.TextProperty(indexed=False)
    refresh_token = ndb.StringProperty(indexed=False)
    status = ndb.StringProperty()



class CleanMessageProcess(ndb.Model):
    email_id = ndb.StringProperty()
    status = ndb.StringProperty()

class CleanAttachmentProcess(ndb.Model):
    status = ndb.StringProperty()