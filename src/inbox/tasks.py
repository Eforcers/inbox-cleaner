# -*- coding: utf-8 -*-
import logging

from google.appengine.ext import deferred

from helpers import IMAPHelper
import constants
from inbox.models import ProcessedUser, MoveProcess
from livecount import counter


def get_messages(user_email=None, tag=None, process_id=None):
    imap = IMAPHelper()
    imap.oauth1_2lo_login(user_email=user_email)
    if tag:
        logging.info('Creating label [%s]', tag)
        imap.create_label(tag)
    msg_ids = imap.list_messages(only_from_trash=True)
    imap.close()
    if len(msg_ids) > 0:
        n = constants.MESSAGE_BATCH_SIZE
        counter.load_and_increment_counter('%s_total_count' % user_email,
                                           delta=len(msg_ids),
                                           namespace=str(process_id))
        return [msg_ids[i::n] for i in xrange(n)]
    else:
        return []


def move_messages(user_email=None, tag=None, chunk_ids=list(),
                  process_id=None, retry_count=0):
    moved_successfully = []
    if len(chunk_ids) <= 0:
        return True
    try:
        imap = IMAPHelper()
        imap.oauth1_2lo_login(user_email=user_email)
        imap.select(only_from_trash=True)
        for message_id in chunk_ids:
            try:
                result, data = imap.copy_message(
                    msg_id=message_id,
                    destination_label=tag,
                    only_from_trash=True
                )
                if result == 'OK':
                    counter.load_and_increment_counter(
                        '%s_ok_count' % (user_email),
                        namespace=str(process_id))
                    moved_successfully.append(message_id)
                else:
                    counter.load_and_increment_counter(
                        '%s_error_count' % user_email,
                        namespace=str(process_id))
                    logging.error(
                        'Error moving message ID [%s] for user [%s]: [%s] '
                        'data [%s]',
                        message_id, user_email, result, data)
            except Exception as e:
                logging.exception(
                    'Failed moving individual message ID [%s] for user [%s]',
                    message_id, user_email)
                remaining = list(set(chunk_ids) - set(moved_successfully))
                if retry_count < 3:
                    logging.info(
                        'Scheduling [%s] remaining messages for user [%s]',
                        len(remaining), user_email)
                    deferred.defer(move_messages, user_email=user_email,
                                   tag=tag,
                                   chunk_ids=remaining,
                                   process_id=process_id,
                                   retry_count=retry_count + 1)
                else:
                    logging.info('Giving up with remaining [%s] messages for '
                                 'user [%s]', len(remaining),
                                 user_email)
                    counter.load_and_increment_counter(
                        '%s_error_count' % user_email, delta=len(remaining),
                        namespace=str(process_id))
                break
    except Exception as e:
        logging.exception('Failed moving messages chunk')
        raise e
    finally:
        if imap:
            imap.close()


def schedule_user_move(user_email=None, tag=None, move_process_key=None):
    for chunk_ids in get_messages(user_email=user_email, tag=tag,
                                  process_id=move_process_key.id()):
        if len(chunk_ids) > 0:
            logging.info('Scheduling user [%s] messages move', user_email)
            deferred.defer(move_messages, user_email=user_email, tag=tag,
                           chunk_ids=chunk_ids,
                           process_id=move_process_key.id())


def generate_count_report():
    # Process counters with the latest syntax
    futures = []
    for process in MoveProcess.query().fetch():
        process_ok_count = 0
        process_error_count = 0
        process_total_count = 0
        for email in process.emails:
            user = ProcessedUser.get_by_id(email)
            if not user:
                user = ProcessedUser(id=email, ok_count=0, error_count=0,
                                     total_count=list())
            total_count = counter.load_and_get_count(
                '%s_total_count' % email, namespace=str(process.key.id()))
            if total_count:
                process_total_count += total_count
                if total_count not in user.total_count:
                    user.total_count.append(total_count)
            ok_count = counter.load_and_get_count(
                '%s_ok_count' % email, namespace=str(process.key.id()))
            if ok_count:
                process_ok_count += ok_count
                user.ok_count += ok_count
            error_count = counter.load_and_get_count(
                '%s_error_count' % email, namespace=str(process.key.id()))
            if error_count:
                process_error_count += error_count
                user.error_count += error_count
            futures.append(user.put_async())
        process.ok_count = process_ok_count
        process.error_count = process_error_count
        process.total_count = process_total_count
        futures.append(process.put_async())
    # Process futures
    [future.get_result() for future in futures]