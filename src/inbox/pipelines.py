# -*- coding: utf-8 -*-
from google.appengine.ext import ndb
import constants
import pipeline
from pipeline.common import List, Return
import logging

class MoveProcessPipeline(pipeline.Pipeline):
    def run(self, move_process_id):
        logging.info("start process for move_process %s", move_process_id)
        pass
