# -*- coding: utf-8 -*-
from google.appengine.ext import ndb
import constants
from livecount import counter
import pipeline
from pipeline.common import List, Return
import logging
from helpers import IMAPHelper
from models import MoveProcess, MoveUserProcess
from tasks import get_messages, move_message

class MoveProcessPipeline(pipeline.Pipeline):
    def run(self, move_process_id):
        logging.info("start process for move_process %s", move_process_id)
        process = MoveProcess.get_by_id(move_process_id)
        emails = process.emails

        user_processes = []
        for email in emails:
            user_process = MoveUserProcess(
                user_email = email,
                move_process_key = process.key
            )
            user_process_key = user_process.put()
            user_process_id = user_process_key.id()

            user_processes.append((yield MoveUserProcessPipeline(
                user_process_id=user_process_id)))

        yield List(*user_process)

    def finalized(self):
        move_process_id = self.kwargs.get('move_process_id')
        process = MoveProcess.get_by_id(move_process_id)
        process.state = constants.FINISHED
        process.put()


class MoveUserProcessPipeline(pipeline.Pipeline):
    def run(self, user_process_id=None):
        user_process = MoveUserProcess.get_by_id(user_process_id)
        messages = get_messages(user_process)
        message_processes = []

        counter.reset_counter('%s_%s_ok_counter' % (user_process.email, user_process.key.id()))
        counter.reset_counter('%s_%s_error_counter' % (user_process.email, user_process.key.id()))

        for batch in messages:
            message_processes.append((yield MoveMessageProcessPipeline(
                batch=batch, user_process_id=user_process_id)))
        yield List(*message_processes)

    def finalized(self):
        user_process_id = self.kwargs.get('user_process_id')
        user_process = MoveUserProcess.get_by_id(user_process_id)
        user_process.state = constants.FINISHED
        user_process.put()

class MoveMessageProcessPipeline(pipeline.Pipeline):
    def run(self, batch=None, user_process_id=None):
        user_process = MoveUserProcess.get_by_id(user_process_id)
        move_process = user_process.move_process_key.get()
        for msg_id in batch:
            move_message(user_process=user_process, msg_id=msg_id, label=move_process.tag)

