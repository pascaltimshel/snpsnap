##!/usr/bin/env python2.7

import sys
import glob
import os
import time

#import datetime

import subprocess
import logging

import pdb


class Logger(object):
	def __init__(self, script_name, logdir):
		name = '{root}.{child}'.format( root=__name__, child=script_name.replace('.py','') )
		logname = '{name}_{time}.{ext}'.format( name=name, time=gen_timestamp, ext='log' )
		logger = logging.getLogger( name ) # __name__ is the name of the CURRENT module, e.g. launch_process
		#logger = logging.getLogger('%s.%s' % (__name__, name) ) # __name__ is the name of the CURRENT module, e.g. launch_process
		#logger = logging.getLogger(__name__)
		logger.setLevel(logging.DEBUG) #specifies the lowest-severity log message a logger will handle,
		if not logger.handlers:
			#file_name = os.path.join(logdir, '%s.log' % name)
			file_name = os.path.join(logdir, logname)
			fh = logging.FileHandler(file_name)
			formatter = logging.Formatter('%(asctime)s %(levelname)s:%(name)s %(message)s')
			#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s') # try this
			fh.setFormatter(formatter)
			fh.setLevel(logging.DEBUG)

			ch = logging.StreamHandler()
			ch.setLevel(logging.INFO)
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
	    return datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S') # date/time string e.g. 2012-12-15_01:21:05,


class LaunchProcess(object):
    #LP_time_stamp = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S') # date/time string e.g. 2012-12-15_01:21:05
	#LP_logname = 'LP_' + script_name + '_' + LP.LP_time_stamp + '.txt'
	
	def __init__(self, cmd, logdir, logname, script_name='unknown_name'):
		#self.logger = Logger(self.__class__.__name__).get()
		self.cmd = cmd
		self.logdir = check_if_writable(logdir)
		self.logname = logname
		self.logger = Logger(script_name, logdir).get() #*** find out why .get() is necessary
		#self.logname = 'LP_' + script_name + '_' + LP.LP_time_stamp + '.txt'
		#self.script_name = script_name

	def run_Log(self):
		path_log = os.path.join(self.logdir, self.logname)
		self.fhlog = open(path_log, 'w')
		self.process=subprocess.Popen(self.cmd, stdout=self.fhlog, stderr=subprocess.STDOUT, shell=True)


	def run_PipeAndLog():
		pass



def check_fhandles(filehandles):
	for f in filehandles:
		print "f_log closed: %s" % f.closed

def close_fhandles(filehandles):
	for f in filehandles:
		print "closing filehandle..."
		f.close()


def display_pids(jobs):
	print "Displaying %d jobs" % len(jobs)
	for p in jobs:
		print p.pid

def process_wait(jobs):
	print "waiting for all jobs"
	for (n, p) in enumerate(jobs, start=1):
		print "#%d/#%d: waiting for PID %s" % ( n, len(jobs), p.pid )
		p.wait()

def process_communicate(jobs):
	print "communicating with all jobs"
	for (n, p) in enumerate(jobs, start=1):
		print "#%d/#%d: communicating with PID %s" % ( n, len(jobs), p.pid )
		(stdout, stderr) = p.communicate()
		print "HERE IS STDOUT: " + str(stdout)
		print "HERE IS STDERR: " + str(stderr)
		#p.poll()


def check_returncodes(jobs):
	""" This function must be called after [wait, communicate or poll] """
	print "Inspecting returncodes"
	for (n, p) in enumerate(jobs, start=1):
		code = p.returncode
		if code != 0:
			print "**** Warning! **** #%d/#%d: PID %s returned non-zero returncode-code: %s" % ( n, len(jobs), p.pid, code)
			#print "#%d/#%d: returncode for PID %s: %s" % ( n, len(jobs), p.pid, code)


# #jobs = submit()
# (jobs, filehandles) = submit()
# check_fhandles(filehandles)
# display_pids(jobs)
# #process_wait(jobs)
# process_communicate(jobs)
# check_fhandles(filehandles)
# check_returncodes(jobs)

# close_fhandles(filehandles)
# check_fhandles(filehandles)











