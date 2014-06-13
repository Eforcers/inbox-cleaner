from inbox import constants
from inbox.models import PrimaryDomain
from tests import AppEngineFlaskTestCase
from inbox.helpers import IMAPHelper, DriveHelper
from secret_keys import (
    TEST_LOGIN, TEST_PASS, TEST_OAUTH2_CONSUMER_KEY,
    TEST_OAUTH2_CONSUMER_SECRET, TEST_PRIMARY_CREDENTIALS,
    TEST_PRIMARY_ADMIN_EMAIL, TEST_PRIMARY_REFRESH_TOKEN,
    TEST_FAKE_PRIMARY_CREDENTIALS
)
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

class DriveHelperTestCase(AppEngineFlaskTestCase):

    def test_init(self):
        admin_email = TEST_PRIMARY_ADMIN_EMAIL
        
        # Test wrong credentials
        try:
            drive = DriveHelper(credentials_json=TEST_FAKE_PRIMARY_CREDENTIALS,
                        admin_email=admin_email,
                        refresh_token='')
            drive.get_folder('anything')
            assert False
        except:
            pass

        # And then the right ones
        drive = DriveHelper(credentials_json=TEST_PRIMARY_CREDENTIALS,
                    admin_email=admin_email,
                    refresh_token=TEST_PRIMARY_REFRESH_TOKEN)
        folder = drive.get_folder('anything')

    def test_get_and_create_folder(self):
        admin_email = TEST_PRIMARY_ADMIN_EMAIL

        drive = DriveHelper(credentials_json=TEST_PRIMARY_CREDENTIALS,
                    admin_email=admin_email,
                    refresh_token=TEST_PRIMARY_REFRESH_TOKEN)

        # Create and check folder
        folder = drive.get_folder('integration-test-folder')
        self.assertEquals(None, folder, "Folder shouldn't exist")

        folder = drive.create_folder('integration-test-folder')
        self.assertNotEquals(None, folder, "Folder exists now")

        created_folder = drive.get_folder('integration-test-folder')
        self.assertEquals(created_folder, folder, "Folder wasn't created")

        # Create and check subfolder
        sub_folder = drive.get_folder('integration-test-subfolder')
        self.assertEquals(None, sub_folder, "Folder shouldn't exist")

        parents = [{'id': folder['id']}]
        sub_folder = drive.create_folder(
            'integration-test-subfolder', parents=parents)
        self.assertNotEquals(None, sub_folder, "Subfolder exists now")

        created_subfolder = drive.get_folder(
            'integration-test-subfolder', parent_id=folder['id'])
        self.assertEquals(created_subfolder, sub_folder, "Subfolder wasn't created")

        # Garbage collect
        drive.service.files().delete(fileId=folder['id']).execute()
        drive.service.files().delete(fileId=sub_folder['id']).execute()

    def test_insert_file_and_get_metadata(self):
        admin_email = TEST_PRIMARY_ADMIN_EMAIL

        drive = DriveHelper(credentials_json=TEST_PRIMARY_CREDENTIALS,
                    admin_email=admin_email,
                    refresh_token=TEST_PRIMARY_REFRESH_TOKEN)

        # Create in root
        created_file = drive.insert_file("integration-test.txt", 'plain/text', 'lorem ipsum')
        self.assertNotEquals(None, created_file, "File wasn't created")

        saved_file = drive.get_metadata(title="integration-test.txt")
        self.assertEquals(created_file['md5Checksum'],
                          saved_file['md5Checksum'], "The file wasn't created")

        # Create in a folder
        created_folder = drive.create_folder("integration-text-folder")
        self.assertNotEquals(None, created_folder, "Folder wasn't created")

        created_folder_file = drive.insert_file(
            "integration-foldertest.txt", 'plain/text', 'lorem ipsum',
            parent_id=created_folder['id'])
        self.assertNotEquals(None, created_folder_file,
                             "File wasn't created")

        saved_folder_file = drive.get_metadata(
            "integration-foldertest.txt", parent_id=created_folder['id'])
        self.assertEquals(created_folder_file['md5Checksum'],
                          saved_folder_file['md5Checksum'],
                          "File in folder wasnn't created")

        # Garbage Collect
        drive.service.files().delete(fileId=created_folder['id']).execute()
        drive.service.files().delete(fileId=created_file['id']).execute()
        drive.service.files().delete(fileId=created_folder_file['id']).execute()

    def test_insert_permission(self):
        admin_email = TEST_PRIMARY_ADMIN_EMAIL

        drive = DriveHelper(credentials_json=TEST_PRIMARY_CREDENTIALS,
                    admin_email=admin_email,
                    refresh_token=TEST_PRIMARY_REFRESH_TOKEN)

        # Create in root
        created_file = drive.insert_file("integration-test.txt", 'plain/text', 'lorem ipsum')
        self.assertNotEquals(None, created_file, "File wasn't created")

        permission = drive.insert_permission(file_id=created_file['id'],
                                value='dev@eforcers.com',
                                type='user', role='reader')

        self.assertNotEquals(None, permission, "Permission not set")

        drive.service.files().delete(fileId=created_file['id']).execute()
