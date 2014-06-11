# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8


import imaplib
import logging

import httplib2

from util import OAuthEntity, GenerateXOauthString
from apiclient.discovery import build
from oauth2client.client import Credentials, OAuth2WebServerFlow
from inbox import app
import constants
import email


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
    all_labels = {}

    def __init__(self):
        self.mail_connection = imaplib.IMAP4_SSL(host=constants.IMAP_SERVER,
                                                 port=constants.IMAP_PORT)
        self.mail_connection.debug = app.config.get('DEBUG')

    def oauth1_2lo_login(self, user_email):
        self.consumer = OAuthEntity(app.config.get('OAUTH2_CONSUMER_KEY'),
                                    app.config.get('OAUTH2_CONSUMER_SECRET'))
        xoauth_string = GenerateXOauthString(self.consumer, user_email, 'GET',
                                             'imap')

        self.mail_connection.authenticate('XOAUTH', lambda x: xoauth_string)
        logging.info('IMAP connection [%s] successfully established',
                     user_email)

    def login(self, email, password):
        logging.info("Connecting to IMAP server with user [%s]", email)
        try:
            result, data = self.mail_connection.login(email, password)
        except:
            result, data = 'NO', None
        return result, data

    def get_localized_labels(self):
        result, mail_labels = self.mail_connection.list()
        if result == 'OK':
            for labels in mail_labels:
                key, label = labels.split(' "/" ')
                self.all_labels[key] = label

        return self.all_labels

    def get_date(self, msg_id=None):
        result, header = self.mail_connection.uid(
            'fetch', msg_id, '(BODY[HEADER.FIELDS (DATE SUBJECT)])')
        if result != 'OK':
            return None
        headerparser = email.parser.HeaderParser()
        headerdict = headerparser.parsestr(header[0][1])

        pz = email.utils.parsedate_tz(headerdict["Date"])
        stamp = email.utils.mktime_tz(pz)

        date = imaplib.Time2Internaldate(stamp)
        return date

    def close(self):
        logging.info('IMAP connection state: %s', self.mail_connection.state)
        try:
            if self.mail_connection.state == 'SELECTED':
                self.mail_connection.close()
            self.mail_connection.logout()
            logging.info('IMAP connection sucessfully closed')
        except:
            logging.exception('Error closing the connection')

    def list_messages(self, criteria='', only_with_attachments=False,
                      only_from_trash=False):
        self.select(only_from_trash=only_from_trash)
        query = ' '
        if only_with_attachments:
            query += 'has:attachment '

        if only_from_trash:
            query += 'in:trash '

        query += '%s ' % criteria
        result, data = self.mail_connection.uid('search', None,
                                                r'(X-GM-RAW "%s")' % query)

        msg_ids = []
        if result == 'OK':
            msg_ids = data[0].split()

        return msg_ids

    def get_message(self, msg_id):
        result, data = self.mail_connection.uid('fetch', msg_id, '(RFC822)')
        return result, data

    def create_label(self, new_label=None):
        # Attempt to create the destination label. If it already exists, nothing
        # will happen.
        self.mail_connection.create(new_label)

    def select(self, only_from_trash=False):
        self.get_localized_labels()
        main_label = ''

        if only_from_trash:
            if constants.GMAIL_TRASH_KEY in self.all_labels:
                main_label = self.all_labels[constants.GMAIL_TRASH_KEY]
            else:
                en_label = constants.IMAP_TRASH_LABEL_EN
                es_label = constants.IMAP_TRASH_LABEL_ES
        else:
            if constants.GMAIL_ALL_KEY in self.all_labels:
                main_label = self.all_labels[constants.GMAIL_ALL_KEY]
            else:
                en_label = constants.IMAP_ALL_LABEL_EN
                es_label = constants.IMAP_ALL_LABEL_ES

        if main_label != '':
            result, data = self.mail_connection.select(main_label)
        else:
            result, data = self.mail_connection.select(es_label)
            # Try in english if not found in spanish
            if result != 'OK':
                result, data = self.mail_connection.select(en_label)

        if result != 'OK':
            # Maybe configured in another language or label name is wrong
            logging.error("Unable to get count for all label. %s [%s]",
                          result, data)
            return None, None
        return result, data

    def copy_message(self, msg_id=None, destination_label=None, only_from_trash=False):
        # For any message that we find, we will copy it to the destination label.
        # and remove the original label. IMAP does not have a move command.
        result, data = self.mail_connection.uid('COPY', msg_id,
                                                destination_label)
        self.mail_connection.expunge()
        return result, data

    def remove_message_label(self, msg_id=None, prev_label=None):
        result, data = self.mail_connection.uid('STORE', msg_id, '-X-GM-LABELS',
                                                prev_label)
        return result, data


    def add_message_labels(self, msg_id=None, new_labels=None):
        formatted_labels = []
        for label in new_labels:
            formatted_labels.append(label.strip('"'))
        labels_string = '"' + '" "'.join(formatted_labels) + '"'
        result, data = self.mail_connection.uid('STORE', msg_id, '+X-GM-LABELS',
                                                labels_string)
        return result, data

    def get_message_labels(self, msg_id=None):
        result, data = self.mail_connection.uid('FETCH', msg_id, 'X-GM-LABELS')
        return result, data

    def delete_message(self, msg_id=None):
        self.mail_connection.uid('COPY', msg_id,
                             self.all_labels[constants.GMAIL_TRASH_KEY])
        self.mail_connection.expunge()