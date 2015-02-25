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
	pattern_accounting_info = re.compile(r"CPU_T\s+WAIT\s+TURNAROUND\s+STATUS\s+HOG_FACTOR\s+MEM\s+SWAP", flags=re.IGNORECASE)
	keep = 'no_regex_match_found:check_src_code'
	call = "bacct -l %s" % pid
	try:
		out = subprocess.check_output(call, shell=True)
	except subprocess.CalledProcessError as e:
		emsg = e
		print "%s" % e 	### TODO: change this to a log statement! (requires parsing of a logger).
						### BUT BE CAREFUL: it may not work because the arguments MUST be pickable
	else:
	# Accounting information about this job:
	#      CPU_T     WAIT     TURNAROUND   STATUS     HOG_FACTOR    MEM    SWAP
	#      35.24       31             80     done         0.4404    99M    483M

	# If queue='priority' is used then an extra line is possibly added:
	# Accounting information about this job:
	#      Share group charged </ptimshel>
	#      CPU_T     WAIT     TURNAROUND   STATUS     HOG_FACTOR    MEM    SWAP
	#   27089.57     4288          30632     done         0.8844   189M    576M
		lines = out.splitlines()
		for (i, line) in enumerate(lines):
			line = line.strip()
			match = pattern_accounting_info.search(line)
			if match:
				header = lines[i].split()
				values = lines[i+1].split()
				combined = map("=".join, zip(header, values)) #List_C = ['{} {}'.format(x,y) for x,y in zip(List_A,List_B)]
				keep = "|".join(combined)
				break
	keep = "{pid}|{name}|{status_line}".format(pid=pid, name=jobname, status_line=keep)
	return keep


### TODO - improvements:
#1) Add each instance of LaunchBsub to a class variable list.
#2) Add class method 'print_processes' to print the PID of the class
#3) 'Unit test': make 'test method' that submits a 'echo and sleep' job


