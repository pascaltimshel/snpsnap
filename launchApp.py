#!/bin/env python

import os
import time # potential

import subprocess

import collections

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import argparse
import json

import zipfile

#### LEFTOVERS: attempt to make threading/multiprocessing
#import multiprocessing
#import threading
# #class Processor(multiprocessing.Process):
# class Processor(threading.Thread):
# 	def __init__(self, session_id, email_address, job_name, cmd_annotate, cmd_match):
# 		#multiprocessing.Process.__init__(self)
# 		threading.Thread.__init__(self)

class Processor(object):
	def __init__(self, session_id, email_address, job_name, cmd_annotate, cmd_match, cmd_clump):
		#self.script2call = "/cvar/jhlab/snpsnap/snpsnap/snpsnap_query.py"
		self.session_id = session_id
		self.cmd_annotate=cmd_annotate # bool value
		self.cmd_match=cmd_match # bool value
		self.cmd_clump=cmd_clump # bool value
		self.email_address=email_address
		self.job_name=job_name
		#self.processes = []
		self.processes = collections.defaultdict(dict) # two-level dict
		#self.commands_called = []
		#self.returncodes = 
		
		#self.path_session_output = '/cvar/jhlab/snpsnap/web_results'+'/'+self.session_id
		#self.path_web_tmp_output = '/cvar/jhlab/snpsnap/web_tmp'
		
		self.path_session_output = '/local/data/web_results'+'/'+self.session_id
		self.path_web_tmp_output = '/local/data/web_tmp'
		self.file_returncodes = "{base}/{sid}_{type}.{ext}".format(base=self.path_web_tmp_output, sid=self.session_id, type='returncodes', ext='json')
		#self.link_result = "http://snpsnap.broadinstitute.org/mpg/snpsnap/results/{session_id}/{prefix}_{job}.zip".format(session_id=self.session_id, prefix='SNPsnap', job=self.job_name) # OLD VERSION, using internal URL
		self.link_result = "http://www.broadinstitute.org/mpg/snpsnap/results/{session_id}/{prefix}_{job}.zip".format(session_id=self.session_id, prefix='SNPsnap', job=self.job_name)

		self.summary = {}

	def daemonize(self):
		"""do the UNIX double-fork magic, see Stevens' "Advanced
		Programming in the UNIX Environment" for details (ISBN 0201563177)"""
		try:
			pid = os.fork()
			if pid > 0:
					# exit first parent
					#sys.exit(0)
					#os._exit(0)
					return
		except OSError, e:
			#sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
			raise
			#sys.exit(1)

		# decouple from parent environment
		os.chdir("/")
		os.setsid()
		os.umask(0)

		# do second fork
		try:
			pid = os.fork()
			if pid > 0:
				# exit from second parent
				#sys.exit(0)
				os._exit(0)
		except OSError, e:
			#sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
			raise
			#sys.exit(1)

		self.run()
		os._exit(0)

	def fork_me(self):
		pid = os.fork()
		if pid == 0:
			# we are the child
			#print 'Hello from child. My PID: %s' % os.getpid() 
			#app.run() #Start the process activity in a SEPERATE process.
			self.run() #Start the process activity in a SEPERATE process.
			#print 'I am done with app.run(). Exiting now My PID: %s' % os.getpid()
			os._exit(0) #Exit the process with status n, without calling cleanup handlers, flushing stdio buffers, etc.
		else:
			return # return to main CGI script
			# we are the parent. pid is not 0
			#print 'Hello from parent. My PID: %s | Child PID: %s' % (os.getpid(), pid)


	def read_report(self):
		#TODO: these files should go into the config file
		#path_web_tmp_output = '/cvar/jhlab/snpsnap/web_tmp'
		
		#OBS: this is the existing 'report/summary' file
		#file_report = "{base}/{sid}_{type}.{ext}".format(base=self.path_web_tmp_output, sid=self.session_id, type='report', ext='json') # OUTCOMMENTED 09/11/2014
		

		file_report_match = "{base}/{sid}_{file_type}_{subcommand}.{ext}".format(base=self.path_web_tmp_output, sid=self.session_id, file_type='report', subcommand='match', ext='json')
		file_report_annotate = "{base}/{sid}_{file_type}_{subcommand}.{ext}".format(base=self.path_web_tmp_output, sid=self.session_id, file_type='report', subcommand='annotate', ext='json')
		file_report_clump = "{base}/{sid}_{file_type}_{subcommand}.{ext}".format(base=self.path_web_tmp_output, sid=self.session_id, file_type='report', subcommand='clump', ext='json')
		
		file_report_bootface = "{base}/{sid}_{subcommand}.{ext}".format(base=self.path_web_tmp_output, sid=self.session_id, subcommand='bootface', ext='json')

		self.report_obj = None ## Needed for correct variable scope
		#### READING match ######
		try:
			with open(file_report_match, 'r') as json_data: ## TODO: make try: execpt: block
				self.report_obj = json.load(json_data)
		except:
			logger.warning( "Could not read match report: %s" % file_report_match )

		
		#### READING annotate ######
		# OBS: there is really not that much to read from this json file. I think that runtime is the only thing of interest.
		try:
			with open(file_report_annotate, 'r') as json_data: ## TODO: make try: execpt: block
				tmp_json = json.load(json_data)
	 			self.report_obj.update(tmp_json) #update() uses last-one-wins conflict-handling
		except:
			logger.warning( "Could not read annotate report: %s" % file_report_annotate )


		#### READING clump ######
		try:
			with open(file_report_clump, 'r') as json_data: ## TODO: make try: execpt: block
				tmp_json = json.load(json_data)
	 			self.report_obj.update(tmp_json) #update() uses last-one-wins conflict-handling
		except:
			logger.warning( "Could not read clump report: %s" % file_report_clump )


		#### READING bootface ######
		try:
			with open(file_report_bootface, 'r') as json_data: ## TODO: make try: execpt: block
				tmp_json = json.load(json_data)
	 			self.report_obj.update(tmp_json) #update() uses last-one-wins conflict-handling
		except:
			logger.warning( "Could not read bootface report: %s" % file_report_bootface )

		### FOR DEBUGGING
		#logger.info("After CLUMP: %s" % json.dumps(self.report_obj))

	def write_snpsnap_summary(self):
		## This function writes out the snpsnap_summary file to "MAIN" OUTPUT DIR, that is the path that snpsnap_query.py also writes to.
		
		file_snpsnap_summary = "{base}/{filename}.{ext}".format(base=self.path_session_output, filename='snpsnap_summary', ext='txt')

		### OUTCOMMENTED 09/11/2014 - no longer needed because information exists in bootface2.py
		# report_news =	{'session_id':self.session_id,
		# 					'job_name':self.job_name,
		# 					'email_address':self.email_address
		# 					}
		# #self.report_obj['web'].update(report_news)
		# self.report_obj['web'] = report_news


		f = open(file_snpsnap_summary, 'w')
		for category, params in self.report_obj.items():
			f.write( "##### {} #####".format(category.upper())+"\t"+"\n")
			for param, value in params.items():
				f.write( "{}\t{}".format(param.upper(), value) +"\n")
		f.close()



	def generate_report_for_email(self):
		### This function sets the report table for the email.

		# tmp1 = "Rating 'insufficient SNP matches' = '{rating:s}' with scale [{scale:s}]".format(rating=report_obj['insufficient_rating'], scale=report_obj['insufficient_scale_str'] )
		# tmp2 = "Percent 'insufficient SNP matches' = {pct:.4g}% (low is good; {count:d} 'insufficient SNP matches' out of {total:d} valid input SNPs)".format(pct=report_obj['insufficient_matches_pct'], count=report_obj['insufficient_N'], total=report_obj['N_snps'])
		# write_str_insufficient_rating = "<p>{}<br>{}</p>".format(tmp1,tmp2)


		# tmp1 = "Rating 'match size' = '{rating:s}' for SNPs in 'insufficient SNP matches' with scale [{scale:s}]".format(rating=report_obj['match_size_rating'], scale=report_obj['match_size_scale_str'] )
		# tmp2 = "Relative 'match size' = {pct:.4g}% (high is good; median number of SNPs to sample from in 'insufficient SNP matches' is {median:.6g} compared to {total:d} requested sample sets)".format(pct=report_obj['match_size_median_pct'], median=report_obj['match_size_median'], total=report_obj['N_sample_sets'])
		# write_str_score_match_size = "<p>{}<br>{}</p>".format(tmp1,tmp2)

		# report_html = write_str_insufficient_rating + write_str_score_match_size

		##### WORKED - replaced 07/10/2014 ########
		# report_html = """
		# <table style='width:75%;'>
		# <tr>
		#   <th>Evaluation type</th>
		#   <th>Rating</th> 
		# </tr>
		# <tr>
		#   <td>Insufficient-matches</td>
		#   <td>{insufficient_rating}</td> 
		# </tr>
		# <tr>
		#   <td>Match-size</td>
		#   <td>{match_size_rating}</td> 
		# </tr>
		# </table>
		# """.format(insufficient_rating=self.report_obj['report']['insufficient_rating'], match_size_rating=self.report_obj['report']['match_size_rating'])


		fmt_value_insufficient = "{:.2f}".format( self.report_obj['snpsnap_score']['insufficient_matches_pct'] ) # OBS: formatting number. You can format any number as float, but you cannot format floats as int (e.g. {:d})
		fmt_value_match_size = "{:.2f}".format( self.report_obj['snpsnap_score']['match_size_median_pct'] ) # OBS: formatting number. You can format any number as float, but you cannot format floats as int (e.g. {:d})

		insufficient_rating = self.report_obj['snpsnap_score']['insufficient_rating']
		match_size_rating = self.report_obj['snpsnap_score']['match_size_rating']

		report_html = """
		  <table style='width:75%;'>
		    <thead>
		      <tr>
		        <th style="text-align: right;">SNPsnap score</th>
		        <th style="text-align: right;">Value</th>
		        <th style="text-align: right;">Rating</th>
		      </tr>
		    </thead>
		    <tbody>
		      <tr>
		        <th style="text-align: right;">Insufficient-matches</th>
		        <td style="text-align: right;">{fmt_value_insufficient}%</td>
		        <td style="text-align: right;">{insufficient_rating}</td>
		      </tr>
		      <tr>
		        <th style="text-align: right;">Match-size</th>
		        <td style="text-align: right;">{fmt_value_match_size}%</td>
		        <td style="text-align: right;">{match_size_rating}</td>
		      </tr>
		    </tbody>
		  </table>
		""".format(
			fmt_value_insufficient=fmt_value_insufficient,
			insufficient_rating=insufficient_rating,
			fmt_value_match_size=fmt_value_match_size,
			match_size_rating=match_size_rating
			)


		return report_html



	def send_crash_email(self):
		fromaddr = "snpsnap@broadinstitute.org"
		toaddr = self.email_address

		msg = MIMEMultipart('alternative')
		msg['Subject'] = "SNPsnap job could not complete: %s" % self.job_name
		msg['From'] = fromaddr
		msg['To'] = toaddr

		text = "Your job {job} could not be completed due to an internal error.\n We apologize for the inconvenience\n--SNPsnap Team".format(job=self.job_name)
		html = """
		<html>
		  <head></head>
		  <body>
		    <h2>Your job {job} could not be completed</h2>
		    <p>An internal error caused your job to crash. Please re-run the job and report to the SNPsnap team if you keep getting this error message. </p>
		    <p>We apologize for the inconvenience.</p>
		    <p><i>SNPsnap Team</i></p>
		  </body>
		</html>
		""".format( job=self.job_name)

		part1 = MIMEText(text, 'plain')
		part2 = MIMEText(html, 'html')
		msg.attach(part1)
		msg.attach(part2)

		server = smtplib.SMTP('localhost')
		text = msg.as_string()
		server.sendmail(fromaddr, toaddr, text)
		server.quit()


	def send_email(self):
		""" Function to send out email """
		fromaddr = "snpsnap@broadinstitute.org"
		toaddr = self.email_address

		# Create message container - the correct MIME type is multipart/alternative.
		msg = MIMEMultipart('alternative')
		msg['Subject'] = "SNPsnap job finished: %s" % self.job_name
		msg['From'] = fromaddr
		msg['To'] = toaddr

		## create link to result file
		#link_result = "http://snpsnap.broadinstitute.org/results/{session_id}".format(session_id=self.session_id)
		

		### QUICK FUNCTION to write out call, process ID and return code
		### KEEP for now...
		# status_report = ""
		# for call_type in self.processes:
		# 	status_report += "<h2>{}</h2>".format(call_type)
		# 	for k, v in self.processes[call_type].items():
		# 		status_report += "{}:{}<br>".format(k, v)


		#<a href="{link}">link</a>
		# Create the body of the message (a plain-text and an HTML version).
		text = "Your job {job} has finished.\n Details should be available at:\n{link}\n--SNPsnap Team".format(job=self.job_name, link=self.link_result)
		html = """
		<html>
		  <head></head>
		  <body>
		    <h2>Your job {job} has finished.</h2>
		    <p>
		    	The result files can be downloaded at:<br>
		    	{link}
		    </p>

		    <h4>SNPsnap scores</h4>
		    <p>
		    	{report}
		    </p>
		    </br>
		    <p><i>SNPsnap Team</i></p>
		  </body>
		</html>
		""".format( job=self.job_name, link=self.link_result, report=self.generate_report_for_email() )

		# Record the MIME types of both parts - text/plain and text/html.
		part1 = MIMEText(text, 'plain')
		part2 = MIMEText(html, 'html')

		# Attach parts into message container.
		# According to RFC 2046, the last part of a multipart message, in this case
		# the HTML message, is best and preferred.
		msg.attach(part1)
		msg.attach(part2)

		# From email June 5th 2014 from BITs
		# ...You should either be using "localhost" if you are on a Linux VM, 
		# or "smtp.broadinstitute.org" if "localhost" doesn't work. 
		# Connecting to either of these email systems will use port 25 with no authentication.
		### This works on the Broad server
		server = smtplib.SMTP('localhost')
		text = msg.as_string()
		server.sendmail(fromaddr, toaddr, text)
		server.quit()

	###################### NOTE USED ANY MORE - zips entrie DIRECTORY STRUCTURE ###############
	@staticmethod
	def zip_folder(folder_path, output_path):
		"""Zip the contents of an entire folder (with that folder included in the archive). 
		Empty subfolders will be included in the archive as well."""
		zip_file = zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED)
		parent_folder = os.path.dirname(folder_path) # this is the PARRENT folder of the folder_path. e.g. parrent=/local/data when folder_path=/local/data/<session_id>
		# Retrieve the paths of the folder contents.
		contents = os.walk(folder_path) # ---> type generator
		for root, folders, files in contents:
			# Include all subfolders, including empty ones.
			for folder_name in folders:
				absolute_path = os.path.join(root, folder_name)
				relative_path = absolute_path.replace(parent_folder + os.sep, '')
				zip_file.write(absolute_path, arcname=relative_path)
			for file_name in files:
				absolute_path = os.path.join(root, file_name)
				relative_path = absolute_path.replace(parent_folder + os.sep, '')
				zip_file.write(absolute_path, arcname=relative_path)
		zip_file.close()
	#########################################################################################

	@staticmethod
	def zip_files(folder_path, output_path, archive_base_dir):
		"""Zip all the FILES in a folder and write them to a archive inside the folder_path. 
		path_output: specifies the dir and filename of the output zip file.
		archive_base_dir: specifices the name of the top level folder (where the files resides) inside the zip archive.
		NOTE: archive_base_name will be the name of the dir when the zip file is extracted
		RECOMMENDATION: use the same name for the output file and the archive name"""
		zip_file = zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED)
		# Retrieve the paths of the folder contents.
		contents = os.walk(folder_path) # ---> type generator
		for root, folders, files in contents:
			#logger.info( "root: %s\nfolders:[%s]\nfiles:[%s]" % (root, " ".join(folders), " ".join(files)) )
			for file_name in files: # we only care about files in the dir
				absolute_path = os.path.join(root, file_name)
				if '.zip' in file_name: continue # skip the zip_file we have just created
				archive_name=archive_base_dir+"/"+file_name
				zip_file.write(absolute_path, arcname=archive_name)
				
				#logger.info( "file_name:%s" % file_name )
				#logger.info( "archive_name:%s" % archive_name )
				
			break # we only want the TOP level in the dir
		zip_file.close()


	def run(self):
		## Note that you cannot get the output message from CalledProcessError execption.
		## This is because the output goes to /dev/null.
		## However, we do not want the user to know any more than an error occured.
		## Debugging must be done by me be replicating the example. 
		## (consider sending the formular in the email)

		if self.cmd_match:
			command_shell = self.cmd_match
			self.processes['match']['call'] = command_shell
			with open(os.devnull, "w") as fnull: # same as open('/dev/null', 'w')
				p = subprocess.Popen(command_shell, stdout = fnull, stderr = subprocess.STDOUT, shell=True)
				self.processes['match']['process_obj'] = p


		if self.cmd_annotate:
			command_shell = self.cmd_annotate # HACK
			self.processes['annotate']['call'] = command_shell
			with open(os.devnull, "w") as fnull: # same as open('/dev/null', 'w')
				p = subprocess.Popen(command_shell, stdout = fnull, stderr = subprocess.STDOUT, shell=True) 
				self.processes['annotate']['process_obj'] = p
				
				# ONLY FOR DEBUGGING!!!
				#p = subprocess.Popen(command_shell, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell=True)
				#(stdoutdata, stderrdata) = p.communicate()
				#logger.info( "annotate STDOUT: %s" % stdoutdata )
				#logger.info( "annotate STDERR: %s" % stderrdata )
				#SIGKILL	9	Exit	Killed

		if self.cmd_clump:
			command_shell = self.cmd_clump # HACK
			self.processes['clump']['call'] = command_shell
			with open(os.devnull, "w") as fnull: # same as open('/dev/null', 'w')
				p = subprocess.Popen(command_shell, stdout = fnull, stderr = subprocess.STDOUT, shell=True) 
				self.processes['clump']['process_obj'] = p

		# USED FOR DEBUGGING
		# if self.cmd_match:
		# 	print "cmd cmd_match"
		# 	command_shell = self.cmd_match
		# 	self.processes['match']['call'] = command_shell
		# 	p = subprocess.Popen(command_shell, stdout = None, stderr = subprocess.STDOUT, shell=True)
		# 	#self.processes.append(p)
		# 	self.processes['match']['process_obj'] = p

		### Now save PID (for potential later use) and WAIT for all processes to finish
		for call_type in self.processes:
			p = self.processes[call_type]['process_obj']
			self.processes[call_type]['pid'] = p.pid
			logger.info( "call_type=%s, waiting for PID=%s" % (call_type, p.pid) )
			p.wait() # this will also enable us to get the return code of the process
			self.processes[call_type]['returncode'] = p.returncode # saving return code

		## generating dict to contain return codes to be written to json file
		return_code_dict = {} # keys in dict will be 'match' and 'annotate'
		return_code_error_flag = False # if this flag is set to true, then send_crash_email() and return from this function
		for call_type in self.processes:
			p = self.processes[call_type]['process_obj']
			logger.info( "call_type=%s, return code for PID=%s: %s" % (call_type, p.pid, p.returncode) )
			return_code_dict[call_type] = p.returncode
			if p.returncode != 0:
				return_code_error_flag = True
		## WRITE return code file
		with open(self.file_returncodes, 'w') as f:
			json.dump(return_code_dict, f)

		if return_code_error_flag:
			logger.critical( "return_code_error_flag is set - will call send_crash_email and return!" )
			self.send_crash_email()
			return # IMPORTANT
		else:
			logger.info( "All jobs seem to have completed nicely! No return_code_error_flag is set..." )

		### Now all is done:
		logger.info( "read_report will be called" )
		self.read_report() # this sets the nessesary instance variables (i.e. self.report_obj) for the email to be generated
		logger.info( "write_snpsnap_summary will be called" )
		self.write_snpsnap_summary() # adds additional information (email, jobname) to report_obj and WRITE report to output dir (i.e. not temp dir)
		
		#self.zip_folder(self.path_session_output, self.path_session_output+'.zip') # OLD ZIP - zipping whole dir
		self.zip_files(folder_path=self.path_session_output, output_path=self.path_session_output+'/SNPsnap_'+self.job_name+'.zip', archive_base_dir='SNPsnap_'+self.job_name)
		### SOME EXAMPLES - do not delete:
		#folder_path: /local/data/web_results/f0fc477e4eaba3c4e0dbce1674ba26f2
		#output_path=/local/data/web_results/f0fc477e4eaba3c4e0dbce1674ba26f2/SNPsnap_<job_name>.zip 
		#archive_base_dir=SNPsnap_<job_name>


		## Send out email
		logger.info( "send_email will be called" )
		self.send_email()





