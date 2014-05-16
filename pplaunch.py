#!/usr/bin/env python2.7


import sys
import glob
import os
import time

import datetime
import re

import subprocess
import logging
import multiprocessing

from pplogger import Logger
from pphelper import HelperUtils

import copy

import pdb


def report_bacct(pid, jobname):
	keep = ''
	call = "bacct -l %s" % pid
	try:
		out = subprocess.check_output(call, shell=True)
	except subprocess.CalledProcessError as e:
		emsg = e
		print "%s" %e
	else:
		lines = out.splitlines()
		for (i, line) in enumerate(lines):
			line = line.strip()
			if 'Accounting information about this job:' in line:
				header = lines[i+1].split()
				values = lines[i+2].split()
				combined = map("=".join, zip(header, values)) #List_C = ['{} {}'.format(x,y) for x,y in zip(List_A,List_B)]
				keep = "|".join(combined)
				break
	keep = "{pid}|{name}|{status_line}".format(pid=pid, name=jobname, status_line=keep)
	return keep




class LaunchBsub(object):
	LB_job_counter = 0
	LB_job_fails = 0
	def __init__(self, cmd, queue_name, walltime, mem, jobname='NoJobName', projectname='NoProjectName', path_stdout=os.getcwd(), file_output=None, no_output=False, email=False, logger=False): #file_output=os.path.join(os.getcwd(), __name__+'.tmp.log'
		LaunchBsub.LB_job_counter += 1 # Counter the number of jobs
		self.job_number = LaunchBsub.LB_job_counter
		
		self.path_stdout = HelperUtils.check_if_writable(path_stdout)
		if logger: #TODO: check that logger is of class Logger?
			self.logger = logger
		else: # create new logger, with name e.g. LauchBsub_NoLoggerParsed_2014-05-15_23.08.59.log
			self.logger = Logger(self.__class__.__name__+"_NoLoggerParsed", path_stdout).get() #*** find out why .get() is necessary
		
		#OBS: updating variable
		if no_output:
			self.file_output = '/dev/null'
		elif file_output is None:
			self.file_output = "bsub_outfile_ID{job_number}.{ext}".format(job_number=job_number, ext='out')
		else:
			self.file_output = os.path.join(self.path_stdout, file_output)

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
		#TODO: overwrite output files with -oo ?

		self.cmd = cmd
		if email:
			#TODO: consider using -N option to seperate output and report
			self.email = email
			self.bcmd = "bsub -P {project} -J {jobname} -o {output} -r -q {queue} -W {walltime} -R 'rusage[mem={mem}]' -N -u {email}".format(project=self.projectname, jobname=self.jobname,  output=self.file_output, queue=self.p_queue_name, walltime=self.p_walltime, mem=self.p_mem, email=self.email) 
		else:
			self.bcmd = "bsub -P {project} -J {jobname} -o {output} -r -q {queue} -W {walltime} -R 'rusage[mem={mem}]'".format(project=self.projectname, jobname=self.jobname,  output=self.file_output, queue=self.p_queue_name, walltime=self.p_walltime, mem=self.p_mem) 

		self.call = self.bcmd + " " + self.cmd

		# self.logger.critical( "JOB:{} | here is some CRIT information".format(jobname) )
		# self.logger.info( "JOB:{} | here is some INFO information".format(jobname) )
		# self.logger.debug( "JOB:{} | here is some DEBUG information".format(jobname) )


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
		self.logger.critical( "ATTEMPT #%d/%d| *** ERROR: Maximum number of attempts reached. JOB NOT SUBMITTED!!! ****" % (self.attempts, max_calls) )
		
		## Disabled writing to "log" file
		#err_log_path = "%s/%s" % (self.logdir, self.err_log)
		#self.logger.info( "ATTEMPT #%d/%d| *** Reporting this in logfile ***\n%s" % (self.attempts, max_calls, err_log_path) )
		# with open(err_log_path, 'a') as QJ_err_log:
		#     QJ_err_log.write( 'JOB FAIL #%d   Last error message is\n' % LaunchBsub.LB_job_fails )
		#     QJ_err_log.write( '%s \n\n' % emsg )


	@staticmethod
	def _report_bacct(pid, jobname, logger):
		keep = ''
		call = "bacct -l %s" % pid
		try:
			out = subprocess.check_output(call, shell=True)
		except subprocess.CalledProcessError as e:
			emsg = e
			logger.error( "call: %s\nerror in report_bacct: %s" % (call, emsg) )
		else:
		# Accounting information about this job:
		#      CPU_T     WAIT     TURNAROUND   STATUS     HOG_FACTOR    MEM    SWAP
		#      35.24       31             80     done         0.4404    99M    483M
			lines = out.splitlines()
			#logger.info( "called: %s" % call )
			#logger.info( "got out:\n%s" % out )
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
	def report_status(pids, logger): #LB_List_Of_Instances
		sleep_time = 20 # seconds
		incomplete = copy.deepcopy(pids)
		finished = []
		failed = []
		done = []
		#**TODO: make sure that pids and incomplete is UNIQUE
		#TODO: make sure that len(finished) NEVER becomes larger than len(pids)
		counter = 0
		start_time = time.time()
		while len(finished) < len(pids):
			counter += 1
			elapsed_time = time.time() - start_time
			logger.info( "Checking status: #{:d} | Run time = {:.5g} s ({:.3g} min)".format( counter, elapsed_time, elapsed_time/float(60) ) )
			logger.info( "Checking status: #{:d} | Finished={:d}, Incomplete={:d}, Total={:d} [Fails={:d}]".format( counter, len(finished), len(incomplete), len(pids), len(failed) ) )
			lines = ['']
			call = "bjobs -aw {jobs}".format( jobs=" ".join(incomplete) ) #consider bjobs -aw
			try:
				out = subprocess.check_output(call, shell=True)
			except subprocess.CalledProcessError as e:
				emsg = e
				logger.error( "call: %s\nerror in report_status: %s" % (call, emsg) )
			else:
				lines = out.splitlines()[1:] #skipping header
				#logger.info( "called: %s" % call )
				#logger.info( "got out:\n%s" % out )
			for line in lines:
				cols = line.strip().split()
				(tmp_pid, tmp_status, tmp_jobname) = (cols[0], cols[2], cols[6])
				#[RUN,EXIT,DONE,PENDING?]
				if tmp_status == 'EXIT':
					logger.info( "{pid}|{name}: jobstatus = EXIT. Waiting for _report_bacct...".format(pid=tmp_pid, name=tmp_jobname) )
					t1 = time.time()
					report_line = LaunchBsub._report_bacct(tmp_pid, tmp_jobname, logger)
					elapsed_time = time.time() - t1
					logger.info( "_report_bacct runtime: %s s (%s min)" % ( elapsed_time, elapsed_time/float(60) ) )
					incomplete.remove(tmp_pid)
					finished.append(report_line)
					failed.append(report_line)
				elif tmp_status == 'DONE':
					logger.info( "{pid}|{name}: jobstatus = DONE. Waiting for _report_bacct...".format(pid=tmp_pid, name=tmp_jobname) )
					t1 = time.time()
					report_line = LaunchBsub._report_bacct(tmp_pid, tmp_jobname, logger)
					elapsed_time = time.time() - t1
					logger.info( "_report_bacct runtime: %s s (%s min)" % ( elapsed_time, elapsed_time/float(60) ) )
					incomplete.remove(tmp_pid)
					finished.append(report_line)
					done.append(report_line)


			#consider sleeping for some time
			time.sleep(sleep_time)
		# All jobs are NOW somehow finished
		elapsed_time = time.time() - start_time
		logger.info( "Checking status: #{:d} | Run time = {:.5g} s ({:.3g} min)".format( counter, elapsed_time, elapsed_time/float(60) ) )
		logger.info( "LAST Checking status DONE: #{:d} | Run time = {:.5g} s ({:.3g} min)".format( counter, elapsed_time, elapsed_time/float(60) ) )
		logger.info( "LAST Checking status DONE: #{:d} | Finished={:d}, Incomplete={:d}, Total={:d} [Fails={:d}]".format( counter, len(finished), len(incomplete), len(pids), len(failed) ) )
		logger.info( "########### ALL JOBS - %d ##############" % len(finished) )
		for job in finished:
			logger.info(job)
		logger.info( "########### SUCESSFUL DONE JOBS - %d ##############" % len(done) )
		if done:
			for job in done: logger.critical(job)
		else:
			logger.critical("No jobs to list")
		logger.critical( "########### FAILED JOBS - %d ##############" % len(failed) )
		if failed:
			for job in failed: logger.critical(job)
		else:
			logger.critical("No jobs to list")


	@staticmethod
	def report_status_multiprocess(pids, logger): #LB_List_Of_Instances
		sleep_time = 20 # seconds
		incomplete = copy.deepcopy(pids)
		finished = [] # all jobs that are not runninng or pending - jobs that are either "exit" or "done"
		failed = [] # exit status
		done = [] # done status
		#**TODO: make sure that pids and incomplete is UNIQUE
		#TODO: make sure that len(finished) NEVER becomes larger than len(pids)
		counter = 0
		start_time = time.time()
		while len(finished) < len(pids):
			counter += 1
			elapsed_time = time.time() - start_time
			logger.info( "Checking status: #{:d} | Run time = {:.5g} s ({:.3g} min)".format( counter, elapsed_time, elapsed_time/float(60) ) )
			logger.info( "Checking status: #{:d} | Finished={:d}, Incomplete={:d}, Total={:d} [Fails={:d}]".format( counter, len(finished), len(incomplete), len(pids), len(failed) ) )
			lines = ['']
			call = "bjobs -aw {jobs}".format( jobs=" ".join(incomplete) ) #consider bjobs -aw
			try:
				out = subprocess.check_output(call, shell=True)
			except subprocess.CalledProcessError as e:
				emsg = e
				logger.error( "call: %s\nerror in report_status: %s" % (call, emsg) )
			else:
				lines = out.splitlines()[1:] #skipping header
				#logger.info( "called: %s" % call )
				#logger.info( "got out:\n%s" % out )
			pids2check = []
			for line in lines:
				cols = line.strip().split()
				(tmp_pid, tmp_status, tmp_jobname) = (cols[0], cols[2], cols[6])
				#[RUN,EXIT,DONE,PENDING?]
				#batch_size = 10
				if tmp_status == 'EXIT':
					logger.info( "{pid}|{name}: jobstatus = EXIT".format(pid=tmp_pid, name=tmp_jobname) )
					#report_line = LaunchBsub._report_bacct(tmp_pid, tmp_jobname, logger)
					pids2check.append( (tmp_pid, tmp_jobname, logger) ) # append 3 element tuple
					incomplete.remove(tmp_pid)
					report_line = '{pid}|{name}'.format(pid=tmp_pid, name=tmp_jobname)
					failed.append(report_line)
					#finished.append(report_line)
				elif tmp_status == 'DONE':
					logger.info( "{pid}|{name}: jobstatus = DONE".format(pid=tmp_pid, name=tmp_jobname) )
					#report_line = LaunchBsub._report_bacct(tmp_pid, tmp_jobname, logger)
					pids2check.append( (tmp_pid, tmp_jobname, logger) ) # append 3 element tuple
					incomplete.remove(tmp_pid)
					report_line = '{pid}|{name}'.format(pid=tmp_pid, name=tmp_jobname)
					done.append(report_line)
					#finished.append(report_line)
			logger.info( "Got %d pids2check." % len(pids2check) )
			if pids2check:
				n_processes = len(pids2check)
				t1 = time.time()
				pool = multiprocessing.Pool(n_processes)
				elapsed_time = time.time() - t1
				logger.info( "Making multiprocessing pool. Time to load pool: %s s (%s min)" % ( elapsed_time, elapsed_time/float(60) ) )
				t1 = time.time()
				for i in range(n_processes):
					#apply_async(func[, args[, kwds[, callback]]])
					(tmp_pid, tmp_jobname, logger) = pids2check[i]
					#pdb.set_trace()
					#logger.info( "i is %d" % ( i ) )
					pool.apply_async(report_bacct, args=(tmp_pid, tmp_jobname), callback=finished.append)
				pool.close()
				pool.join()
				elapsed_time = time.time() - t1
				logger.info( "Time to run join() pool: %s s (%s min)" % ( elapsed_time, elapsed_time/float(60) ) )

			#consider sleeping for some time
			time.sleep(sleep_time)
		# All jobs are NOW somehow finished
		elapsed_time = time.time() - start_time
		logger.info( "LAST Checking status DONE: #{:d} | Run time = {:.5g} s ({:.3g} min)".format( counter, elapsed_time, elapsed_time/float(60) ) )
		logger.info( "LAST Checking status DONE: #{:d} | Finished={:d}, Incomplete={:d}, Total={:d} [Fails={:d}]".format( counter, len(finished), len(incomplete), len(pids), len(failed) ) )
		logger.info( "########### ALL JOBS - %d ##############" % len(finished) )
		for job in finished:
			logger.info(job)
		logger.info( "########### SUCESSFUL DONE JOBS - %d ##############" % len(done) )
		if done:
			for job in done: logger.critical(job)
		else:
			logger.critical("No jobs to list")
		logger.critical( "########### FAILED JOBS - %d ##############" % len(failed) )
		if failed:
			for job in failed: logger.critical(job)
		else:
			logger.critical("No jobs to list")


#6840302 6840303 6840304 6840306 6840307 6840309 6840310 6840312 6840313 6840315

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

















