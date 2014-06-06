# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8

import httplib2

from apiclient.discovery import build
from oauth2client.client import Credentials, OAuth2WebServerFlow
from inbox import app
import logging
import imaplib
import constants

import base64
import csv
import datetime
import hashlib
import hmac
import imaplib
import logging
from optparse import OptionParser
import random
import sys
import time
import urllib

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
        self.mail_connection = imaplib.IMAP4_SSL(host=constants.IMAP_SERVER)

    def oauth1_login(self):
        self.consumer = OAuthEntity(app.config.get('OAUTH2_CONSUMER_KEY'),
                               app.config.get('OAUTH2_CONSUMER_SECRET'))

    def login(self, email, password):
        logging.info("Connecting to IMAP server with user [%s]", email)
        result, data = self.mail_connection.login(email, password)
        return result, data

    def list_messages(self, criteria=''):
        try:
            result, data = self.mail_connection.select(constants.IMAP_ALL_LABEL_ES)
            #Try in english if not found in spanish
            if result != 'OK':
                result, data = self.mail_connection.select(constants.IMAP_ALL_LABEL_EN)
                if result != 'OK':
                    #Maybe configured in another language or label name is wrong
                    logging.error("Unable to get count for all label. %s [%s]", result, data)
                    return 'NO', None

            query = 'has:attachment %s' % criteria
            result, data = self.mail_connection.uid('search', None, r'(X-GM-RAW "%s")' % query)

            msg_ids = []
            if result == 'OK':
                msg_ids = data[0].split()

            return 'OK', msg_ids
        except:
            logging.exception("Unable to select mailbox")
            return 'NO', None

    def get_message(self, msg_id):
        result, data = self.mail_connection.uid('fetch', msg_id, '(RFC822)')
        return result, data

    def list(self, user_email):
        xoauth_string = GenerateXOauthString(self.consumer, user_email, 'GET', 'imap')










