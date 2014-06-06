# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8


import imaplib
import logging

from util import OAuthEntity, GenerateXOauthString

import httplib2
from apiclient.discovery import build
from oauth2client.client import Credentials, OAuth2WebServerFlow
from inbox import app
import constants


class OAuthDanceHelper:
    """ OAuth dance helper class"""
    flow = None

    def __init__(self, redirect_uri='', approval_prompt='auto', scope=''):
        self.flow = OAuth2WebServerFlow(
            client_id=app.config.get('OAUTH2_CLIENT_ID'),
            client_secret=app.config.get(
                'OAUTH2_CLIENT_SECRET'),
            scope=scope,
            redirect_uri=redirect_uri,
            approval_prompt=approval_prompt)

    def step1_get_authorize_url(self):
        return self.flow.step1_get_authorize_url()

    def step2_exchange(self, code):
        return self.flow.step2_exchange(code)

    def get_credentials(self, credentials_json):
        return Credentials.new_from_json(credentials_json)


class OAuthServiceHelper:
    """ OAuth services base helper class"""

    credentials = None
    service = None

    def __init__(self, credentials_json, refresh_token=None):
        oauth_helper = OAuthDanceHelper()
        self.credentials = oauth_helper.get_credentials(credentials_json)
        if refresh_token and self.credentials.refresh_token is None:
            self.credentials.refresh_token = refresh_token
        self.http = self.credentials.authorize(httplib2.Http())


class DirectoryHelper(OAuthServiceHelper):
    """ Google Directory API helper class"""

    def __init__(self, credentials_json, customer_id=None, refresh_token=None):
        OAuthServiceHelper.__init__(self, credentials_json, refresh_token)
        self.service = build('admin', 'directory_v1', http=self.http)
        self.customer_id = customer_id

    def get_customer_id(self, email):
        user_document = self.service.users().get(
            userKey=email,
            fields="customerId"
        ).execute()
        if "customerId" in user_document:
            self.customer_id = user_document["customerId"]
            return user_document["customerId"]
        return None


class IMAPHelper:
    """ IMAP helper class"""
    mail_connection = None

    def __init__(self):
        self.mail_connection = imaplib.IMAP4_SSL(host=constants.IMAP_SERVER,
                                                 port=constants.IMAP_PORT)
        self.mail_connection.debug = app.config.get('DEBUG')

    def oauth1_2lo_login(self, user_email):
        self.consumer = OAuthEntity(app.config.get('OAUTH2_CONSUMER_KEY'),
                                    app.config.get('OAUTH2_CONSUMER_SECRET'))
        xoauth_string = GenerateXOauthString(self.consumer, user_email, 'GET',
                                             'imap')
        try:
            self.mail_connection.authenticate('XOAUTH', lambda x: xoauth_string)
            logging.info('IMAP connection [%s] successfully established',
                         user_email)
        except imaplib.IMAP4.error:
            logging.error(
                'Error authenticating [%s] with OAUTH credentials provided' % user_email)

    def login(self, email, password):
        logging.info("Connecting to IMAP server with user [%s]", email)
        result, data = self.mail_connection.login(email, password)
        return result, data

    def close(self):
        self.mail_connection.close()
        self.mail_connection.logout()
        logging.info('IMAP connection sucessfully closed')

    def list_messages(self, criteria='', only_with_attachments=False,
                      only_from_trash=False):
        if only_from_trash:
            en_label = constants.IMAP_TRASH_LABEL_EN
            es_label = constants.IMAP_TRASH_LABEL_ES
        else:
            en_label = constants.IMAP_ALL_LABEL_EN
            es_label = constants.IMAP_ALL_LABEL_ES
        try:
            result, data = self.mail_connection.select(es_label)
            # Try in english if not found in spanish
            if result != 'OK':
                result, data = self.mail_connection.select(en_label)
                if result != 'OK':
                    # Maybe configured in another language or label name is wrong
                    logging.error("Unable to get count for all label. %s [%s]",
                                  result, data)
                    return result, data

            query = ' '
            if only_with_attachments:
                query += 'has:attachment %s ' % criteria

            if only_from_trash:
                query += 'in:trash '

            result, data = self.mail_connection.uid('search', None,
                                                    r'(X-GM-RAW "%s")' % query)
            print result, data, query

            msg_ids = []
            if result == 'OK':
                msg_ids = data[0].split()

            return 'OK', msg_ids
        except:
            logging.exception("Unable to select mailbox")
            return 'NO', None

    def get_message(self, msg_id):
        result, data = self.mail_connection.uid('fetch', msg_id, '(RFC822)')
        self.mail_connection.expunge()
        return result, data

    def copy_message(self, msg_id=None, new_label=None):
        self.mail_connection.create(new_label)
        result, data = self.mail_connection.uid('COPY', msg_id, new_label)
        self.mail_connection.expunge()
        return result, data

    def remove_message_label(self, msg_id=None, prev_label=None):
        result, data = self.mail_connection.uid('STORE', msg_id, '-X-GM-LABELS',
                                                prev_label)
        self.mail_connection.expunge()
        return result, data

    def delete_message(self, msg_id=None):
        result, data = self.mail_connection.uid('STORE', msg_id, '+FLAGS',
                                                '\\Deleted')
        if result == 'OK':
            result, data = self.mail_connection.expunge()
        else:
            self.mail_connection.expunge()
        return result, data

    def move_message(self, msg_id=None, prev_label=None, new_label=None):
        # When the original label is trash, you only need to copy the message
        result, data = self.copy_message(msg_id=msg_id, new_label=new_label)
        if result == 'OK':
            result, data = self.remove_message_label(
                msg_id=msg_id, prev_label=prev_label)
            if result == 'OK':
                result, data = self.delete_message(msg_id=msg_id)
        return result, data

    def add_message_labels(self, msg_id=None, new_labels=None):
        labels_string = '"' + '" "'.join(new_labels) + '"'
        result, data = self.mail_connection.uid('STORE', msg_id, '+X-GM-LABELS',
                                                labels_string)
        self.mail_connection.expunge()
        return result, data

    def get_message_labels(self, msg_id=None):
        result, data = self.mail_connection.uid('FETCH', msg_id, 'X-GM-LABELS')
        self.mail_connection.expunge()
        return result, data





