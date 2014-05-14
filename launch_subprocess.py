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
			ch.setLevel(logging.INFO)
			#ch.setLevel(logging.WARNING)
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
	
	def __init__(self, cmd, logdir=os.getcwd(), log_root='unknown_root_name', file_output= __name__+'.tmp.log', tag='NoTag'): #file_output=os.path.join(os.getcwd(), __name__+'.tmp.log'
		#self.logger = Logger(self.__class__.__name__).get()
		self.tag = tag
		self.cmd = cmd
		self.logdir = HelperUtils.check_if_writable(logdir)
		self.file_output = file_output
		self.logger = Logger(log_root, logdir).get() #*** find out why .get() is necessary
		#self.file_output = 'LP_' + script_name + '_' + LP.LP_time_stamp + '.txt'
		#self.script_name = script_name

	def run_Log(self):
		#TODO: consider moving the argument file_output= __name__+'.tmp.log' FROM __init__ TO here
		path_output = os.path.join(self.logdir, self.file_output)
		self.fh_output = open(path_output, 'w')
		self.process=subprocess.Popen(self.cmd, stdout=self.fh_output, stderr=subprocess.STDOUT, shell=True)


	def run_Pipe(self):
		self.process=subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


	def run(self):
		self.process=subprocess.Popen(self.cmd, stdout=None, stderr=None, shell=True)

	#def write_pipe_to_file(self):
	#	path_output = os.path.join(self.logdir, self.file_output)
	# for line in p.stdout.readlines():
	#     print line

	def fhandle_pipe(self):
		""" Method only for run_Pipe(). Returns file object that provides output from the child process. """
		self.logger.info( "[PID:%s|Tag:%s]\tparsed STDOUT filehandle" % ( self.process.pid, self.tag ) )
		return self.process.stdout


	def fhandle_check(self):
		if self.fh_output:
			self.logger.info( "[PID:%s|Tag:%s]\tfilehandle is closed: %s" % ( self.process.pid, self.tag, self.fh_output.closed ) )
		else:
			self.logger.warning( "[PID:%s|Tag:%s]\tfilehandle does not exists" % ( self.process.pid, self.tag ) )

	def fhandle_close(self):
		#TODO: only if fh exists
		self.logger.info( "[PID:%s|Tag:%s]\tclosing filehandle" % ( self.process.pid, self.tag ) )
		self.fh_output.close()

	def get_pid(self):
		return self.process.pid

	def process_wait(self):
		self.logger.info( "[PID:%s|Tag:%s]\twaiting for process to finish" % ( self.process.pid, self.tag ) )
		self.process.wait()

	def process_communicate_and_read_pipe_lines(self):
		""" Method only for run_Pipe(). Returns list of lines from output of the child process. """
		self.logger.info( "[PID:%s|Tag:%s]\tcommunicating with process. Then reading lines..." % ( self.process.pid, self.tag ) )
		(stdout, stderr) = self.process.communicate()
		if stderr is not None:
			self.logger.warning( "[PID:%s|Tag:%s]\tSTDERR is not empty (None). Not saving STDERR: %s" % ( self.process.pid, self.tag, stderr ) )
		stdout_lines = stdout.splitlines() # consider keepends=[True]
		self.logger.info( "[PID:%s|Tag:%s]\tRead %d lines..." % ( self.process.pid, self.tag, len(stdout_lines) ) )
		# Returns list of lines WITHOUT NEWLINES
		return stdout_lines

	def process_communicate(self):
		#Note The data read is buffered in memory, so do not use this method if the data size is large or unlimited.
		self.logger.info( "[PID:%s|Tag:%s]\tcommunicating with process" % ( self.process.pid, self.tag ) )
		(stdout, stderr) = self.process.communicate()
		self.logger.debug( "[PID:%s|Tag:%s]\tSTDOUT\n%s" % ( self.process.pid, self.tag, stdout ) )
		self.logger.debug( "[PID:%s|Tag:%s]\tSTDERR\n%s" % ( self.process.pid, self.tag, stderr ) )
		#print stdout
		#print stderr
		return (stdout, stderr)

	def process_check_returncode(self):
		""" This function must be called after [wait, communicate or poll] """
		code = self.process.returncode
		if code != 0:
			self.logger.error("[PID:%s|Tag:%s]\treturned non-zero returncode-code: %s" % ( self.process.pid, self.tag, code) )
		else:
			self.logger.info("[PID:%s|Tag:%s]\treturncode-code OK: %s" % ( self.process.pid, self.tag, code) )
		return code

















