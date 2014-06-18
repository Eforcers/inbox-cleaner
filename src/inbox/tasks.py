# -*- coding: utf-8 -*-
import logging
import email

from google.appengine.ext import deferred

import constants
from inbox.models import CleanMessageProcess, CleanAttachmentProcess
import secret_keys
from inbox.helpers import EmailSettingsHelper, IMAPHelper, DriveHelper, MigrationHelper
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
        return chunkify(msg_ids, num_chunks=constants.USER_CONNECTION_LIMIT)
    else:
        counter.load_and_increment_counter('%s_total_count' % user_email,
                                           delta=0,
                                           namespace=str(process_id))

    return []


def get_messages_for_cleaning(user_email=None, process_id=None):
    clean_process = CleanUserProcess.get_by_id(process_id)
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
        counter.load_and_increment_counter(
            'cleaning_%s_total_count' % user_email,
            delta=0,
            namespace=str(process_id))
        process = CleanUserProcess.get_by_id(process_id)
        process.status = constants.FINISHED
        process.put()
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
        for chunk in chunkify(chunk_ids,
                              chunk_size=constants.MESSAGE_BATCH_SIZE):
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
                        namespace=str(process_id), delta=len(chunk))
                    logging.error(
                        'Error moving message IDs [%s-%s] for user [%s]: '
                        'Result [%s] data [%s]', chunk[0], chunk[-1],
                        user_email, result, data)
            except Exception as e:
                logging.exception(
                    'Failed moving message range IDs [%s-%s] for user [%s]',
                    chunk[0], chunk[-1], user_email)
                remaining = list(set(chunk_ids) - set(moved_successfully))
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
                break
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
    if domain_name:
        try:
            primary_domain = PrimaryDomain.get_or_create(
                domain_name=domain_name)
            if primary_domain.credentials:
                email_settings_helper = EmailSettingsHelper(
                    credentials_json=primary_domain.credentials,
                    domain=domain_name,
                    refresh_token=primary_domain.refresh_token
                )
                email_settings_helper.enable_imap(user_email)
                logging.info('IMAP enabled for [%s]',
                             user_email)
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


def clean_message(msg_id='', imap=None, drive=None,
                  migration=None, folder_id=None,
                  user_email=None, process_id=None):
    process = CleanUserProcess.get_by_id(process_id)
    criteria = process.search_criteria

    msg_process = CleanMessageProcess.get_or_create(msg_id, process_id)
    if msg_process.status == constants.FINISHED:
        return True

    result, message = imap.get_message(msg_id=msg_id)

    if result != 'OK':
        raise Exception("Couldn't read message")

    result, label_data = imap.get_message_labels(msg_id=msg_id)

    labels = (((label_data[0].split('('))[2].split(')'))[0]).split()
    mail = email.message_from_string(message[0][1])
    attachments = []
    number_of_attachments = 0

    if mail.get_content_maintype() == 'multipart':
        for part in mail.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            # Is attachment
            attached = False
            number_of_attachments += 1
            attachment_process = CleanAttachmentProcess.get_or_create(
                msg_id, msg_process.key.id(), number_of_attachments
            )

            file_id = ''

            if (attachment_process.status == constants.FINISHED and
                attachment_process.url and
                attachment_process.filename and
                attachment_process.file_id
            ):
                attached = True
                attachments.append(
                    (attachment_process.url, attachment_process.filename))
                file_id = attachment_process.file_id

            if not attached:
                attachment = part.get_payload(decode=True)
                mime_type = part.get_content_type()
                filename = part.get_filename()

                insert_result = drive.insert_file(filename=filename,
                                                  mime_type=mime_type,
                                                  content=attachment,
                                                  parent_id=folder_id)
                if type(insert_result) is Exception:
                    attachment_process.error_description = (
                        insert_result.message
                    )
                    attachment_process.put()
                    raise insert_result

                drive_url = insert_result['alternateLink']
                file_id = insert_result['id']

                attachment_process.url = drive_url
                attachment_process.file_id = file_id
                attachment_process.status = constants.FINISHED
                attachment_process.filename = filename
                attachment_process.put()

                attachments.append((drive_url, filename))

            permission_result = drive.insert_permission(file_id=file_id,
                                                 value=user_email,
                                                 type='user', role='writer')

            if type(permission_result) is Exception:
                attachment_process.error_description = (
                    permission_result.message
                )
                attachment_process.put()
                raise permission_result

            part.set_payload("")
            for header in part.keys():
                part.__delitem__(header)

    msg_process.status = constants.DUPLICATED
    msg_process.put()

    for url, filename in attachments:
        body_suffix = '<a href="%s">%s</a>' % (url, filename)
        new_payload = email.MIMEText.MIMEText(body_suffix, 'html')
        mail.attach(new_payload)

    # Send new mail
    migration_result = migration.migrate_mail(user_email=user_email, msg=mail,
                                    labels=labels)
    if type(migration_result) is Exception:
        msg_process.error_description = migration_result.message
        msg_process.put()
        raise migration_result
    else:
        msg_process.status = constants.MIGRATED
        msg_process.put()

    # Then delete previous email
    delete_result = imap.delete_message(msg_id=msg_id, criteria=criteria)
    if type(delete_result) is Exception:
        msg_process.error_description = delete_result.message
        msg_process.put()
        raise delete_result

    msg_process.status = constants.FINISHED
    msg_process.put()

    return True


