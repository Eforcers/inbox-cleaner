# -*- coding: utf-8 -*-
import logging

from helpers import IMAPHelper
import constants
from models import MoveMessageProcess
from livecount import counter


def get_messages(user_process=None, tag=None):
    batch_list = []
    try:
        imap = IMAPHelper()
        imap.oauth1_2lo_login(user_email=user_process.user_email)
        if tag:
            logging.info('Creating label [%s]', tag)
            imap.create_label(tag)
        msg_ids = imap.list_messages(only_from_trash=True)
        imap.close()

        n = constants.MESSAGE_BATCH_SIZE

        for i in range(0, len(msg_ids), n):
            ids = msg_ids[i:i + n]
            batch_list.append(ids)
    except Exception as e:
        logging.exception('Failed retrieving messages')
        user_process.status = constants.FAILED
        user_process.error_description = e.message
        user_process.put()
    return batch_list


def move_message(user_process=None, msg_id=None, label=None):
    message_process = MoveMessageProcess(email=user_process.user_email,
                                         message_id=msg_id,
                                         user_process_key=user_process.key,
                                         status=constants.STARTED)

    try:
        imap = IMAPHelper()
        imap.oauth1_2lo_login(user_email=user_process.user_email)
        logging.info('Moving msg [%s] to label [%s]', msg_id, label)
        result, data = imap.copy_message(msg_id=msg_id,
                                         destination_label=label,
                                         only_from_trash=True)
        imap.close()
        if result == 'OK':
            counter.load_and_increment_counter(
                '%s_%s_ok_counter' % (
                    user_process.user_email, user_process.key.id()))
            message_process.status = constants.FINISHED
        else:
            counter.load_and_increment_counter(
                '%s_%s_error_counter' % (
                    user_process.user_email, user_process.key.id()))
            message_process.status = constants.FAILED
            message_process.error_description = result
    except Exception as e:
        logging.exception('Exception while moving')
        counter.load_and_increment_counter(
            '%s_%s_error_counter' % (
                user_process.user_email, user_process.key.id()))
        message_process.status = constants.FAILED
        message_process.error_description = e.message
    message_process.put()






