"""
models.py

App Engine NDB datastore models

"""
import re

from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext import ndb

from inbox import constants


def validate_email(prop, value):
    value = value if value else None
    if value is None:
        return value
    elif not re.match(constants.EMAIL_REGEXP, value):
        raise BadValueError
    return value.lower()


class User(ndb.Model):
    email = ndb.StringProperty(required=True, validator=validate_email)
    # OAuth credentials and token for the domain domain
    credentials = ndb.TextProperty(indexed=False)
    refresh_token = ndb.StringProperty(indexed=False)


class CleanUserProcess(ndb.Model):
    process_name = ndb.StringProperty(required=True)
    # Authenticated account, owner of the process
    owner_email = ndb.StringProperty(required=True, validator=validate_email)
    #IMAP credentials
    source_email = ndb.StringProperty(required=True, validator=validate_email,
                                      indexed=False)
    source_password = ndb.StringProperty(required=True, indexed=False)
    destination_message_email = ndb.StringProperty(required=True,
                                                   validator=validate_email,
                                                   indexed=False)
    search_criteria = ndb.StringProperty(required=True)
    pipeline_id = ndb.IntegerProperty(indexed=False)
    status = ndb.StringProperty()


class CleanMessageProcess(ndb.Model):
    email = ndb.StringProperty()
    status = ndb.StringProperty()


class CleanAttachmentProcess(ndb.Model):
    status = ndb.StringProperty()


class MoveProcess(ndb.Model):
    emails = ndb.StringProperty(indexed=False, repeated=True,
                                validator=validate_email)
    tag = ndb.StringProperty(indexed=False, required=True)
    pipeline_id = ndb.StringProperty(indexed=False)
    status = ndb.StringProperty(choices=constants.STATUS_CHOICES)
    execution_start = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    execution_finish = ndb.DateTimeProperty(indexed=False)
    ok_count = ndb.IntegerProperty(indexed=False)
    error_count = ndb.IntegerProperty(indexed=False)
    total_count = ndb.IntegerProperty(indexed=False)


class MoveUserProcess(ndb.Model):
    user_email = ndb.StringProperty(indexed=False, required=True,
                                    validator=validate_email)
    move_process_key = ndb.KeyProperty(MoveProcess, indexed=False)
    status = ndb.StringProperty(choices=constants.STATUS_CHOICES)
    error_description = ndb.StringProperty(indexed=False)


class MoveMessageProcess(ndb.Model):
    email = ndb.StringProperty(indexed=False, required=True,
                               validator=validate_email)
    message_id = ndb.StringProperty(indexed=False, required=True)
    user_process_key = ndb.KeyProperty(MoveUserProcess, indexed=False)
    status = ndb.StringProperty(choices=constants.STATUS_CHOICES)
    error_description = ndb.StringProperty(indexed=False)


class ProcessedUser(ndb.Model):
    #The key ID is the email of the user, for fast retrieval
    ok_count = ndb.IntegerProperty(indexed=False)
    error_count = ndb.IntegerProperty(indexed=False)
    total_count = ndb.IntegerProperty(indexed=False, repeated=True)