def clean_messages(user_email=None, password=None, chunk_ids=list(),
                   retry_count=0, process_id=None):
    cleaned_successfully = []
    if len(chunk_ids) <= 0:
        process = CleanUserProcess.get_by_id(process_id)
        process.status = constants.FINISHED
        process.put()
        return True

    try:
        process = CleanUserProcess.get_by_id(process_id)
        imap = IMAPHelper()
        imap.login(email=user_email, password=process.source_password)
        imap.select()

        primary_domain = PrimaryDomain.get_or_create(
                secret_keys.OAUTH2_CONSUMER_KEY)
        try:
            drive = DriveHelper(credentials_json=primary_domain.credentials,
                                admin_email=primary_domain.admin_email,
                                refresh_token=primary_domain.refresh_token)
            folder = drive.get_folder(constants.ATTACHMENT_FOLDER)
            if not folder:
                folder = drive.create_folder(constants.ATTACHMENT_FOLDER)
            sub_folder = drive.get_folder(user_email)
            if not sub_folder:
                sub_folder = drive.create_folder(user_email,
                                                 [{'id': folder['id']}])
        except Exception as e:
            logging.error(
                "Couldn't authenticate drive for user %s" % user_email)
            raise e

        try:
            migration = MigrationHelper(
                credentials_json=primary_domain.credentials,
                refresh_token=primary_domain.refresh_token)
        except Exception as e:
            logging.error(
                "Couldn't authenticate migration api for user %s" % user_email)
            raise e

        for message_id in chunk_ids:
            try:
                result = clean_message(msg_id=message_id, imap=imap,
                                       drive=drive,
                                       migration=migration,
                                       folder_id=sub_folder['id'],
                                       user_email=user_email,
                                       process_id=process_id)
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
        process.status = constants.FINISHED
        process.put()
    except Exception as e:
        logging.exception('Failed cleaning messages chunk')
        raise e
    finally:
        if imap:
            imap.close()


def schedule_user_cleaning(user_email=None, process_id=None):
    all_messages = get_messages_for_cleaning(
        user_email=user_email, process_id=process_id)

    for chunk_ids in all_messages:
        if len(chunk_ids) > 0:
            logging.info('Scheduling user [%s] messages cleaning', user_email)
            deferred.defer(clean_messages, user_email=user_email,
                           chunk_ids=chunk_ids,
                           process_id=process_id)


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