def ParseArguments():
	arg_parser = argparse.ArgumentParser()

	#session_id, email_address, job_name, cmd_annotate, cmd_match

	### (SMALL) HACK
	## I here set default parameters to af FALSE value.
	## E.g if no --cmd_annotate argument is parsed the "if self.cmd_annotate:" block will not run
	arg_parser.add_argument("--session_id", default=False)
	arg_parser.add_argument("--email_address", default=False)
	arg_parser.add_argument("--job_name", default=False)
	arg_parser.add_argument("--cmd_annotate", default=False)
	arg_parser.add_argument("--cmd_match", default=False)
	arg_parser.add_argument("--cmd_clump", default=False)

	args = arg_parser.parse_args()
	return args


def setup_logger(outputdir, enabled=False, path_logging_module=os.getcwd()):
	""" Function to setup logger """
	import logging
	import sys
	import pplogger

	logger = None
	if not enabled:
		logger = pplogger.Logger(name=current_script_name, log_dir=args.output_dir, log_format=1, enabled=False).get()
	else:
		current_script_name = os.path.basename(__file__).replace('.py','')
		logger = pplogger.Logger(name=current_script_name, log_dir=outputdir, log_format=1, enabled=True).get()
		logger.setLevel(logging.DEBUG) #  <--- this should not be needed...
		## This works. Exceptions are written to the log AND printed to sys.stderr
		## An alternative solution is to make one big "try except" block in main:
		def handleException(excType, excValue, traceback, logger=logger):
			logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
		sys.excepthook = handleException

	return logger

if __name__ == '__main__':
	# We are now run from a terminal (e.g. a subprocess.Popen), i.e. imported
	args = ParseArguments()

	global logger
	logger = setup_logger(outputdir='/local/data/web_logs', enabled=True, path_logging_module='/cvar/jhlab/snpsnap/snpsnap')
	logger.info( "session_id: %s" % args.session_id )
	
	logger.info( "Will now print the command line arguments received from from the caller of this program:" )
	logger.info( "cmd_annotate: [%s]" % args.cmd_annotate )
	logger.info( "cmd_match: [%s]" % args.cmd_match )
	logger.info( "cmd_clump: [%s]" % args.cmd_clump )
	logger.info( "Will instantiate Processor object and call app.run()" )
	app = Processor(args.session_id, args.email_address, args.job_name, args.cmd_annotate, args.cmd_match, args.cmd_clump)
	app.run()



