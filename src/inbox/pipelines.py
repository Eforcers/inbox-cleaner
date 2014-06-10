# -*- coding: utf-8 -*-
from datetime import datetime
import logging

import constants
from inbox.helpers import IMAPHelper
from inbox.models import MoveMessageProcess
from livecount import counter
import pipeline
from pipeline.common import List
from models import MoveProcess, MoveUserProcess
from tasks import get_messages


class MoveProcessPipeline(pipeline.Pipeline):
    def run(self, move_process_id):
        logging.info("start process for move_process %s", move_process_id)
        process = MoveProcess.get_by_id(move_process_id)
        emails = process.emails

        user_processes = []
        for email in emails:
            user_process = MoveUserProcess(
                user_email=email,
                move_process_key=process.key,
                status=constants.STARTED
            )
            user_process_key = user_process.put()
            user_process_id = user_process_key.id()
            user_processes.append((yield MoveUserProcessPipeline(
                user_process_id=user_process_id, tag=process.tag)))

        yield List(*user_processes)

    def finalized(self):
        move_process_id = self.kwargs.get('move_process_id')
        logging.info('Finishing process [%s]', move_process_id)
        process = MoveProcess.get_by_id(move_process_id)
        process.status = constants.FINISHED
        process.execution_finish = datetime.now()
        process.put()


class MoveUserProcessPipeline(pipeline.Pipeline):
    def run(self, user_process_id=None, tag=None):
        user_process = MoveUserProcess.get_by_id(user_process_id)
        try:
            messages = get_messages(user_process, tag)
            message_processes = []
            counter.reset_counter(
                '%s_%s_ok_counter' % (
                    user_process.user_email, user_process.key.id()))
            counter.reset_counter(
                '%s_%s_error_counter' % (
                    user_process.user_email, user_process.key.id()))

            for batch in messages:
                message_processes.append(
                    (yield MoveBatchMessagesProcessPipeline(
                        batch=batch, user_process_id=user_process_id)))
            yield List(*message_processes)
        except Exception as e:
            if self.current_attempt >= self.max_attempts:
                logging.exception('Failed definitely retrieving for [%s] '
                                  'messages', user_process.user_email)
                user_process.status = constants.FAILED
                user_process.error_description = e.message
                user_process.put()
            else:
                logging.exception('Failed retrieving messagesfor [%s], '
                                  'try again...', user_process.user_email)
            raise e

    def finalized(self):
        user_process_id = self.kwargs.get('user_process_id')
        logging.info('Finishing user process [%s]', user_process_id)
        user_process = MoveUserProcess.get_by_id(user_process_id)
        if not self.was_aborted:
            user_process.status = constants.FINISHED
            user_process.error_description = None
            user_process.put()


class MoveBatchMessagesProcessPipeline(pipeline.Pipeline):
    def run(self, batch=None, user_process_id=None):
        user_process = MoveUserProcess.get_by_id(user_process_id)
        move_process = user_process.move_process_key.get()
        failed_messages = []
        #Create connection
        imap = IMAPHelper()
        imap.oauth1_2lo_login(user_email=user_process.user_email)
        for msg_id in batch:
            message_process = MoveMessageProcess(
                email=user_process.user_email,
                message_id=msg_id,
                user_process_key=user_process.key,
                status=constants.STARTED)
            message_process_key = message_process.put()
            try:
                move_message(user_process=user_process,
                             message_process_id=message_process_key.id(),
                             label=move_process.tag, imap=imap)
            except Exception as e:
                logging.exception(
                    'Failed while moving message [%s] for user [%s], '
                    'try again...', msg_id, user_process.user_email)
                failed_messages.append(
                    (yield MoveMessageProcessPipeline(
                        message_process_id=message_process_key.id(),
                        move_process_id=move_process.key.id()))
                )
        imap.close()


class MoveMessageProcessPipeline(pipeline.Pipeline):
    def run(self, message_process_id=None, user_process_id=None,
            move_process_id=None):
        move_process = MoveProcess.get_by_id(move_process_id)
        user_process = MoveUserProcess.get_by_id(user_process_id)
        try:
            move_message(user_process=user_process,
                         message_process_id=message_process_id,
                         label=move_process.tag)

        except Exception as e:
            if self.current_attempt >= self.max_attempts:
                logging.exception(
                    'Failed definitely moving the message id [%s] for user [%s] messages',
                    message_process_id, user_process.user_email)
                message_process = MoveMessageProcess.get_by_id(
                    message_process_id)
                message_process.status = constants.FAILED
                message_process.error_description = e.message
                message_process.put()
                counter.load_and_increment_counter(
                    '%s_%s_error_counter' % (
                        user_process.user_email, user_process.key.id()))
            else:
                logging.exception(
                    'Failed retrieving a messagee id [%s] for [%s], '
                    'try again...', message_process_id, user_process.user_email)
        raise e

