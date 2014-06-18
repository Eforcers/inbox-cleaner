from inbox.models import CleanUserProcess
from inbox.tasks import clean_message
from tests import AppEngineFlaskTestCase
import mock
from inbox.helpers import IMAPHelper, DriveHelper, MigrationHelper
from fixtures import IMAP_MESSAGE


class CleanMessagesTestCase(AppEngineFlaskTestCase):
    def get_message_labels(self, msg_id=None):
        return 'OK', ['10 (X-GM-LABELS ("\\\\Inbox" "\\\\Important") UID 59)']

    def get_message(self, msg_id=None):
        return 'OK', IMAP_MESSAGE

    def get_folder(self, name=None, parent_id=None):
        return {'id': '1'}

    def create_folder(self, name=None, parents=None):
        return {'id': '2'}

    def insert_file(self, filename=None, mime_type=None, content=None, parent_id=None):
        return {'id': '1', 'alternateLink': 'http://eforcers.com'}

    def insert_permission(self, file_id=None, value=None, type=None, role=None):
        return True

    def delete_message(self, msg_id=None, criteria='', mailbox_is_trash=False):
        return True

    def migrate_mail(self, user_email=None, msg=None, labels=None):
        return True

    def get_by_id(cls, id, parent=None, **ctx_options):
        result = object()
        result.search_criteria = 'anything'
        return result

    def init(self):
        return

    @mock.patch.object(IMAPHelper, 'get_message', get_message)
    @mock.patch.object(IMAPHelper, 'get_message_labels', get_message_labels)
    @mock.patch.object(IMAPHelper, 'delete_message', delete_message)
    @mock.patch.object(DriveHelper, 'get_folder', get_folder)
    @mock.patch.object(DriveHelper, 'create_folder', create_folder)
    @mock.patch.object(DriveHelper, 'insert_file', insert_file)
    @mock.patch.object(DriveHelper, 'insert_permission', insert_permission)
    @mock.patch.object(DriveHelper, '__init__', init)
    @mock.patch.object(MigrationHelper, 'migrate_mail', migrate_mail)
    @mock.patch.object(MigrationHelper, '__init__', init)
    def test_clean_message(self):
        process = CleanUserProcess(
            process_name = 'unit-test',
            owner_email = 'administrador@eforcers.com.co',
            source_email = 'prueba42@eforcers.com.co',
            source_password = 'fakestpass',
            destination_message_email = 'prueba42@eforcers.com.co'
        )
        process_key = process.put()
        imap = IMAPHelper()
        drive = DriveHelper()
        migration = MigrationHelper()
        result = clean_message(msg_id='1', imap=imap,
                    drive=drive,
                    migration=migration,
                    folder_id='1',
                    user_email='prueba42@eforcers.com.co',
                    process_id=process_key.id())

        self.assertEquals(True, result, "Message cleanning not finished")