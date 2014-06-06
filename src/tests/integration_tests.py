from tests import AppEngineFlaskTestCase
from inbox.helpers import IMAPHelper
from secret_keys import TEST_LOGIN, TEST_PASS

class ImapHelperTestCase(AppEngineFlaskTestCase):
    def test_login(self):
        imap = IMAPHelper()
        result, data = imap.login(TEST_LOGIN, TEST_PASS)
        self.assertEquals('OK', result, "Couldn't login successfully")

    def test_list_messages(self):
        imap = IMAPHelper()
        result, data = imap.login(TEST_LOGIN, TEST_PASS)
        self.assertEquals('OK', result, "Couldn't login successfully")

        result, data = imap.list_messages()
        self.assertEquals('OK', result, "Couldn't list messages successfully")

    def test_get_message(self):
        imap = IMAPHelper()
        result, data = imap.login(TEST_LOGIN, TEST_PASS)
        self.assertEquals('OK', result, "Couldn't login successfully")

        result, data = imap.list_messages()
        self.assertEquals('OK', result, "Couldn't list messages successfully")

        result, data = imap.get_message(data[0])
        self.assertEquals('OK', result, "Couldn't get message successfully")
