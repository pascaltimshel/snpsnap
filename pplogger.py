#!/usr/bin/env python2.7


import sys
import os
import logging

import pphelper
#from pphelper import HelperUtils

#import pdb


class Logger(object):
	""" The intended use of this class is the following call:
	current_script_name = os.path.basename(__file__).replace('.py','')
	logger = Logger(name=current_script_name, log_dir=outputdir, log_format=1, enabled=True).get() """
	def __init__(self, name='NoLogNameParsed', log_dir=os.getcwd(), log_format=1, enabled=True):
		self.name = "myroot.%s" % name
		self.log_dir = log_dir
		self.log_format = log_format
		self.enabled = enabled

		if self.enabled:
			self.logger = self.setup_logger()
		else: 
			self.logger = self.setup_null_handler()

		# Call class method to log an 'instantiation of the log'. NB: nothing will happen (be logged) if enable=False
		self.log_mark_of_initiation()

		#TODO: implement a optional log_note. Like
		#logger.info( "INSTANTIATION NOTE: placeholder" )


	def setup_logger(self):
		## WE GET the logger
		logger = logging.getLogger( self.name ) # __name__ is the name of the CURRENT module, e.g. launch_process or "main"
		#logger = logging.getLogger('%s.%s' % (__name__, name) ) # __name__ is the name of the CURRENT module, e.g. launch_process
		#logger = logging.getLogger(__name__)

		# Set logging level - this can be changed/overwritten later by the module importing Logger()
		logger.setLevel(logging.DEBUG) #specifies the lowest-severity log message a logger will handle

		################## Setting log file name ##################
		# ## USE THIS to create a log file name with a TIME STAMP (READ: file_log is not the same as logger)
		# ## However, since the logging handlers (file handle, formatting etc.) are only setup ONCE for the class several instantiations of the class will NOT create different log files (file_log)
		# ## This will effectively mean that each call to a given python script (start of interpreter) will have its OWN log file (because the time stamp will never be the same)
		# ## Remember that ultimately it is the NAME in "logging.getLogger( "myroot.%s" % name )" that determines what logger (and thus filehandle) to use for the class instance.
		# file_log = '{name}_{time}.{ext}'.format( name=name, time=pphelper.HelperUtils.gen_timestamp(), ext='log' )
		
		## USE THIS to create ONE log file that is appended to.
		## The file_log is appended to as long as the Logger() class is called with the same 'name'
		self.file_log = '{name}.{ext}'.format( name=self.name, ext='log' )
		#########################################

		## only run all this setup if no previous logger has been configured
		if not logger.handlers:
			self.file_name = os.path.join(self.log_dir, self.file_log) # OBS setting instance variable

			fh = logging.FileHandler(self.file_name)

			if self.log_format == 0:
				fh_formatter = logging.Formatter('%(message)s')
				ch_formatter = logging.Formatter('%(message)s')
			elif self.log_format == 1: 
				#1) fields are TAB SEPERATED
				#2) asctime is without miliseconds
				fh_formatter = logging.Formatter('%(asctime)s	%(levelname)s	%(message)s', '%Y-%m-%d %H:%M:%S')
				ch_formatter = logging.Formatter('%(message)s')
			elif self.log_format == 2: #these fields are TAB SEPERATED
				fh_formatter = logging.Formatter('%(asctime)s	%(filename)s	%(levelname)s	%(message)s')
				ch_formatter = logging.Formatter('%(levelname)s	%(message)s')
			elif self.log_format == 3:
				fh_formatter = logging.Formatter('%(asctime)s %(filename)-18s %(levelname)-8s %(message)s')
				ch_formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
				# file format (fh_formatter) gives ---- *** check that below information is actually updated
				# 2014-05-16 09:17:14,092 pplaunch.py        INFO     _report_bacct runtime: 58.0431189537 s (0.967385315895 min)
				# 2014-05-16 09:17:14,092 pplaunch.py        INFO     6865113|Primary_biliary_cirrhosis: jobstatus = DONE. Waiting for
			elif self.log_format == 4:
				fh_formatter = logging.Formatter('%(asctime)s %(filename)-18s %(levelname)-8s %(message)s')
				ch_formatter = logging.Formatter('%(levelname)-8s %(message)s')
			elif self.log_format == 5:
				fh_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
				ch_formatter = logging.Formatter('%(levelname)-8s %(message)s')
			else: # if 'wrong' log_format is given then 'fallback' on this formatter
				fh_formatter = logging.Formatter('%(asctime)s	%(levelname)s	%(message)s', '%Y-%m-%d %H:%M:%S')
				ch_formatter = logging.Formatter('%(message)s')


			fh.setFormatter(fh_formatter)
			fh.setLevel(logging.DEBUG)

			ch = logging.StreamHandler()
			#ch = logging.StreamHandler() # default 
			ch.setLevel(logging.INFO)
			ch.setFormatter(ch_formatter)
			# Add handler to the logger
			logger.addHandler(fh)
			logger.addHandler(ch)
		
		return logger

	def setup_null_handler(self):
		#logger = logging.getLogger() # get root logger - does not matter?
		logger = logging.getLogger( self.name )
		noop = logging.NullHandler()
		logger.addHandler(noop)
		return logger


	## If the logging handles are setup correctly for the Exceptions are written to the log AND printed to sys.stderr
	## An alternative solution is to make one big "try except" block in main:
	# @staticmethod
	# def handleException(excType, excValue, traceback, logger=logger):
	# 	""" This function intended use is to 'redirect' expections from sys.excepthook to this function.
	# 	sys.excepthook(type, value, traceback) is called whenever an exception is raised and uncaught.
	# 	By default sys.excepthook prints the traceback to sys.stderr.
	# 	Here we exploit the logging modules exc_info to nicely log the traceback
	# 	OBS: only redirect tracebacks to this function if the logger has a StreamHandler - that is, prints to the console. If not, the exception will not be printed!"""
		
	# 	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
	

	def log_mark_of_initiation(self):
		initiation_string = "########################## Initiated Logger() instance - {time} ##########################".format( time=pphelper.HelperUtils.gen_timestamp() )
		self.logger.critical( initiation_string )


	def get(self):
		return self.logger