class LaunchBsub(object):
	"""
	DOCUMENTATION

	About output:
		The output of the job is NEVER sent by email because the -o {output} is allways given.
		LaunchBsub ONLY uses the -o {output} option, meaning that the standard error of the job is stored in the output file.

	Dotkit inheritance:
		LaunchBsub does not issue any dotkit commands (e.g reuse -q Python-2.7) so the SHELL calling LaunchBsub is responsible for having loaded the correct dotkits
		The dotkits from the calling shell SHOULD be inherited to the bsub command.
		*** Disclaimer #1: using a TMUX session may conflict with this so check 'echo $PATH' before you submit the jobs.
		*** Disclaimer #2: the bsub command is called as a subprocess.Popen(..., shell=True) which hopefully inherits the dotkit
		See more on https://it.broadinstitute.org/wiki/Dotkit

	- path_stdout:
		- sets the PATH for the stdout/stderr (output file) from bsub. (this path is also used for the logger if no logger is given)
		- DEFAULT: os.getcwd()
	- file_output:
		- sets the FILENAME of the stdout/stderr (output file) from bsub.
		- RECOMMENDATION: leave this input BLANK. LaunchBsub will set a sensable filename like 'bsub_outfile_IDXX_jobnameYY.out'
		- DEFAULT: 'bsub_outfile_IDXX_jobnameYY.out'
	- no_output: 
		- if this value is set to true, then the stdout and stderr is written to /dev/null.
	- email: 
		- parse an email address to this argument. The user MUST set email_status_notification or email_report to 'True' for any email to be sent
		- DEFAULT: None
		- Example: email='pascal.timshel@gmail.com'
		* email_status_notification:
			if enabled, you will receive email notification when the job starts/stops. 
		* email_report:
			if enabled, the JOB REPORT is sent by email and NOT written to the stdout file.
	- logger:
		- if no logger (a object of the class 'Logging') is parsed, then LaunchBsub creates a log file in path_stdout (os.getcwd by default) with a name like 'LauchBsub_NoLoggerParsed_2014-05-15_23.08.59.log' (notice that LauchBsub sets the timestamp itself)
	- cmd_custom:
		- if any true value (in a boolean context) is given then the cmd_custom COMPLETELY overwrites the other settings
		- RECOMMENDATION: when using cmd_custom, instantiate the LaunchBsub object with 'None' in ALL other arguments

	## Queues
	- queue_name
	- app:
		application profile
		string. 
		shortjobs [max runtime = 15.0 min]
		supershortjobs [max runtime = 1 min] 
		HINT: "bapp -l" will list the application profiles available
	
	## RESOURCES
	- proc: ["min_proc"] or ["min_proc,max_proc"]
		min_proc[,max_proc].
		parallel job and specifies the number of processors required to run the job
		this sets the $LSB_DJOB_NUMPROC
		EXAMPLE:
			"2"		: two processes/slots/CPUs
			"2,4"	: between two and four processes/slots/CPUs
	- mem: memory reserved (for the whole job) in GB
		sets -R "rusage[mem=mem]"
	- runlimit: [hh:mm] string OR [mm] string
		-W [hour:]minute
		Set the wall-clock run time limit of this batch job. RUNLIMIT==WALLTIME.
		the maximum time the job can have the status "running". This is a HARD LIMIT
		EXAMPLE:
			"3:30"	a run_limit of 3 and a half hours.
			"210"	a run_limit of 3 and a half hours.
	- shared_mem: OWN flag
		sets -R 'span[hosts=1]'
		use this for multithreaded SMP jobs: You always want to use this with SMP jobs!

	## LSF INFO
	lsinfo
	bsub -V
	bsub -h
	lsid -V ---> Platform LSF 7.0.6.134609, Sep 04 2009

	## Monitoring jobs:
	/seq/annotation/bio_tools/OBA/GridSubmissions/bjobss
	watch -n 10 bjobs

	## LINK collection
	SMP/MPI on LSF: http://wiki.gwdg.de/index.php/Running_Jobs#bsub_options_for_parallel_.28SMP_or_MPI.29_jobs
	BROAD lsf7.0.5: https://iwww.broadinstitute.org/itsystems/softwaredocs/lsf7.0.5/lsf_command_ref/index.htm
	BROAD lsf7.0.6: https://iwww.broadinstitute.org/itsystems/softwaredocs/lsf7.0.6/



	"""
	LB_job_counter = 0
	LB_job_fails = 0
	def __init__(self, cmd, queue_name, mem, proc=None, shared_mem=None, runlimit=None, app=None, jobname='NoJobName', projectname='NoProjectName', path_stdout=os.getcwd(), file_output=None, no_output=False, email=None, email_status_notification=False, email_report=False, logger=False, cmd_custom=None): #file_output=os.path.join(os.getcwd(), __name__+'.tmp.log'
		LaunchBsub.LB_job_counter += 1 # Counter the number of jobs
		self.job_number = LaunchBsub.LB_job_counter
		
		self.path_stdout = HelperUtils.check_if_writable(path_stdout)
		if logger: #TODO: check that logger is of class Logger?
			self.logger = logger
		else: # create new logger, with name e.g. LauchBsub_NoLoggerParsed_2014-05-15_23.08.59.log
			self.logger = Logger(name=self.__class__.__name__+"_NoLoggerParsed"+HelperUtils.gen_timestamp(), log_dir=path_stdout, log_format=1, enabled=True).get()
		#OBS: updating variable
		if no_output:
			self.file_output = '/dev/null'
		elif file_output is None:
			file_output = "bsub_outfile_ID{job_number}_{jobname}.{ext}".format(job_number=self.job_number, jobname=jobname, ext='out')
			self.file_output = os.path.join(self.path_stdout, file_output) # OBS: overwriting variable. Change this!
		else:
			self.file_output = os.path.join(self.path_stdout, file_output) # OBS: overwriting variable. Change this!

		self.jobname = jobname
		self.projectname = projectname
		self.status = ""
		self.attempts = 0
		#TODO: overwrite output files with -oo ?

		#TODO self.mem_per_process ## M --> a per-process (soft) memory limit
		#TODO: span[ptile=value]
			#Indicates the number of processors on each host that should be allocated to the job, where value is one of the following:
			#-R span[ptile=<x>]
			# x denotes the exact number of job slots to be used on each host. If the total process number is not divisible by x, the residual processes will be put on one host.
			#**DOES THIS OPTION EXISTS ON THE BROAD LSF 7.0.6?
		#TODO: "-w" option to bsub to set up the dependencies 
		#TODO: I/O resource requests --> bsub -R "rusage[indium_io=3]" ...
			## "df -k ." --> gets the file
			## /broad/tools/scripts/io_resource_for_file . -->
		#TODO: BSUB -x - request exclusive access to the nodes


		self.p_queue_name = queue_name # string
		self.p_mem = mem # in GB
		self.p_proc = proc 
		self.p_runlimit = runlimit 
		self.p_shared_mem = shared_mem # boolean value. 
		self.p_app = app 


		self.cmd = cmd # this is the command/program to run. THIS IS APPENDED TO the bsub command
		self.bcmd = "bsub -P {project} -J {jobname} -o {output} -r -q {queue} -R 'rusage[mem={mem}]'".format(project=self.projectname, jobname=self.jobname,  output=self.file_output, queue=self.p_queue_name, mem=self.p_mem) 
		
		if self.p_shared_mem:
			#TODO: figure out how the 'multiple -R options' works --> ANSWER: bsub accepts multiple -R options for the select section in simple resource requirements.
			#http://www-01.ibm.com/support/docview.wss?uid=isg3T1013512
			#http://www.ccs.miami.edu/hpc/lsf/7.0.6/admin/resrequirements.html
			#ALTERNATIVE: -R "rusage[mem=128000]  span[hosts=1]" 
			addon = "-R 'span[hosts=1]'" # OBS: remember the QUOTES!
			self.bcmd = "{base} {addon}".format(base=self.bcmd, addon=addon)

		if self.p_proc:
			addon = "-n {}".format(self.p_proc)
			self.bcmd = "{base} {addon}".format(base=self.bcmd, addon=addon)

		if self.p_runlimit:
			addon = "-W {}".format(self.p_runlimit) 
			self.bcmd = "{base} {addon}".format(base=self.bcmd, addon=addon)

		if self.p_app:
			addon = "-app {}".format(self.p_app)
			self.bcmd = "{base} {addon}".format(base=self.bcmd, addon=addon)

		if email:
			# *Question: can I get the report in both an email and the stdout file? ANSWER ---> NO!
			addon = "-u {}".format(email) 
			self.bcmd = "{base} {addon}".format(base=self.bcmd, addon=addon)
		if email_status_notification: # -B
			# -B: Sends email to the job submitter when the job is dispatched and begins running
			addon = "-B"
			self.bcmd = "{base} {addon}".format(base=self.bcmd, addon=addon)
		if email_report: # -N
			# -N: If you want to separate the job report information from the job output, use the -N option to specify that the job report information should be sent by email.
			addon = "-N"
			self.bcmd = "{base} {addon}".format(base=self.bcmd, addon=addon)



		### GENERATING CALL
		self.call = ''
		if not cmd_custom:
			self.call = self.bcmd + " " + self.cmd
		else:
			self.logger.warning( "OBS: custom command parsed to LaunchBsub(). The command is: %s" % cmd_custom )
			self.call = cmd_custom

		# self.logger.critical( "JOB:{} | here is some CRIT information".format(jobname) )
		# self.logger.info( "JOB:{} | here is some INFO information".format(jobname) )
		# self.logger.debug( "JOB:{} | here is some DEBUG information".format(jobname) )




	def run(self):
		max_calls = 15
		sleep_time = 15 # if ERROR occurs, pause time before making a new call
		#TODO make sleep_time increse for each attempt.

		pattern = re.compile("<(.*?)>")
		emsg = "" # placeholder for error massage from CalledProcessError exception
		self.logger.info( "#################### JOB NUMBER %s ####################" % self.job_number )
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
		pattern_accounting_info = re.compile(r"CPU_T\s+WAIT\s+TURNAROUND\s+STATUS\s+HOG_FACTOR\s+MEM\s+SWAP", flags=re.IGNORECASE)
		keep = 'no_regex_match_found:check_src_code'
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

		# If queue='priority' is used then an extra line is possibly added:
		# Accounting information about this job:
		#      Share group charged </ptimshel>
		#      CPU_T     WAIT     TURNAROUND   STATUS     HOG_FACTOR    MEM    SWAP
		#   27089.57     4288          30632     done         0.8844   189M    576M
			lines = out.splitlines()
			for (i, line) in enumerate(lines):
				line = line.strip()
				match = pattern_accounting_info.search(line)
				if match:
					header = lines[i].split()
					values = lines[i+1].split()
					#NB: len(header) must be equal to len(values) for zip() to work?
					combined = map("=".join, zip(header, values)) #List_C = ['{} {}'.format(x,y) for x,y in zip(List_A,List_B)]
					keep = "|".join(combined)
					break
		keep = "{pid}|{name}|{status_line}".format(pid=pid, name=jobname, status_line=keep)
		return keep


	@staticmethod
	def report_status(pids, logger): #LB_List_Of_Instances
		""" 
		This method was fix/updated/debugged 01/28/2015
		The major change was replacing subprocess.check_output() with subprocess.Popen().
		Remember that subprocess.check_output() only pipes the STDOUT and not STDERR.
		"""
		sleep_time = 60 # seconds
		incomplete = copy.deepcopy(pids)
		finished = [] # list will contain 'report_line''s from _report_bacct
		failed = [] # list will contain 'report_line''s from _report_bacct
		done = [] # list will contain 'report_line''s from _report_bacct
		unknown_completion = [] # list will contain a message/string stating that the result is unknown

		waiting = []
		running = []
		#**TODO: make sure that pids and incomplete is UNIQUE
		#TODO: make sure that len(finished) NEVER becomes larger than len(pids)
		counter = 0
		start_time = time.time()

		pattern_job_not_found = re.compile(r"Job <(\d+)> is not found", flags=re.IGNORECASE|re.MULTILINE) # multiple flags

		################## While loop - START ##################
		while len(finished) < len(pids):
			counter += 1
			elapsed_time = time.time() - start_time
			logger.info( "Checking status: #{:d} | Run time = {:.5g} s ({:.3g} min)".format( counter, elapsed_time, elapsed_time/float(60) ) )
			logger.info( "Checking status: #{:d} | Finished={:d} [Fails={:d}, Unknown Completion={:d}], Incomplete={:d}, Total={:d}".format( counter, len(finished), len(failed), len(unknown_completion), len(incomplete), len(pids) ) )
			logger.info( "Checking status: #{:d} | Waiting={:d}, Running={:d}".format( counter, len(waiting), len(running) ) )
			call = "bjobs -aw {jobs}".format( jobs=" ".join(incomplete) ) #consider bjobs -aw

			### OLD - Making subprocess call
			# try:
			# 	out = subprocess.check_output(call, shell=True)
			# except subprocess.CalledProcessError as e: # if return code from "subprocess.check_output()" is non-zero the CalledProcessError is raised
			# 	emsg = e
			# 	logger.error( "call: %s\nerror in report_status: %s" % (call, emsg) )
			# else:
			# 	lines = out.splitlines()[1:] #skipping header


			### Making subprocess call
			p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
			(stdoutdata, stderrdata) = p.communicate() # OBS: .communicate() will wait for process to terminate.
			p_returncode = p.returncode
			
			### Look for all matches to "Job <XXXXXXX> is not found"
			# re.findall(pattern, string, flags=0)
			# Return all non-overlapping matches of pattern in string, as a list of strings. Will return empty list if no matched
			# If one group are present in the pattern, return a list of strings containing the groups;
			
			# NB. we are interested in all matches in the string - this is why we do NOT use search(stdoutdata, flags=re.MULTILINE).
			# If we where to use .search(), we would have to loop over each line in stdoutdata, which is inconvinient
			### Assuming that the stderrdata looks like this:
			# Job <8065143> is not found
			# Job <8065144> is not found
			list_of_matched_groups_stdoutdata = pattern_job_not_found.findall(stdoutdata)
			list_of_matched_groups_stderrdata = pattern_job_not_found.findall(stderrdata)

			if p_returncode != 0: # does not do anything - the only purpose is to present the user with information about the situtation
				logger.error( "Error in report_status: subprocess call returned non-zero exist status. Returncode = %s" % p_returncode )
				logger.error( "Subprocess call that caused error: %s" % call )
				logger.error( "Subprocess.STDOUT (if any):\n%s" % stdoutdata )
				logger.error( "Subprocess.STDERR (if any):\n%s" % stderrdata )
				logger.error( "This program handles this 'exception'-like situation in the 'if list_of_matched_groups_{stdoutdata/stderrdata}:' statements." )

			if list_of_matched_groups_stdoutdata: # I think stdoutdata will contain matches to the "pattern_job_not_found" ONLY when all JOB IDs in 'bjobs -aw [JOB IDs]' *does not exists* anymore.
				logger.error( "Processing STDOUT data from call (e.g. 'bjobs -aw [JOB IDs]'): {}".format(call) )
				logger.error( "As far as the program can tell (by regex matching), the error was caused by the following JOB IDs not being found: {}".format(" ".join(list_of_matched_groups_stdoutdata)) )
				logger.error( "Will add each of the these JOB IDs to 'finished' list and remove them from '{waiting/running/incomplete}'." )
				for tmp_pid in list_of_matched_groups_stdoutdata:
					report_line = "{pid}|{name}|{status_line}".format(pid=tmp_pid, name="...", status_line="Unknown - cannot get status of job")
					if tmp_pid in waiting: waiting.remove(tmp_pid)
					if tmp_pid in running: running.remove(tmp_pid)
					if tmp_pid in incomplete: incomplete.remove(tmp_pid) # maybe the "if tmp_pid in XXX" is not needed here...
					finished.append(report_line) #TODO - IMPROVE THIS: Perhaps we should not add the job to "finished". However, the while loop is dependent on 'finish' filling up
					unknown_completion.append(report_line)
			if list_of_matched_groups_stderrdata:
				logger.error( "Processing STDERR data from call (e.g. 'bjobs -aw [JOB IDs]'): {}".format(call) )
				logger.error( "As far as the program can tell (by regex matching), the error was caused by the following JOB IDs not being found: {}".format(" ".join(list_of_matched_groups_stderrdata)) )
				logger.error( "Will add each of the these JOB IDs to 'finished' list and remove them from '{waiting/running/incomplete}'." )
				for tmp_pid in list_of_matched_groups_stderrdata:
					report_line = "{pid}|{name}|{status_line}".format(pid=tmp_pid, name="...", status_line="Unknown - cannot get status of job")
					if tmp_pid in waiting: waiting.remove(tmp_pid)
					if tmp_pid in running: running.remove(tmp_pid)
					if tmp_pid in incomplete: incomplete.remove(tmp_pid) # maybe the "if tmp_pid in XXX" is not needed here...
					finished.append(report_line) #TODO - IMPROVE THIS: Perhaps we should not add the job to "finished". However, the while loop is dependent on 'finish' filling up
					unknown_completion.append(report_line)
			
			lines = ['']
			################## Checking stdoutdata ##################
			if stdoutdata:
				lines = stdoutdata.splitlines()[1:] #skipping header
			else:
				logger.error( "stdoutdata was empty from subprocess 'bjobs -aw [JOB IDs]' call. Will continue in 'while loop' in 10 seconds..." )
				time.sleep(10)
				continue

			################## Processing stdout from subprocess ##################
			for line in lines:
				cols = line.strip().split()
				(tmp_pid, tmp_status, tmp_jobname) = (cols[0], cols[2], cols[6])
				#'STAT' field has: [RUN,EXIT,DONE,PEND] and more!
				if tmp_status == 'EXIT':
					logger.info( "{pid}|{name}: jobstatus = EXIT. Waiting for _report_bacct...".format(pid=tmp_pid, name=tmp_jobname) )
					t1 = time.time()
					report_line = LaunchBsub._report_bacct(tmp_pid, tmp_jobname, logger)
					elapsed_time = time.time() - t1
					logger.info( "_report_bacct runtime: %s s (%s min)" % ( elapsed_time, elapsed_time/float(60) ) )
					logger.info( "return from _report_bacct: %s" % report_line ) # logging out report line
					incomplete.remove(tmp_pid)
					finished.append(report_line)
					failed.append(report_line)

					if tmp_pid in waiting: waiting.remove(tmp_pid) # remove from waiting - added June 2014
					if tmp_pid in running: running.remove(tmp_pid) # remove from running - added June 2014


				elif tmp_status == 'DONE':
					logger.info( "{pid}|{name}: jobstatus = DONE. Waiting for _report_bacct...".format(pid=tmp_pid, name=tmp_jobname) )
					t1 = time.time()
					report_line = LaunchBsub._report_bacct(tmp_pid, tmp_jobname, logger)
					elapsed_time = time.time() - t1
					logger.info( "_report_bacct runtime: %s s (%s min)" % ( elapsed_time, elapsed_time/float(60) ) )
					logger.info( "return from _report_bacct: %s" % report_line ) # logging out report line
					incomplete.remove(tmp_pid)
					finished.append(report_line)
					done.append(report_line)

					if tmp_pid in waiting: waiting.remove(tmp_pid) # remove from waiting - added June 2014
					if tmp_pid in running: running.remove(tmp_pid) # remove from running - added June 2014
				elif tmp_status == 'RUN':
					if not tmp_pid in running: # only add pid ONCE
						logger.info( "{pid}|{name}: jobstatus = RUN. Adding job to list of running jobs".format(pid=tmp_pid, name=tmp_jobname) )
						running.append(tmp_pid)
					if tmp_pid in waiting: waiting.remove(tmp_pid) # remove from waiting - added June 2014
				elif tmp_status in ['PEND', 'PSUSP', 'USUSP', 'SSUSP']:
					if not tmp_pid in waiting: # only add pid ONCE
						logger.info( "{pid}|{name}: jobstatus = ['PEND', 'PSUSP', 'USUSP', 'SSUSP']. Adding job to list of waiting jobs".format(pid=tmp_pid, name=tmp_jobname) )
						waiting.append(tmp_pid)
					if tmp_pid in running: running.remove(tmp_pid) # remove from running - added June 2014

			#consider sleeping for some time
			time.sleep(sleep_time)
		################## While loop - END ##################

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
			for job in done: logger.info(job)
		else:
			logger.info("No jobs to list")
		logger.info( "########### FAILED JOBS - %d ##############" % len(failed) )
		if failed:
			for job in failed: logger.critical(job)
		else:
			logger.info("No jobs to list")


	@staticmethod
	def report_status_multiprocess(pids, logger): #LB_List_Of_Instances
		""" Please note that report_status_multiprocess() currently does *NOT* support the following 'categories' of job status:
			- Running: 'RUN'
			- Waiting: 'PEND', 'PSUSP', 'USUSP', 'SSUSP'
		"""
		sleep_time = 60 # seconds
		incomplete = copy.deepcopy(pids)
		finished = [] # all jobs that are not runninng or pending - jobs that are either "exit" or "done"
		failed = [] # exit status
		done = [] # done status
		#**TODO: make sure that pids and incomplete is UNIQUE
		#TODO: make sure that len(finished) NEVER becomes larger than len(pids)
		counter = 0
		start_time = time.time()

		################## While loop - START ##################
		while len(finished) < len(pids):
			counter += 1
			elapsed_time = time.time() - start_time
			logger.info( "Checking status: #{:d} | Run time = {:.5g} s ({:.3g} min)".format( counter, elapsed_time, elapsed_time/float(60) ) )
			logger.info( "Checking status: #{:d} | Finished={:d}, Incomplete={:d}, Total={:d} [Fails={:d}]".format( counter, len(finished), len(incomplete), len(pids), len(failed) ) )
			lines = ['']
			call = "bjobs -aw {jobs}".format( jobs=" ".join(incomplete) ) #consider bjobs -aw
			
			### Making subprocess call
			p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
			(stdoutdata, stderrdata) = p.communicate() # OBS: .communicate() will wait for process to terminate.
			p_returncode = p.returncode
			if p_returncode != 0:
				logger.error( "Error in report_status: subprocess call returned non-zero exist status. Returncode = %s" % p_returncode )
				logger.error( "Subprocess call that caused error: %s" % call )
				logger.error( "Subprocess.STDOUT (if any): %s" % stdoutdata )
				logger.error( "Subprocess.STDERR (if any): %s" % stderrdata )
				logger.error( "Will attempt to make subprocess call again. (continue in while loop without missing anything)" )
				
				## Attempt to solve problem by 'continue'
				pause_time = 5 # seconds
				logger.error( "Will attempt to make subprocess call again in %s seconds. (continue in while loop without missing anything)" % pause_time )
				## NOTE: 	if continue is not called, an exception is likely to be raised in "... = (cols[0], cols[2], cols[6])" because stdoutdata and thus also cols is empty!
				## 		continue in this while loop does not "miss out" on any job checks. The only change is that *counter is incremented*.
				time.sleep(pause_time)
				continue 
			else:
				lines = stdoutdata.splitlines()[1:] #skipping header


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
					#logger.info( "i is %d" % ( i ) )
					pool.apply_async(report_bacct, args=(tmp_pid, tmp_jobname), callback=finished.append) # OBS: cannot parse logger since it is NOT a pickable object!
					#^^apply_async and map_async are intended to let the main process continuing. It does so maintaining an internal Queue which size is unfortunately impossible to change.
				pool.close()
				pool.join()
				elapsed_time = time.time() - t1
				logger.info( "Time to run join() pool: %s s (%s min)" % ( elapsed_time, elapsed_time/float(60) ) )

			#consider sleeping for some time
			time.sleep(sleep_time)
		################## While loop - END ##################


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


		###################################### SAMPLE OUTPUT from bacct ######################################
		# bacct -l 1013033ptimshel@copper:/cvar/jhlab/snpsnap/snpsnap> bacct -l 1013033


		# Accounting information about jobs that are:
		#   - submitted by all users.
		#   - accounted on all projects.
		#   - completed normally or exited
		#   - executed on all hosts.
		#   - submitted to all queues.
		#   - accounted on all service classes.
		# ------------------------------------------------------------------------------

		# Job <1013033>, Job Name <Height>, User <ptimshel>, Project <snpsnp>, Mail <pasc
		#                      al.timshel@gmail.com>, Status <DONE>, Queue <priority>, Co
		#                      mmand <python /cvar/jhlab/snpsnap/snpsnap/snpsnap_query.py
		#                       --user_snps_file /cvar/jhlab/snpsnap/data/input_lists/gwa
		#                      scatalog_140201_listsBIGbim/Height.txt --output_dir /cvar/
		#                      jhlab/snpsnap/data/query/gwascatalog_production_v1/bsub/bs
		#                      ub_output/Height --distance_type ld --distance_cutoff 0.5
		#                      match --N_sample_sets 10000 --ld_buddy_cutoff 0.5 --max_fr
		#                      eq_deviation 5 --max_distance_deviation 50 --max_genes_cou
		#                      nt_deviation 50 --max_ld_buddy_count_deviation 50 --exclud
		#                      e_input_SNPs>, Share group charged </ptimshel>
		# Tue Jul  1 23:34:24: Submitted from host <node1386>, CWD </cvar/jhlab/snpsnap/s
		#                      npsnap>, Output File </cvar/jhlab/snpsnap/data/query/gwasc
		#                      atalog_production_v1/bsub/bsub_stdout/Height.txt>;
		# Wed Jul  2 00:45:52: Dispatched to <node1417>;
		# Wed Jul  2 08:04:56: Completed <done>.

		# Accounting information about this job:
		#      Share group charged </ptimshel>
		#      CPU_T     WAIT     TURNAROUND   STATUS     HOG_FACTOR    MEM    SWAP
		#   27089.57     4288          30632     done         0.8844   189M    576M
		# ------------------------------------------------------------------------------

		# SUMMARY:      ( time unit: second )
		#  Total number of done jobs:       1      Total number of exited jobs:     0
		#  Total CPU time consumed:   27089.6      Average CPU time consumed: 27089.6
		#  Maximum CPU time of a job: 27089.6      Minimum CPU time of a job: 27089.6
		#  Total wait time in queues:  4288.0
		#  Average wait time in queue: 4288.0
		#  Maximum wait time in queue: 4288.0      Minimum wait time in queue: 4288.0
		#  Average turnaround time:     30632 (seconds/job)
		#  Maximum turnaround time:     30632      Minimum turnaround time:     30632
		#  Average hog factor of a job:  0.88 ( cpu time / turnaround time )
		#  Maximum hog factor of a job:  0.88      Minimum hog factor of a job:  0.88

		# ptimshel@copper:/cvar/jhlab/snpsnap/snpsnap>
		#################################################################################


