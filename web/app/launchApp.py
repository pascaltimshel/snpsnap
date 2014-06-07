#!/usr/bin/python

#!/opt/rh/python27/root/usr/bin/python2.7
#!/opt/rh/python27/root/usr/bin/python

#!/usr/bin/python

#!/usr/bin/env python2.7
#!/usr/bin/env python




import os
import time # potential

import subprocess

#import pandas



class LaunchSubprocess(object):
	#LP_time_stamp = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S') # date/time string e.g. 2012-12-15_01:21:05
	#LP_logname = 'LP_' + script_name + '_' + LP.LP_time_stamp + '.txt'
	
	def __init__(self, cmd, path_stdout=os.getcwd(), logger=False, jobname='NoJobName'): #file_output=os.path.join(os.getcwd(), __name__+'.tmp.log'
		self.path_stdout = HelperUtils.check_if_writable(path_stdout)
		if logger: #TODO: check that logger is of class Logger?
			self.logger = logger
		else: # create new logger, with name e.g. LaunchSubprocess_NoLoggerParsed_2014-05-15_23.08.59.log
			self.logger = Logger(self.__class__.__name__+"_NoLoggerParsed", path_stdout).get() #*** find out why .get() is necessary
		
		self.jobname = jobname
		self.cmd = cmd


	def run_Log(self, file_output):
		""" Potentially call this function right after instantiation. In this way you will have the file_output 'ready' """
		self.file_output = os.path.join(self.path_stdout, file_output)
		self.fh_output = open(self.file_output, 'w')
		self.process=subprocess.Popen(self.cmd, stdout=self.fh_output, stderr=subprocess.STDOUT, shell=True)


	def run_Pipe(self):
		self.process=subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


	def run(self):
		""" This function should just run the process. 'No questions asked' """
		#TODO: finish writing this method
		self.process=subprocess.Popen(self.cmd, stdout=None, stderr=None, shell=True)

	#def write_pipe_to_file(self):
	#	path_output = os.path.join(self.logdir, self.file_output)
	# for line in p.stdout.readlines():
	#     print line

	def fhandle_pipe(self):
		""" Method only for run_Pipe(). Returns file object that provides output from the child process. """
		self.logger.info( "[PID:%s|jobname:%s]\tparsed STDOUT filehandle" % ( self.process.pid, self.jobname ) )
		return self.process.stdout


	def fhandle_check(self):
		if self.fh_output:
			self.logger.info( "[PID:%s|jobname:%s]\tfilehandle is closed: %s" % ( self.process.pid, self.jobname, self.fh_output.closed ) )
		else:
			self.logger.warning( "[PID:%s|jobname:%s]\tfilehandle does not exists" % ( self.process.pid, self.jobname ) )

	def fhandle_close(self):
		#TODO: only if fh exists
		self.logger.info( "[PID:%s|jobname:%s]\tclosing filehandle" % ( self.process.pid, self.jobname ) )
		self.fh_output.close()

	def get_pid(self):
		return self.process.pid

	def process_wait(self):
		self.logger.info( "[PID:%s|jobname:%s]\twaiting for process to finish" % ( self.process.pid, self.jobname ) )
		self.process.wait()

	def process_communicate_and_read_pipe_lines(self):
		""" Method only for run_Pipe(). Returns list of lines from output of the child process. """
		self.logger.info( "[PID:%s|jobname:%s]\tcommunicating with process. Then reading lines..." % ( self.process.pid, self.jobname ) )
		(stdout, stderr) = self.process.communicate()
		if stderr is not None:
			self.logger.warning( "[PID:%s|jobname:%s]\tSTDERR is not empty (None). Not saving STDERR: %s" % ( self.process.pid, self.jobname, stderr ) )
		stdout_lines = stdout.splitlines() # consider keepends=[True]
		self.logger.info( "[PID:%s|jobname:%s]\tRead %d lines..." % ( self.process.pid, self.jobname, len(stdout_lines) ) )
		# Returns list of lines WITHOUT NEWLINES
		return stdout_lines

	def process_communicate(self):
		#Note The data read is buffered in memory, so do not use this method if the data size is large or unlimited.
		self.logger.info( "[PID:%s|jobname:%s]\tcommunicating with process" % ( self.process.pid, self.jobname ) )
		(stdout, stderr) = self.process.communicate()
		self.logger.debug( "[PID:%s|jobname:%s]\tSTDOUT\n%s" % ( self.process.pid, self.jobname, stdout ) )
		self.logger.debug( "[PID:%s|jobname:%s]\tSTDERR\n%s" % ( self.process.pid, self.jobname, stderr ) )
		#print stdout
		#print stderr
		return (stdout, stderr)

	def process_check_returncode(self):
		""" This function must be called after [wait, communicate or poll] """
		code = self.process.returncode
		if code != 0:
			self.logger.error("[PID:%s|jobname:%s]\treturned non-zero returncode-code: %s" % ( self.process.pid, self.jobname, code) )
		else:
			self.logger.info("[PID:%s|jobname:%s]\treturncode-code OK: %s" % ( self.process.pid, self.jobname, code) )
		return code





