#!/usr/bin/env python2.7


import sys
import os
import logging

from pphelper import HelperUtils

import pdb


class Logger(object):
	def __init__(self, name='NoLogNameParsed', logdir=os.getcwd(), format=1):
		file_log = '{name}_{time}.{ext}'.format( name=name, time=HelperUtils.gen_timestamp(), ext='log' )
		logger = logging.getLogger( "myroot.%s" % name ) # __name__ is the name of the CURRENT module, e.g. launch_process or "main"
		#logger = logging.getLogger('%s.%s' % (__name__, name) ) # __name__ is the name of the CURRENT module, e.g. launch_process
		#logger = logging.getLogger(__name__)
		logger.setLevel(logging.DEBUG) #specifies the lowest-severity log message a logger will handle,
		if not logger.handlers:
			file_name = os.path.join(logdir, file_log)
			fh = logging.FileHandler(file_name)

			if format == 0:
				fh_formatter = logging.Formatter('%(message)s')
				ch_formatter = logging.Formatter('%(message)s')
			elif format == 1: #these fields are TAB SEPERATED
				fh_formatter = logging.Formatter('%(asctime)s	%(filename)s	%(levelname)s	%(message)s')
				ch_formatter = logging.Formatter('%(levelname)s	%(message)s')
			elif format == 2:
				fh_formatter = logging.Formatter('%(asctime)s %(filename)-18s %(levelname)-8s %(message)s')
				ch_formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
				# file format (fh_formatter) gives ---- *** check that below information is actually updated
				# 2014-05-16 09:17:14,092 pplaunch.py        INFO     _report_bacct runtime: 58.0431189537 s (0.967385315895 min)
				# 2014-05-16 09:17:14,092 pplaunch.py        INFO     6865113|Primary_biliary_cirrhosis: jobstatus = DONE. Waiting for
			elif format == 2:
				fh_formatter = logging.Formatter('%(asctime)s %(filename)-18s %(levelname)-8s %(message)s')
				ch_formatter = logging.Formatter('%(levelname)-8s %(message)s')
			elif format == 3:
				fh_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
				ch_formatter = logging.Formatter('%(levelname)-8s %(message)s')

			fh.setFormatter(fh_formatter)
			fh.setLevel(logging.DEBUG)

			ch = logging.StreamHandler()
			#ch = logging.StreamHandler() # default 
			ch.setLevel(logging.INFO)
			ch.setFormatter(ch_formatter)
			# Add handler to the logger
			logger.addHandler(fh)
			logger.addHandler(ch)
		self.logger = logger

	def get(self):
		return self.logger











