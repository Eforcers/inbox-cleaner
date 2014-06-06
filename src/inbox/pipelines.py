import pipeline
import constants
from helpers import IMAPHelper

class MoveMessageBatchProcess(pipeline.Pipeline):
    def run(self, email):
        imap = IMAPHelper()
        imap.oauth1_2lo_login(user_email=email)
        pass

class MoveMessageProcess(pipeline.Pipeline):
    def run(self, msg_id):
        pass

