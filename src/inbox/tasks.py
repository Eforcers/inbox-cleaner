# -*- coding: utf-8 -*-
import logging

from google.appengine.ext import deferred

from helpers import IMAPHelper
import constants
from inbox.models import MoveUserProcess
from livecount import counter


def get_messages(user_email=None, tag=None, user_process_id=None):
    imap = IMAPHelper()
    imap.oauth1_2lo_login(user_email=user_email)
    if tag:
        logging.info('Creating label [%s]', tag)
        imap.create_label(tag)
    msg_ids = imap.list_messages(only_from_trash=True)
    imap.close()
    n = constants.MESSAGE_BATCH_SIZE
    counter.load_and_increment_counter(
        '%s_%s_total_counter' % (
            user_email, user_process_id), delta=len(msg_ids))
    return [msg_ids[i::n] for i in xrange(n)]


def move_messages(user_email=None, tag=None, chunk_ids=[],
                  user_process_id=None, is_failed=False):
    failed_ids = []
    try:
        imap = IMAPHelper()
        imap.oauth1_2lo_login(user_email=user_email)
        for message_id in chunk_ids:
            try:
                result, data = imap.copy_message(msg_id=message_id,
                                                 destination_label=tag,
                                                 only_from_trash=True)
                if result == 'OK':
                    counter.load_and_increment_counter(
                        '%s_%s_ok_counter' % (
                            user_email, user_process_id))
                else:
                    failed_ids.append(message_id)
                    counter.load_and_increment_counter(
                        '%s_%s_error_counter' % (
                            user_email, user_process_id))
                    logging.error('Error moving message ID [%s] for user [%s]: [%s]',
                                  message_id, user_email, result)
            except Exception as e:
                failed_ids.append(message_id)
                logging.exception('Failed moving individual message ID [%s] for user [%s]', message_id, user_email)
    except Exception as e:
        logging.exception('Failed moving messages chunk')
        raise e
    finally:
        if imap:
            imap.close()
    #Schedule failed ones
    if len(failed_ids) > 0 and not is_failed:
        deferred.defer(move_messages, user_email=user_email, tag=tag,
                       chunk_ids=failed_ids, is_failed=True)


def schedule_user_move(user_email=None, tag=None, move_process_key=None):
    user_process = MoveUserProcess(
        user_email=user_email,
        move_process_key=move_process_key,
        status=constants.STARTED
    )
    user_process_key = user_process.put()
    for chunk_ids in get_messages(user_email, tag, user_process_key.id()):
        logging.info('Scheduling user [%s] messages move', user_email)
        deferred.defer(move_messages, user_email=user_email, tag=tag,
                       chunk_ids=chunk_ids)
