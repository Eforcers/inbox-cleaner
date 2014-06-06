# -*- coding: utf-8 -*-
from google.appengine.ext import ndb
import constants
import pipeline
from pipeline.common import List, Return
import logging
from helpers import IMAPHelper

class MoveProcessPipeline(pipeline.Pipeline):
    def run(self, move_process_id):
        logging.info("start process for move_process %s", move_process_id)
        pass

class MoveMessageBatchProcess(pipeline.Pipeline):
    def run(self, email):
        imap = IMAPHelper()
        imap.oauth1_2lo_login(user_email=email)
        pass

class MoveMessageProcess(pipeline.Pipeline):
    def run(self, msg_id):
        pass