####### OLD FUNCTION - using "if 'Accounting information about this job:' in line" - replaced 07/02/2014
####### MAY BE DELETED
# def report_bacct(pid, jobname):
# 	keep = ''
# 	call = "bacct -l %s" % pid
# 	try:
# 		out = subprocess.check_output(call, shell=True)
# 	except subprocess.CalledProcessError as e:
# 		emsg = e
# 		print "%s" % e 	### TODO: change this to a log statement! (requires parsing of a logger).
# 						### BUT BE CAREFUL: it may not work because the arguments MUST be pickable
# 	else:
# 		lines = out.splitlines()
# 		for (i, line) in enumerate(lines):
# 			line = line.strip()
# 			if 'Accounting information about this job:' in line:
# 				header = lines[i+1].split()
# 				values = lines[i+2].split()
# 				combined = map("=".join, zip(header, values)) #List_C = ['{} {}'.format(x,y) for x,y in zip(List_A,List_B)]
# 				keep = "|".join(combined)
# 				break
# 	keep = "{pid}|{name}|{status_line}".format(pid=pid, name=jobname, status_line=keep)
# 	return keep


###################################### OLD VERSION of *PART* of report_status()  ######################################
			####### Replaced 01/30/2015
			####### MAY BE DELETED

			# ### Making subprocess call
			# p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
			# (stdoutdata, stderrdata) = p.communicate() # OBS: .communicate() will wait for process to terminate.
			# p_returncode = p.returncode
			# if p_returncode != 0:
			# 	logger.error( "Error in report_status: subprocess call returned non-zero exist status. Returncode = %s" % p_returncode )
			# 	logger.error( "Subprocess call that caused error: %s" % call )
			# 	logger.error( "Subprocess.STDOUT (if any):\n%s" % stdoutdata )
			# 	logger.error( "Subprocess.STDERR (if any):\n%s" % stderrdata )
			# 	### Attempt to solve problem by 'continue'
			# 	#pause_time = 5 # seconds
			# 	#logger.error( "Will attempt to make subprocess call again in %s seconds. (continue in while loop without missing anything)" % pause_time )
			# 	#NOTE: 	if continue is not called, an exception is likely to be raised in "... = (cols[0], cols[2], cols[6])" because stdoutdata and thus also cols is empty!
			# 	#		continue in this while loop does not "miss out" on any job checks. The only change is that *counter is incremented*.
			# 	#time.sleep(pause_time)
			# 	#continue 

			# 	logger.error( "This program assumes that some jobs specified in 'bjobs -aw [JOB IDs]' could not be found. E.g. the error 'Job <8065143> is not found'" )
			# 	logger.error( "Will attempt to remove LSF jobs IDs that could not be found." )

			# 	pattern_job_not_found = re.compile(r"Job <(\d+)> is not found", flags=re.IGNORECASE)
			# 	for line in stderrdata.splitlines(): # 'keepends' is False by default. 
			# 		# ^^ IMPORTANT: stderrdata is a STRING and needs to be splitted. Newlines are automatically stripped using .splitlines()

			# 		### Assuming that the stderrdata looks like this:
			# 		# Job <8065143> is not found
			# 		# Job <8065144> is not found
			# 		# Job <8065145> is not found
			# 		mobj = pattern_job_not_found.match(line) # consider using .search() to match the whole string
			# 		if mobj: # if true: we have a match
			# 			tmp_pid = mobj.group(1) # Return the first parenthesized subgroup as a string.
			# 			report_line = "{pid}|{name}|{status_line}".format(pid=tmp_pid, name="...", status_line="Unknown - cannot get status of job")
			# 			if tmp_pid in waiting: waiting.remove(tmp_pid)
			# 			if tmp_pid in running: running.remove(tmp_pid)
			# 			if tmp_pid in incomplete: incomplete.remove(tmp_pid) # maybe the "if tmp_pid in XXX" is not needed here...
			# 			finished.append(report_line) #TODO - IMPROVE THIS: Perhaps we should not add the job to "finished". However, the while loop is dependent on 'finish' filling up
			# 			unknown_completion.append(report_line)
			
			# ################## Checking stdoutdata ##################
			# if stdoutdata:
			# 	lines = stdoutdata.splitlines()[1:] #skipping header
			# else:
			# 	logger.error( "stdoutdata was empty from subprocess 'bjobs -aw [JOB IDs]' call. Will continue in 'while loop' in 5 seconds..." )
			# 	time.sleep(5)
			# 	continue



class LaunchSubprocess(object):
	def __init__(self, cmd, path_stdout=os.getcwd(), logger=False, jobname='NoJobName'): #file_output=os.path.join(os.getcwd(), __name__+'.tmp.log'
		self.path_stdout = HelperUtils.check_if_writable(path_stdout)
		if logger: #TODO: check that logger is of class Logger?
			self.logger = logger
		else: # create new logger, with name e.g. LaunchSubprocess_NoLoggerParsed_2014-05-15_23.08.59.log
			#self.logger = Logger(self.__class__.__name__+"_NoLoggerParsed", path_stdout).get() # BEFORE JUNE 2014
			self.logger = Logger(name=self.__class__.__name__+"_NoLoggerParsed"+HelperUtils.gen_timestamp(), log_dir=path_stdout, log_format=1, enabled=True).get()
			
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

















