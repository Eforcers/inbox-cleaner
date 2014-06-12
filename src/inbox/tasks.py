# -*- coding: utf-8 -*-
import logging
import email

from google.appengine.ext import deferred

import constants
from helpers import EmailSettingsHelper, IMAPHelper
from models import ProcessedUser, MoveProcess, CleanUserProcess, \
    PrimaryDomain
from util import chunkify
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
        except Exception as e:
            logging.exception('Error creating label or retrieving messages for '
                              'user [%s]', user_email)
            processed_user = ProcessedUser.get_by_id(email)
            if not processed_user:
                processed_user = ProcessedUser(id=user_email, ok_count=0,
                                               error_count=0,
                                               total_count=list(),
                                               error_description=list())
            processed_user.error_description.append(e.message)
            processed_user.put()

            return []
    except Exception as e:
        logging.exception('Authentication or connection problem for user '
                          '[%s]', user_email)
        processed_user = ProcessedUser.get_by_id(user_email)
        if not processed_user:
            processed_user = ProcessedUser(id=user_email, ok_count=0,
                                           error_count=0,
                                           total_count=list(),
                                           error_description=list())
        processed_user.error_description.append(e.message)
        processed_user.put()

        return []
    finally:
        if imap:
            imap.close()
    # Assuming IMAP connection was OK
    if len(msg_ids) > 0:
        counter.load_and_increment_counter('%s_total_count' % user_email,
                                           delta=len(msg_ids),
                                           namespace=str(process_id))
        return chunkify(msg_ids, constants.USER_CONNECTION_LIMIT)
    else:
        counter.load_and_increment_counter('%s_total_count' % user_email,
                                           delta=0,
                                           namespace=str(process_id))

    return []


def get_messages_for_cleaning(user_email=None, process_id=None,
                              clean_process_key=None):
    clean_process = clean_process_key.get()
    imap = IMAPHelper()
    imap.login(email=user_email, password=clean_process.source_password)
    msg_ids = imap.list_messages(criteria=clean_process.search_criteria,
                                 only_with_attachments=True)
    imap.close()

    if len(msg_ids) > 0:
        if constants.USER_CONNECTION_LIMIT < len(msg_ids):
            n = constants.USER_CONNECTION_LIMIT
        else:
            n = len(msg_ids)
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
        for chunk in chunkify(chunk_ids, constants.MESSAGE_BATCH_SIZE):
            try:
                result, data = imap.copy_message(
                    msg_id="%s:%s" % (chunk[0], chunk[-1]),
                    destination_label=tag
                )
                if result == 'OK':
                    counter.load_and_increment_counter(
                        '%s_ok_count' % (user_email),
                        namespace=str(process_id), delta=len(chunk))
                    moved_successfully.extend(chunk)
                else:
                    counter.load_and_increment_counter(
                        '%s_error_count' % user_email,
                        namespace=str(process_id))
                    logging.error(
                        'Error moving message IDs [%s-%s] for user [%s]: '
                        'Result [%s] data [%s]', chunk[0], chunk[-1],
                        user_email, result, data)
            except Exception as e:
                logging.exception(
                    'Failed moving message range IDs [%s-%s] for user [%s]',
                    chunk[0], chunk[-1], user_email)
                remaining = list(set(chunk) - set(moved_successfully))
                # Keep retrying if messages are being moved
                if retry_count >= 3 and len(moved_successfully) == 0:
                    logging.error('Giving up with remaining [%s] messages for '
                                  'user [%s]', len(remaining),
                                  user_email)
                    counter.load_and_increment_counter(
                        '%s_error_count' % user_email, delta=len(remaining),
                        namespace=str(process_id))
                else:
                    logging.info(
                        'Scheduling [%s] remaining messages for user [%s]',
                        len(remaining), user_email)
                    deferred.defer(move_messages, user_email=user_email,
                                   tag=tag,
                                   chunk_ids=remaining,
                                   process_id=process_id,
                                   retry_count=retry_count + 1)
    except Exception as e:
        logging.exception('Authentication, connection or select problem for '
                          'user [%s]', user_email)
        counter.load_and_increment_counter(
            '%s_error_count' % user_email, delta=len(chunk_ids),
            namespace=str(process_id))
    finally:
        logging.info(
            'Succesfully moved [%s] messages for user [%s] in this task',
            len(moved_successfully), user_email)
        if imap:
            imap.close()


def schedule_user_move(user_email=None, tag=None, move_process_key=None,
                       domain_name=None):
    try:
        primary_domain = PrimaryDomain.get_or_create(domain_name=domain_name)
        if primary_domain.credentials:
            email_settings_helper = EmailSettingsHelper(
                credentials_json=primary_domain.credentials,
                domain=domain_name,
                refresh_token=primary_domain.refresh_token
            )
            email_settings_helper.enable_imap(user_email)
        else:
            logging.warn('Error trying to enable IMAP for user [%s]',
                         user_email)
    except:
        logging.exception('Domain [%s] is not authorized, IMAP not enabled',
                          domain_name)

    for chunk_ids in get_messages(user_email=user_email, tag=tag,
                                  process_id=move_process_key.id()):
        if len(chunk_ids) > 0:
            logging.info('Scheduling user [%s] messages move', user_email)
            deferred.defer(move_messages, user_email=user_email, tag=tag,
                           chunk_ids=chunk_ids,
                           process_id=move_process_key.id())


def clean_message(msg_id='', imap=None):
    result, message = imap.get_message(msg_id=msg_id)
    mail_date = imap.get_date(msg_id=msg_id)
    if result != 'OK':
        raise
    result, label_data = imap.get_message_labels(msg_id=msg_id)
    labels = (((label_data[0].split('('))[2].split(')'))[0]).split()
    mail = email.message_from_string(message[0][1])
    attachments = []

    if mail.get_content_maintype() == 'multipart':
        for part in mail.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            attachment = part.get_payload(decode=True)
            logging.info("Attachment content is %s" % attachment)

            # Send attachment to drive

            # And get the drive url

            drive_url = 'http://eforcers.com'
            attachments.append((drive_url, part.get_filename()))

            part.set_payload("")
            for header in part.keys():
                part.__delitem__(header)

    for url, filename in attachments:
        body_suffix = '<a href="%s">%s</a>' % (url, filename)
        new_payload = email.MIMEText.MIMEText(body_suffix, 'html')
        mail.attach(new_payload)

    # Send new mail

    # Then delete previous email

    # For tests only - remove later
    # result, data = imap.mail_connection.append('prueba', None, mail_date, mail.as_string())

    return True


def clean_messages(user_email=None, password=None, chunk_ids=list(),
                   retry_count=0,
                   process_id=None):
    cleaned_successfully = []
    if len(chunk_ids) <= 0:
        return True
    try:
        process = CleanUserProcess.get_by_id(process_id)
        imap = IMAPHelper()
        imap.login(email=user_email, password=process.source_password)
        imap.select()
        for message_id in chunk_ids:
            try:
                result = clean_message(msg_id=message_id, imap=imap)
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
    all_messages = get_messages_for_cleaning(
        user_email=user_email, clean_process_key=clean_process_key)
    for chunk_ids in all_messages:
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
            else:
                total_count = 0
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