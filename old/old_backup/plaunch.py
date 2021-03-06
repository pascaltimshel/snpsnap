#!/usr/bin/env python2.7


import sys
import glob
import os
import time

import datetime
import re

import subprocess
import logging

import copy

import pdb


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


class LaunchBsub(object):
	LB_job_counter = 0
	LB_job_fails = 0
	def __init__(self, cmd, queue_name, walltime, mem, jobname='NoJobName', projectname='NoProjectName', logdir=os.getcwd(), log_root='unknown_root_name', file_output= __name__+'.tmp.out', no_output=False, email=False): #file_output=os.path.join(os.getcwd(), __name__+'.tmp.log'
		LaunchBsub.LB_job_counter += 1 # Counter the number of jobs
		self.logdir = HelperUtils.check_if_writable(logdir)
		self.logger = Logger(log_root, logdir).get() #*** find out why .get() is necessary
		if no_output:
			self.file_output = '/dev/null'
		else:
			self.file_output = os.path.join(logdir, file_output)
		self.job_number = LaunchBsub.LB_job_counter
		self.jobname = jobname
		self.projectname = projectname
		self.status = ""
		self.attempts = 0

		self.p_queue_name = queue_name # string
		self.p_walltime = walltime # hours		format HOURS | or hh:mm  (hours:minutes)
		self.p_mem = mem #
		#TODO self.mem_per_process ## M --> a per-process (soft) memory limit
		#TODO self.p_cpu ## n (e.g. 2 or 1-4)
		#TODO self.p_n_span
		#TODO -N --> If you use both -o and -N, the output is stored in the output file and the job report is sent by mail.

		self.cmd = cmd
		if email:
			#TODO: consider using -N option to seperate output and report
			self.email = email
			self.bcmd = "bsub -P {project} -J {jobname} -o {output} -r -q {queue} -W {walltime} -R 'rusage[mem={mem}]' -N -u {email}".format(project=self.projectname, jobname=self.jobname,  output=self.file_output, queue=self.p_queue_name, walltime=self.p_walltime, mem=self.p_mem, email=self.email) 
		else:
			self.bcmd = "bsub -P {project} -J {jobname} -o {output} -r -q {queue} -W {walltime} -R 'rusage[mem={mem}]'".format(project=self.projectname, jobname=self.jobname,  output=self.file_output, queue=self.p_queue_name, walltime=self.p_walltime, mem=self.p_mem) 

		self.call = self.bcmd + " " + self.cmd


	def run(self):
		max_calls = 15
		sleep_time = 15 # pause time before making a new call.
		#TODO make sleep_time increse for each attempt.

		pattern = re.compile("<(.*?)>")
		emsg = "" # placeholder for error massage from CalledProcessError exception
		self.logger.info( "#################### JOB NUMBER %d ####################" % self.job_number )
		self.logger.info( "LaunchBsub method call to run(). Jobsubmission call:\n%s" % self.call )

		while self.attempts < max_calls:
			self.attempts += 1
			try:
				self.logger.info( "ATTEMPT #%d/%d| Making jobsubmission call" % (self.attempts, max_calls) )
				out = subprocess.check_output(self.call, shell=True)
			except subprocess.CalledProcessError as e:
				self.logger.warning( "ATTEMPT #%d/%d| *** could not submitting job ***" % (self.attempts, max_calls) )
				self.logger.warning( "ATTEMPT #%d/%d| *** error massage ***\n%s" % (self.attempts, max_calls, e) )
				self.logger.warning( "ATTEMPT #%d/%d| *** Sleeping for %d seconds before re-submitting job ***" % (self.attempts, max_calls, sleep_time) )
				emsg = e
				time.sleep(sleep_time)
				#self.attempts += 1
			else:
				#Job <6747962> is submitted to queue <bhour>
				match = pattern.search(out.strip())
				if match: 
					self.id = match.group(1) # or .groups()[0]
				else:
					self.id = 'fail_in_regex'
					self.logger.error( "ATTEMPT #%d/%d| could not recieve JOBID matching regex" % (self.attempts, max_calls) )
				self.logger.info( "ATTEMPT #%d/%d| JOB SUCCESFULLY SUBMITTED!" % (self.attempts, max_calls) )
				self.logger.info( "ATTEMPT #%d/%d| JOBID IS %s" % (self.attempts, max_calls, self.id) )
				## Disabled writing to "log" file
				# jobs_log_path = "%s/%s" % (self.logdir, self.jobs_log)
				# with open(jobs_log_path, 'a') as QJ_jobs_log:
				#     QJ_jobs_log.write( '%s\n' % self.id )
				
				## return if no exceptions are cought
				return
		# These lines are only executed if attempts <= max_calls
		LaunchBsub.LB_job_fails += 1
		self.logger.error( "ATTEMPT #%d/%d| *** ERROR: Maximum number of attempts reached ****" % (self.attempts, max_calls) )
		
		## Disabled writing to "log" file
		#err_log_path = "%s/%s" % (self.logdir, self.err_log)
		#self.logger.info( "ATTEMPT #%d/%d| *** Reporting this in logfile ***\n%s" % (self.attempts, max_calls, err_log_path) )
		# with open(err_log_path, 'a') as QJ_err_log:
		#     QJ_err_log.write( 'JOB FAIL #%d   Last error message is\n' % LaunchBsub.LB_job_fails )
		#     QJ_err_log.write( '%s \n\n' % emsg )

	@staticmethod
	def _report_bacct(pid, jobname):
		keep = ''
		call = "bacct -l %s" % pid
		try:
			out = subprocess.check_output(call, shell=True)
		except subprocess.CalledProcessError as e:
			emsg = e
			print "call: %s\nerror in report_bacct: %s" % (call, emsg)
		else:
		# Accounting information about this job:
		#      CPU_T     WAIT     TURNAROUND   STATUS     HOG_FACTOR    MEM    SWAP
		#      35.24       31             80     done         0.4404    99M    483M
			lines = out.splitlines()
			#print "called: %s" % call
			#print "got out:\n%s" % out
			for (i, line) in enumerate(lines):
				line = line.strip()
				if 'Accounting information about this job:' in line:
					header = lines[i+1].split()
					values = lines[i+2].split()
					#NB: len(header) must be equal to len(values) for zip() to work?
					combined = map("=".join, zip(header, values)) #List_C = ['{} {}'.format(x,y) for x,y in zip(List_A,List_B)]
					keep = "|".join(combined)
					break
			#cols = keep.split()
		keep = "{pid}|{name}|{status_line}".format(pid=pid, name=jobname, status_line=keep)
		return keep


	@staticmethod
	def report_status(pids): #LB_List_Of_Instances
		sleep_time = 15 # seconds
		incomplete = copy.deepcopy(pids)
		finished = []
		failed = []
		#**TODO: make sure that pids and incomplete is UNIQUE
		#TODO: make sure that len(finished) NEVER becomes larger than len(pids)
		counter = 0
		start_time = time.time()
		while len(finished) < len(pids):
			counter += 1
			elapsed_time = time.time() - start_time
			print "Checking status: #{:d} | Run time = {:.5g} s ({:.3g} min)".format( counter, elapsed_time, elapsed_time/float(60) )
			lines = ['']
			call = "bjobs -aw {jobs}".format( jobs=" ".join(incomplete) ) #consider bjobs -aw
			try:
				out = subprocess.check_output(call, shell=True)
			except subprocess.CalledProcessError as e:
				emsg = e
				print "call: %s\nerror in report_status: %s" % (call, emsg)
			else:
				lines = out.splitlines()[1:] #skipping header
				#print "called: %s" % call
				#print "got out:\n%s" % out
			for line in lines:
				cols = line.strip().split()
				(tmp_pid, tmp_status, tmp_jobname) = (cols[0], cols[2], cols[6])
				#[RUN,EXIT,DONE,PENDING?]
				if tmp_status == 'EXIT':
					print "{pid}|{name}: jobstatus = EXIT".format(pid=tmp_pid, name=tmp_jobname)
					report_line = LaunchBsub._report_bacct(tmp_pid, tmp_jobname)
					incomplete.remove(tmp_pid)
					failed.append(report_line)
					finished.append(report_line)
				elif tmp_status == 'DONE':
					print "{pid}|{name}: jobstatus = DONE".format(pid=tmp_pid, name=tmp_jobname)
					report_line = LaunchBsub._report_bacct(tmp_pid, tmp_jobname)
					incomplete.remove(tmp_pid)
					finished.append(report_line)

			#consider sleeping for some time
			time.sleep(sleep_time)
		# All jobs are NOW somehow finished
		print "########### FINISHED JOBS ##############"
		for job in finished:
			print job
		print "########### FAILED JOBS ##############"
		for job in failed:
			print job



	def check_status(self):
		""" Function to check status of jobs """
		pass

	def get_runtime(self):
		""" Function to retrive runtime of completed job and print it nicely formatted """
		pass


		# ptimshel@copper:~/git/snpsnap> bjobs -aw
		# JOBID   USER    STAT  QUEUE      FROM_HOST   EXEC_HOST   JOB_NAME   SUBMIT_TIME
		# 6728139 ptimshel RUN   interactive copper      node1382    /bin/bash  May 14 15:29
		# 6769527 ptimshel EXIT  bhour      copper      node1695    Hypertension May 14 21:47
		# 6769508 ptimshel EXIT  bhour      copper      node1698    Fasting_glucose-related_traits_interaction_with_BMI May 14 21:47
		# 6769555 ptimshel EXIT  bhour      copper      node1005    Menopause_age_at_onset May 14 21:47
		# 6769571 ptimshel EXIT  bhour      copper      node1337    Myopia_pathological May 14 21:47
		# 6769466 ptimshel EXIT  bhour      copper      node1359    Bone_mineral_density_spine May 14 21:47
		# 6769553 ptimshel EXIT  bhour      copper      node1006    Menarche_age_at_onset May 14 21:47
		# 6769539 ptimshel EXIT  bhour      copper      node1403    Liver_enzyme_levels_gamma-glutamyl_transferase May 14 21:47
		# 6769581 ptimshel EXIT  bhour      copper      node1407    Phospholipid_levels_plasma May 14 21:47
		# 6769512 ptimshel DONE  bhour      copper      node1719    Graves_disease May 14 21:47
		# 6769525 ptimshel DONE  bhour      copper      node1370    Hematological_and_biochemical_traits May 14 21:47
		# 6769505 ptimshel DONE  bhour      copper      node1355    F-cell_distribution May 14 21:47
		# 6769586 ptimshel DONE  bhour      copper      node1372    Primary_biliary_cirrhosis May 14 21:47

		# long gone...
		#6754631 6754629
		#6754630 done

		#6769626 6769629 6769631 6769636

		# Accounting information about this job:
		#      CPU_T     WAIT     TURNAROUND   STATUS     HOG_FACTOR    MEM    SWAP
		#      35.24       31             80     done         0.4404    99M    483M


		# Wed May 14 19:38:20: Dispatched to <node1370>;
		# Wed May 14 19:39:23: Completed <exit>; TERM_RUNLIMIT: job killed after reaching
		#                       LSF run time limit.

		# Accounting information about this job:
		#      CPU_T     WAIT     TURNAROUND   STATUS     HOG_FACTOR    MEM    SWAP
		#      43.94       30             93     exit         0.4724    90M    478M
		# ------------------------------------------------------------------------------

		# SUMMARY:      ( time unit: second )
		#  Total number of done jobs:       0      Total number of exited jobs:     1
		#  Total CPU time consumed:      43.9      Average CPU time consumed:    43.9
		#  Maximum CPU time of a job:    43.9      Minimum CPU time of a job:    43.9
		#  Total wait time in queues:    30.0
		#  Average wait time in queue:   30.0
		#  Maximum wait time in queue:   30.0      Minimum wait time in queue:   30.0
		#  Average turnaround time:        93 (seconds/job)
		#  Maximum turnaround time:        93      Minimum turnaround time:        93
		#  Average hog factor of a job:  0.47 ( cpu time / turnaround time )
		#  Maximum hog factor of a job:  0.47      Minimum hog factor of a job:  0.47




class LaunchSubprocess(object):
	#LP_time_stamp = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S') # date/time string e.g. 2012-12-15_01:21:05
	#LP_logname = 'LP_' + script_name + '_' + LP.LP_time_stamp + '.txt'
	
	def __init__(self, cmd, logdir=os.getcwd(), log_root='unknown_root_name', file_output= __name__+'.tmp.log', jobname='NoJobName'): #file_output=os.path.join(os.getcwd(), __name__+'.tmp.log'
		#self.logger = Logger(self.__class__.__name__).get()
		self.jobname = jobname
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

















