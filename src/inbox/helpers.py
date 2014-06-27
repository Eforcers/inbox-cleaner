# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8
import StringIO

import imaplib
import logging
import email

import httplib2

from apiclient import errors
from apiclient.http import MediaIoBaseUpload

from util import OAuthEntity, GenerateXOauthString
from apiclient.discovery import build
from oauth2client.client import Credentials, OAuth2WebServerFlow
from gdata.apps.emailsettings.client import EmailSettingsClient
from gdata.gauth import OAuth2TokenFromCredentials
from inbox import app
import constants
from email.parser import HeaderParser
import time


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


class DriveHelper(OAuthServiceHelper):
    """ Google Drive API helper class"""
    def __init__(self, credentials_json=None, admin_email=None, refresh_token=None):
        OAuthServiceHelper.__init__(self, credentials_json, refresh_token)
        self.service = build('drive', 'v2', http=self.http)
        self.admin_email = admin_email

    def get_folder(self, name="", parent_id=None):
        mime = "mimeType='application/vnd.google-apps.folder'"
        if not parent_id:
            q = "%s AND title='%s' and trashed = false" % (mime, name)
        else:
            q = "%s AND title='%s' and '%s' in parents and trashed = false" % (
                mime, name, parent_id)
        files = self.service.files().list(q=q).execute()
        if files['items']:
            return files['items'][0]
        else:
            return None

    def create_folder(self, name, parents=None):
        mime_type = "application/vnd.google-apps.folder"
        body = {
            'title': name,
            'mimeType': mime_type
        }

        if parents:
            body['parents'] = parents

        try:
            file = self.service.files().insert(
                body=body).execute()

            return file
        except errors.HttpError, error:
            logging.error('Error creating drive file: %s' % error)
        return None

    def insert_file(self, filename=None, mime_type=None, content=None, parent_id=None):
        body = {
            'title': filename,
            'mimeType': mime_type
        }
        if parent_id:
            body['parents'] = [{'id': parent_id}]
        try:
            media_body = MediaIoBaseUpload(StringIO.StringIO(content), mime_type)
            created_file = self.service.files().insert(body=body, media_body=media_body).execute()
            return created_file
        except Exception as e:
            logging.error("Error uploading file %s" % filename)
            return False

    def get_metadata(self, title=None, parent_id=None):
        try:
            if not parent_id:
                q = "title='%s' and trashed = false" % title
            else:
                q = "title='%s' and '%s' in parents and trashed = false" % (
                    title, parent_id)
            files = self.service.files().list(q=q).execute()
            if files['items']:
                return files['items'][0]
            else:
                return None
        except Exception as e:
            logging.error('Error getting file %s metadata, error: %s' % (title, e))

    def insert_permission(self, file_id=None, value=None, type=None, role=None):
        new_permission = {
            'value': value,
            'type': type,
            'role': role
        }

        try:
            return self.service.permissions().insert(
                fileId=file_id, body=new_permission,
                sendNotificationEmails=False).execute()
        except Exception as e:
            logging.error('Error inserting permission for file: %s, error: %s' % (
                file_id, e))
            return False

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

