# -*- coding: utf-8 -*-
import logging

from google.appengine.ext import deferred

from helpers import IMAPHelper
import constants
from inbox.models import ProcessedUser, MoveProcess
from livecount import counter


def get_messages(user_email=None, tag=None, process_id=None):
    imap = None
    msg_ids = []
    try:
        imap = IMAPHelper()
        imap.oauth1_2lo_login(user_email=user_email)
        try:
            if tag:
                logging.info('Creating label [%s]', tag)
                imap.create_label(tag)
            msg_ids = imap.list_messages(only_from_trash=True)
        except:
            logging.exception('Error creating label or retrieving messages for '
                              'user [%s]', user_email)
            return []
    except:
        logging.exception('Authentication or connection problem for user '
                          '[%s]', user_email)
        return []
    finally:
        if imap:
            imap.close()
    # Assuming IMAP connection was OK
    if len(msg_ids) > 0:
        n = constants.MESSAGE_BATCH_SIZE
        counter.load_and_increment_counter('%s_total_count' % user_email,
                                           delta=len(msg_ids),
                                           namespace=str(process_id))
        return [msg_ids[i::n] for i in xrange(n)]
    return []


def get_messages_for_cleaning(user_email=None, process_id=None,
                              clean_process_key=None):
    clean_process = clean_process_key.get()
    imap = IMAPHelper()
    imap.oauth1_2lo_login(user_email=user_email)
    msg_ids = imap.list_messages(criteria=clean_process.search_criteria)
    imap.close()
    if len(msg_ids) > 0:
        n = constants.MESSAGE_BATCH_SIZE
        counter.load_and_increment_counter(
            'cleaning_%s_total_count' % user_email,
            delta=len(msg_ids),
            namespace=str(process_id))
        return [msg_ids[i::n] for i in xrange(n)]
    else:
        return []


def move_messages(user_email=None, tag=None, chunk_ids=list(),
                  process_id=None, retry_count=0):
    moved_successfully = []
    imap = None
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
        logging.exception('Authentication, connection or select problem for '
                          'user [%s]', user_email)
        counter.load_and_increment_counter(
                        '%s_error_count' % user_email, delta=len(chunk_ids),
                        namespace=str(process_id))
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


def clean_message(msg_id=''):
    logging.info("Cleaning message %s" % msg_id)
    return True


def clean_messages(user_email=None, chunk_ids=list(), retry_count=0,
                   process_id=None):
    cleaned_successfully = []
    if len(chunk_ids) <= 0:
        return True
    try:
        imap = IMAPHelper()
        imap.oauth1_2lo_login(user_email=user_email)
        imap.select()
        for message_id in chunk_ids:
            try:
                result = clean_message(msg_id=message_id)
                if result:
                    counter.load_and_increment_counter(
                        'cleaning_%s_ok_count' % (user_email),
                        namespace=str(process_id))
                    cleaned_successfully.append(message_id)
                else:
                    counter.load_and_increment_counter(
                        'cleaning_%s_error_count' % user_email,
                        namespace=str(process_id))
                    logging.error(
                        'Error cleaning message ID [%s] for user [%s]: [%s] ',
                        message_id, user_email, result)
            except Exception as e:
                logging.exception(
                    'Failed cleaning individual message ID [%s] for user [%s]',
                    message_id, user_email)
                remaining = list(set(chunk_ids) - set(cleaned_successfully))
                if retry_count < 3:
                    logging.info(
                        'Scheduling [%s] remaining cleaning messages for user [%s]',
                        len(remaining), user_email)
                    deferred.defer(clean_messages, user_email=user_email,
                                   chunk_ids=remaining,
                                   process_id=process_id,
                                   retry_count=retry_count + 1)
                else:
                    logging.info(
                        'Giving up with cleaning remaining [%s] messages for '
                        'user [%s]', len(remaining),
                        user_email)
                    counter.load_and_increment_counter(
                        'cleaning_%s_error_count' % user_email,
                        delta=len(remaining),
                        namespace=str(process_id))
                break
    except Exception as e:
        logging.exception('Failed cleaning messages chunk')
        raise e
    finally:
        if imap:
            imap.close()


def schedule_user_cleaning(user_email=None, clean_process_key=None):
    for chunk_ids in get_messages_for_cleaning(
            user_email=user_email, clean_process_key=clean_process_key):
        if len(chunk_ids) > 0:
            logging.info('Scheduling user [%s] messages cleaning', user_email)
            deferred.defer(clean_messages, user_email=user_email,
                           chunk_ids=chunk_ids,
                           process_id=clean_process_key.id())


def generate_count_report():
    # Process counters with the latest syntax
    futures = []
    processes = MoveProcess.query().fetch()
    logging.info('Generating count report in [%s] processes', len(processes))
    for process in processes:
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
        logging.info('Updating process counters: total [%s] ok [%s] error ['
                     '%s]', process_total_count, process_ok_count,
                     process_error_count)
        process.ok_count = process_ok_count
        process.error_count = process_error_count
        process.total_count = process_total_count
        futures.append(process.put_async())
    # Process futures
    [future.get_result() for future in futures]