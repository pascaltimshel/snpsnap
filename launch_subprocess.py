#!/usr/bin/env python2.7

import sys
import glob
import os
import time

import datetime

import subprocess
import logging

import pdb


# class Logger(object):
# 	def __init__(self, script_name, logdir):
# 		name = '{root}.{child}'.format( root=__name__, child=script_name.replace('.py','') )
# 		logname = '{name}_{time}.{ext}'.format( name=name, time=HelperUtils.gen_timestamp(), ext='log' )
# 		logger = logging.getLogger( name ) # __name__ is the name of the CURRENT module, e.g. launch_process
# 		#logger = logging.getLogger('%s.%s' % (__name__, name) ) # __name__ is the name of the CURRENT module, e.g. launch_process
# 		#logger = logging.getLogger(__name__)
# 		logger.setLevel(logging.DEBUG) #specifies the lowest-severity log message a logger will handle,
# 		if not logger.handlers:
# 			#file_name = os.path.join(logdir, '%s.log' % name)
# 			file_name = os.path.join(logdir, logname)
# 			fh = logging.FileHandler(file_name)
# 			formatter = logging.Formatter('%(asctime)s %(filename)-18s %(levelname)-8s: %(message)s')
# 			#formatter = logging.Formatter('%(asctime)s %(levelname)s:%(name)s %(message)s')
# 			#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s') # try this
# 			fh.setFormatter(formatter)
# 			fh.setLevel(logging.DEBUG)

# 			ch = logging.StreamHandler()
# 			ch.setLevel(logging.INFO)
# 			formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# 			ch.setFormatter(formatter)
# 			# Add handler to the logger
# 			logger.addHandler(fh)
# 			logger.addHandler(ch)
# 		self.logger = logger

# 	def get(self):
# 		return self.logger

class Logger(object):
	def __init__(self, log_root, logdir):
		name = '{root}.{child}'.format( root=log_root, child=__name__ )
		file_log = '{name}_{time}.{ext}'.format( name=name, time=HelperUtils.gen_timestamp(), ext='log' )
		logger = logging.getLogger( name ) # __name__ is the name of the CURRENT module, e.g. launch_process
		#logger = logging.getLogger('%s.%s' % (__name__, name) ) # __name__ is the name of the CURRENT module, e.g. launch_process
		#logger = logging.getLogger(__name__)
		logger.setLevel(logging.DEBUG) #specifies the lowest-severity log message a logger will handle,
		if not logger.handlers:
			#file_name = os.path.join(logdir, '%s.log' % name)
			file_name = os.path.join(logdir, file_log)
			fh = logging.FileHandler(file_name)
			formatter = logging.Formatter('%(asctime)s %(filename)-18s %(levelname)-8s %(message)s')
			#formatter = logging.Formatter('%(asctime)s %(levelname)s:%(name)s %(message)s')
			#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s') # try this
			fh.setFormatter(formatter)
			fh.setLevel(logging.DEBUG)

			ch = logging.StreamHandler()
			#ch.setLevel(logging.INFO)
			ch.setLevel(logging.WARNING)
			formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
			ch.setFormatter(formatter)
			# Add handler to the logger
			logger.addHandler(fh)
			logger.addHandler(ch)
		self.logger = logger

	def get(self):
		return self.logger



class HelperUtils(object):
	@staticmethod
	def mkdirs(file_path):
		if not os.path.exists(file_path):
		    os.makedirs(file_path)

	@staticmethod
	def check_if_writable(file_path):
	    if not os.access(file_path, os.W_OK):
	        msg="File path: %s is not writable" % file_path
	        raise Exception(msg)
	    else:
	        return os.path.abspath(file_path)
	
	@staticmethod
	def gen_timestamp():
	    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S') # date/time string e.g. 2012-12-15_01:21:05,


class LaunchSubprocess(object):
    #LP_time_stamp = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S') # date/time string e.g. 2012-12-15_01:21:05
	#LP_logname = 'LP_' + script_name + '_' + LP.LP_time_stamp + '.txt'
	
	def __init__(self, cmd, logdir, log_root='unknown_root_name', file_output=os.path.join(os.getcwd(), __name__+'.tmp.log'), tag='NoTag'):
		#self.logger = Logger(self.__class__.__name__).get()
		self.tag = tag
		self.cmd = cmd
		self.logdir = HelperUtils.check_if_writable(logdir)
		self.file_output = file_output
		self.logger = Logger(log_root, logdir).get() #*** find out why .get() is necessary
		#self.file_output = 'LP_' + script_name + '_' + LP.LP_time_stamp + '.txt'
		#self.script_name = script_name

	def run_Log(self):
		path_output = os.path.join(self.logdir, self.file_output)
		self.fh_output = open(path_output, 'w')
		self.process=subprocess.Popen(self.cmd, stdout=self.fh_output, stderr=subprocess.STDOUT, shell=True)


	def run_PipeAndLog():
		pass


	def check_fhandles(self):
		if self.fh_output:
			self.logger.info( "[PID %s, Tag %s] filehandle is closed: %s" % ( self.process.pid, self.tag, self.fh_output.closed ) )
			self.logger.error("this is an error msg")
		else:
			self.logger.warning( "[PID %s, Tag %s] filehandle does not exists" % ( self.process.pid, self.tag ) )

	def close_fhandles(filehandles):
		for f in filehandles:
			self.logger.info("closing filehandle...")
			f.close()


	def display_pids(jobs):
		self.logger.info("Displaying %d jobs" % len(jobs))
		for p in jobs:
			self.logger.info(p.pid)

	def process_wait(jobs):
		self.logger.info("waiting for all jobs")
		for (n, p) in enumerate(jobs, start=1):
			self.logger.info("#%d/#%d: waiting for PID %s" % ( n, len(jobs), p.pid ))
			p.wait()

	def process_communicate(jobs):
		self.logger.info("communicating with all jobs")
		for (n, p) in enumerate(jobs, start=1):
			self.logger.info("#%d/#%d: communicating with PID %s" % ( n, len(jobs), p.pid ))
			(stdout, stderr) = p.communicate()
			self.logger.info("HERE IS STDOUT: " + str(stdout))
			self.logger.info("HERE IS STDERR: " + str(stderr))
			#p.poll()


	def check_returncodes(jobs):
		""" This function must be called after [wait, communicate or poll] """
		self.logger.info("Inspecting returncodes")
		for (n, p) in enumerate(jobs, start=1):
			code = p.returncode
			if code != 0:
				self.logger.info("**** Warning! **** #%d/#%d: PID %s returned non-zero returncode-code: %s" % ( n, len(jobs), p.pid, code))
				#print "#%d/#%d: returncode for PID %s: %s" % ( n, len(jobs), p.pid, code)


