class EmailSettingsHelper(OAuthServiceHelper):
    def __init__(self, credentials_json, domain=None, refresh_token=None):
        OAuthServiceHelper.__init__(self, credentials_json, refresh_token)
        client = EmailSettingsClient(domain=domain)
        auth2token = OAuth2TokenFromCredentials(self.credentials)
        self.client = auth2token.authorize(client)

    def enable_imap(self, user):
        self.client.update_imap(username=user, enable=True)

    def disable_imap(self, user):
        self.client.update_imap(username=user, enable=True)

    def retrieve_imap_state(self, user):
        return self.client.retrieve_imap(username=user)


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
        query = u'-in:draft '
        if only_with_attachments:
            query += 'has:attachment smaller:9M '

        if only_from_trash:
            query += 'in:trash '

        query += '-filename:*.ics '

        query += '%s ' % criteria
        logging.info("query %s", query)
        self.mail_connection.literal = query.encode('utf-8')
        result, data = self.mail_connection.uid('SEARCH', 'CHARSET', 'UTF-8', 'X-GM-RAW')

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

    def copy_message(self, msg_id=None, destination_label=None):
        # For any message that we find, we will copy it to the destination label.
        # and remove the original label. IMAP does not have a move command.
        result, data = self.mail_connection.uid('COPY', msg_id,
                                                destination_label)
        self.mail_connection.expunge()
        return result, data

    def remove_message_label(self, msg_id=None, prev_label=None):
        result, data = self.mail_connection.uid('STORE', msg_id, '-X-GM-LABELS',
                                                prev_label)
        self.mail_connection.expunge()
        return result, data


    def add_message_labels(self, msg_id=None, new_labels=None):
        formatted_labels = []
        new_labels = [] if new_labels is None else new_labels
        for label in new_labels:
            formatted_labels.append(label.strip('"'))
        labels_string = '"' + '" "'.join(formatted_labels) + '"'
        result, data = self.mail_connection.uid('STORE', msg_id, '+X-GM-LABELS',
                                                labels_string)
        return result, data

    def get_message_labels(self, msg_id=None):
        result, data = self.mail_connection.uid('FETCH', msg_id, 'X-GM-LABELS')
        return result, data

    def get_subject(self, msg_id=None):
        data = self.mail_connection.uid('FETCH',
            msg_id, '(BODY[HEADER.FIELDS (SUBJECT FROM)])')
        header_data = data[1][0][1]
        parser = HeaderParser()
        header = parser.parsestr(header_data)
        subject = header['Subject']
        text, encoding = email.Header.decode_header(subject)[0]
        if encoding is None:
            return text
        else:
            return text.decode(encoding)

    def delete_message(self, msg_id=None, criteria='', mailbox_is_trash=False):
        subject = self.get_subject(msg_id=msg_id)

        self.mail_connection.uid('COPY', msg_id,
                                 self.all_labels[constants.GMAIL_TRASH_KEY])

        # Sometimes the copy doesn't get reflected immediately
        # Also, the email migration API has a 1QPS limit per account
        time.sleep(1)

        self.select(only_from_trash=True)

        criteria = "subject:%s %s" % (subject, criteria)

        try:
            messages = self.list_messages(
                criteria="subject:%s %s" % (subject, criteria),
                only_from_trash=True,
                only_with_attachments=True)
        except:
            messages = self.list_messages(
                criteria=criteria,
                only_from_trash=True,
                only_with_attachments=True)

        for m in messages:
            result, data = self.mail_connection.uid('STORE', m, '+FLAGS', '\\Deleted')
            self.mail_connection.expunge()
        if not mailbox_is_trash:
            self.select()


class MigrationHelper(OAuthServiceHelper):
    """ Google Directory API helper class"""

    def __init__(self, credentials_json=None, refresh_token=None):
        OAuthServiceHelper.__init__(self, credentials_json, refresh_token)
        self.service = build('admin', 'email_migration_v2', http=self.http)

    def migrate_mail(self, user_email=None, msg=None, labels=None):
        if labels is None or type(labels) is not list:
            labels = []
        new_labels = []
        user_labels = []

        properties = constants.GMAIL_PROPERTY_NAMES

        for label in labels:
            new_label = label.strip('"')
            new_labels.append(new_label)
            if new_label not in properties:
                user_labels.append(label)

        body = {
            "kind": "mailItem",
            "labels": user_labels
        }

        for property in constants.GMAIL_PROPERTIES:
            if property.keys()[0] in new_labels:
                body[property.values()[0]] = True

        mime_type = 'message/rfc822'

        content = msg.as_string()
        content = content.replace('Message-ID', 'Old-ID')

        media_body = MediaIoBaseUpload(
            StringIO.StringIO(content), mime_type)

        try:
            result = self.service.mail().insert(
                userKey=user_email,
                body=body,
                media_body=media_body
            ).execute()

            return True
        except Exception as e:
            logging.error("Error migrating email for user %s, error: %s" % (
                user_email, e))
            return False