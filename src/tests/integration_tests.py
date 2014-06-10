from inbox import constants
from tests import AppEngineFlaskTestCase
from inbox.helpers import IMAPHelper
from secret_keys import TEST_LOGIN, TEST_PASS, TEST_OAUTH2_CONSUMER_KEY, TEST_OAUTH2_CONSUMER_SECRET
from inbox.util import OAuthEntity
import mock

class ImapHelperTestCase(AppEngineFlaskTestCase):
    def test_login(self):
        imap = IMAPHelper()
        result, data = imap.login(TEST_LOGIN, TEST_PASS)
        self.assertEquals('OK', result, "Couldn't login successfully")
        imap.close()

    def init(self, key, secret):
        self.key = TEST_OAUTH2_CONSUMER_KEY
        self.secret = TEST_OAUTH2_CONSUMER_SECRET

    @mock.patch.object(OAuthEntity, '__init__', init)
    def test_oauth1_2lo_login(self):
        imap = IMAPHelper()
        imap.oauth1_2lo_login("administrador@eforcers.com.co")
        imap.close()

    def test_list_messages(self):
        imap = IMAPHelper()
        result, data = imap.login(TEST_LOGIN, TEST_PASS)
        self.assertEquals('OK', result, "Couldn't login successfully")

        data = imap.list_messages()
        self.assertNotEquals(0, len(data), "Couldn't list messages successfully")
        imap.close()

    def test_get_message(self):
        imap = IMAPHelper()
        result, data = imap.login(TEST_LOGIN, TEST_PASS)
        self.assertEquals('OK', result, "Couldn't login successfully")

        data = imap.list_messages()
        self.assertNotEquals(0, len(data), "Couldn't list messages successfully")

        result, data = imap.get_message(data[0])
        self.assertEquals('OK', result, "Couldn't get message successfully")
        imap.close()

    def test_get_localized_labels(self):
        imap = IMAPHelper()
        result, data = imap.login(TEST_LOGIN, TEST_PASS)
        imap.get_localized_labels()
        self.assertNotEqual("",
                            imap.all_labels[constants.GMAIL_TRASH_KEY],
                            "Trash label is missing")
        self.assertNotEqual("",
                            imap.all_labels[constants.GMAIL_ALL_KEY],
                            "Trash label is missing")
        imap.close()

    def test_copy_message(self):
        imap = IMAPHelper()
        result, data = imap.login(TEST_LOGIN, TEST_PASS)
        self.assertEquals('OK', result, "Couldn't login successfully")

        imap.create_label('testlabel')

        prev_number_messages = len(imap.list_messages(criteria='label:testlabel'))

        messages = imap.list_messages()

        imap.copy_message(msg_id=messages[0], destination_label='testlabel')
        new_number_messages = len(imap.list_messages(criteria='label:testlabel'))

        self.assertEquals(prev_number_messages,
                          new_number_messages - 1,
                          "The message wasn't copied")

        imap.remove_message_label(msg_id=messages[0], prev_label='testlabel')

        new_number_messages = len(imap.list_messages(criteria='label:testlabel'))

        self.assertEquals(prev_number_messages,
                          new_number_messages,
                          "The message label wasn't removed")

