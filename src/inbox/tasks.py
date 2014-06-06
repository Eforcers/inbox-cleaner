# -*- coding: utf-8 -*-
from models import MoveUserProcess
from helpers import IMAPHelper
import constants
from models import MoveMessageProcess
from livecount import counter

def get_messages(user_process=None):
    imap = IMAPHelper()
    imap.oauth1_2lo_login(user_email=user_process.email)
    msg_ids = imap.list_messages(only_from_trash=True)

    n = constants.MESSAGE_BATCH_SIZE
    return [msg_ids[i:i+n] for i in range(0, len(msg_ids), n)]

def move_message(user_process=None, msg_id=None, label=None):
    message_process = MoveMessageProcess(email=user_process.email,
                       message_id=msg_id,
                       user_process_key=user_process.key,
                       error_description='')

    try:
        imap = IMAPHelper()
        imap.oauth1_2lo_login(user_email=user_process.email)
        result, data = imap.copy_message(msg_id=msg_id, new_label=label)

        if result == 'OK':
            counter.load_and_increment_counter(
                '%s_%s_ok_counter' % (user_process.email, user_process.key.id()))
            message_process.status = constants.FINISHED
        else:
            counter.load_and_increment_counter(
                '%s_%s_error_counter' % (user_process.email, user_process.key.id()))
            message_process.status = constants.FAILED
            message_process.error_description = result
    except Exception as e:
        counter.load_and_increment_counter(
                '%s_%s_error_counter' % (user_process.email, user_process.key.id()))
        message_process.status = constants.FAILED
        message_process.error_description = e.message
    message_process.put()






