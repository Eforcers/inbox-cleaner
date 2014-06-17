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


class PrimaryDomain(ndb.Model):
    # OAuth credentials and token for the domain domain
    credentials = ndb.TextProperty(indexed=False)
    refresh_token = ndb.StringProperty(indexed=False)
    admin_email = ndb.StringProperty(indexed=False)

    @staticmethod
    def get_or_create(domain_name):
        primary_domain = PrimaryDomain.get_by_id(domain_name)
        if not primary_domain:
            primary_domain = PrimaryDomain(id=domain_name)
            primary_domain.put()
        return primary_domain

class User(ndb.Model):
    # OAuth credentials and token for the domain domain
    credentials = ndb.TextProperty(indexed=False)
    refresh_token = ndb.StringProperty(indexed=False)

    @staticmethod
    def get_or_create(user_email):
        user = User.get_by_id(user_email)
        if not user:
            user = User(id=user_email)
            user.put()
        return user


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
    search_criteria = ndb.StringProperty(indexed=False)
    pipeline_id = ndb.IntegerProperty(indexed=False)
    status = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)


class CleanMessageProcess(ndb.Model):
    msg_id = ndb.StringProperty()
    status = ndb.StringProperty()
    clean_process_id = ndb.IntegerProperty()

    @staticmethod
    def get_or_create(msg_id, process_id):
        clean_message = CleanMessageProcess.query(ndb.AND(
            CleanMessageProcess.msg_id == msg_id,
            CleanMessageProcess.clean_process_id == process_id)
        ).get()
        if not clean_message:
            clean_message = CleanMessageProcess(
                msg_id=msg_id,
                status=constants.STARTED,
                clean_process_id = process_id)
            clean_message.put()
        return clean_message

class CleanAttachmentProcess(ndb.Model):
    msg_id = ndb.StringProperty()
    attachment_number = ndb.IntegerProperty()
    status = ndb.StringProperty()
    msg_process_id = ndb.IntegerProperty()
    url = ndb.StringProperty(indexed=False)
    filename = ndb.StringProperty(indexed=False)
    file_id = ndb.StringProperty(indexed=False)

    @staticmethod
    def get_or_create(msg_id,
                      msg_process_id,
                      attachment_number):
        clean_attachment = CleanAttachmentProcess.query(ndb.AND(
            CleanAttachmentProcess.msg_id == msg_id,
            CleanAttachmentProcess.msg_process_id == msg_process_id,
            CleanAttachmentProcess.attachment_number == attachment_number)
        ).get()
        if not clean_attachment:
            clean_attachment = CleanAttachmentProcess(
                msg_id=msg_id,
                status=constants.STARTED,
                msg_process_id=msg_process_id,
                attachment_number=attachment_number)
            clean_attachment.put()
        return clean_attachment


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
    error_description = ndb.StringProperty(indexed=False, repeated=True)
