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

#### LEFTOVERS: attempt to make threading/multiprocessing
#import multiprocessing
#import threading
# #class Processor(multiprocessing.Process):
# class Processor(threading.Thread):
# 	def __init__(self, session_id, email_address, job_name, cmd_annotate, cmd_set_file):
# 		#multiprocessing.Process.__init__(self)
# 		threading.Thread.__init__(self)



class WebMaster(object):
	def __init__(self, session_id, email_address, job_name, cmd_annotate, cmd_set_file):
		#self.script2call = "/cvar/jhlab/snpsnap/snpsnap/snpsnap_query.py"
		self.session_id = session_id
		self.cmd_annotate=cmd_annotate # bool value
		self.cmd_set_file=cmd_set_file # bool value
		self.email_address=email_address
		self.job_name=job_name
		#self.processes = []
		self.processes = collections.defaultdict(dict) # two-level dict
		#self.commands_called = []
		#self.returncodes = 

	def get_config(self):
		pass


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


	def run(self):
		## Note that you cannot get the output message from CalledProcessError execption.
		## This is because the output goes to /dev/null.
		## However, we do not want the user to know any more than an error occured.
		## Debugging must be done by me be replicating the example. 
		## (consider sending the formular in the email)

		if self.cmd_annotate:
			command_shell = self.cmd_annotate # HACK
			#command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} annotate".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff)
			#self.commands_called.append(command_shell)
			self.processes['annotate']['call'] = command_shell
			with open(os.devnull, "w") as fnull: # same as open('/dev/null', 'w')
				p = subprocess.Popen(command_shell, stdout = fnull, stderr = subprocess.STDOUT, shell=True)
				#self.processes.append(p)
				self.processes['annotate']['process_obj'] = p


		if self.cmd_set_file:
			command_shell = self.cmd_set_file
			#self.commands_called.append(command_shell)
			self.processes['match']['call'] = command_shell
			with open(os.devnull, "w") as fnull: # same as open('/dev/null', 'w')
				p = subprocess.Popen(command_shell, stdout = fnull, stderr = subprocess.STDOUT, shell=True)
				#self.processes.append(p)
				self.processes['match']['process_obj'] = p

		# else:
		# 	command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} --status_file {file_status} match --N_sample_sets {N_sample_sets} --max_freq_deviation {max_freq_deviation} --max_distance_deviation {max_distance_deviation} --max_genes_count_deviation {max_genes_count_deviation}".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff, file_status=file_status, \
		# 																																																																											N_sample_sets=N_sample_sets, max_freq_deviation=max_freq_deviation, max_distance_deviation=max_distance_deviation, max_genes_count_deviation=max_genes_count_deviation)
		# 	#self.commands_called.append(command_shell)
		# 	self.processes['match']['call'] = command_shell
		# 	with open(os.devnull, "w") as fnull: # same as open('/dev/null', 'w')
		# 		p = subprocess.Popen(command_shell, stdout = fnull, stderr = subprocess.STDOUT, shell=True)
		# 		#self.processes.append(p)
		# 		self.processes['match']['process_obj'] = p

		# ### Now wait for all processes to finish
		# for p in self.processes:
		# 	p.wait() # this will also enable us to get the return code of the process

		### Now save PID (for potential later use) and WAIT for all processes to finish
		for call_type in self.processes:
			p = self.processes[call_type]['process_obj']
			self.processes[call_type]['pid'] = p.pid
			p.wait() # this will also enable us to get the return code of the process

		for call_type in self.processes:
			p = self.processes[call_type]['process_obj']
			self.processes[call_type]['returncode'] = p.returncode # not nessesary to save value in dict...

		## Now all is done: send out email
		self.send_email()


class Processor(object):
	def __init__(self, session_id, email_address, job_name, cmd_annotate, cmd_set_file):
		#self.script2call = "/cvar/jhlab/snpsnap/snpsnap/snpsnap_query.py"
		self.session_id = session_id
		self.cmd_annotate=cmd_annotate # bool value
		self.cmd_set_file=cmd_set_file # bool value
		self.email_address=email_address
		self.job_name=job_name
		#self.processes = []
		self.processes = collections.defaultdict(dict) # two-level dict
		#self.commands_called = []
		#self.returncodes = 
		
	def create_report(self):
		path_tmp_output = '/cvar/jhlab/snpsnap/web_tmp'
		json_file = "{base}/{sid}_{type}.{ext}".format(base=path_tmp_output, sid=self.session_id, type='report', ext='json')

		report_obj = None ## Needed for correct variable scope
		with open(json_file, 'r') as json_data:
			report_obj = json.load(json_data)

		# "insufficient_rating":insufficient_rating,
		# "insufficient_matches_pct":insufficient_matches_pct, 
		# "insufficient_N":insufficient_N,
		# "N_snps":N_snps,
		# 'insufficient_scale_str':insufficient_scale_str,
		# "match_size_rating":match_size_rating,
		# "match_size_median_pct":match_size_median_pct,
		# "match_size_median":match_size_median,
		# "N_sample_sets":N_sample_sets,
		# 'match_size_scale_str':match_size_scale_str

		tmp1 = "Rating 'insufficient SNP matches' = '{rating:s}' with scale [{scale:s}]".format(rating=report_obj['insufficient_rating'], scale=report_obj['insufficient_scale_str'] )
		tmp2 = "Percent 'insufficient SNP matches' = {pct:.4g}% (low is good; {count:d} 'insufficient SNP matches' out of {total:d} valid input SNPs)".format(pct=report_obj['insufficient_matches_pct'], count=report_obj['insufficient_N'], total=report_obj['N_snps'])
		write_str_insufficient_rating = "<p>{}<br/>{}</p>".format(tmp1,tmp2)


		tmp1 = "Rating 'match size' = '{rating:s}' for SNPs in 'insufficient SNP matches' with scale [{scale:s}]".format(rating=report_obj['match_size_rating'], scale=report_obj['match_size_scale_str'] )
		tmp2 = "Relative 'match size' = {pct:.4g}% (high is good; median number of SNPs to sample from in 'insufficient SNP matches' is {median:.6g} compared to {total:d} requested sample sets)".format(pct=report_obj['match_size_median_pct'], median=report_obj['match_size_median'], total=report_obj['N_sample_sets'])
		write_str_score_match_size = "<p>{}<br/>{}</p>".format(tmp1,tmp2)

		report_html = write_str_insufficient_rating + write_str_score_match_size
		return report_html

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
		link_result = "http://snpsnap.broadinstitute.org/results/{session_id}".format(session_id=self.session_id)
		

		### QUICK FUNCTION to write out call, process ID and return code
		### KEEP for now...
		# status_report = ""
		# for call_type in self.processes:
		# 	status_report += "<h2>{}</h2>".format(call_type)
		# 	for k, v in self.processes[call_type].items():
		# 		status_report += "{}:{}<br/>".format(k, v)


		#<a href="{link}">link</a>
		# Create the body of the message (a plain-text and an HTML version).
		text = "Your job {job} has finished.\n Details should be available at:\n{link}\n--SNPsnap Team".format(job=self.session_id, link=link_result)
		html = """
		<html>
		  <head></head>
		  <body>
		    <p>
		       Your job {job} has finished. <br/>
		       The result files can be downloaded at: <br/>
		       {link}
		    </p>
		    <p>Report:</p>
		    <p>{report}</p>
		  </body>
		</html>
		""".format(job=self.job_name, link=link_result, report=self.create_report())

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

	args = arg_parser.parse_args()
	return args


def setup_logger(outputdir, enabled=False, path_logging_module=os.getcwd()):
	""" Function to setup logger """
	import logging
	import sys
	### DIRTY
	if not os.path.exists(path_logging_module): 
		raise Exception('path_logging_module does not exists: %s. Check that your paths are correct' % path_logging_module)
	else:
		sys.path.insert(0, path_logging_module) 
	from pplogger import Logger
	#from ... pplogger import Logger # ---> only works with modules

	logger = None
	if not enabled:
		logger = logging.getLogger()
		noop = logging.NullHandler()
		logger.addHandler(noop)
	else:
		current_script_name = os.path.basename(__file__).replace('.py','')
		logger = Logger(name=current_script_name, logdir=outputdir, format=1).get() # gives logname --> snapsnap_query.py
		#logger = Logger(name=__name__, logdir=args.output_dir, format=1).get() # gives logname --> __name__ == main
		logger.setLevel(logging.DEBUG) # consider setting 

		## This works. Exceptions are written to the log AND printed to sys.stderr
		## An alternative solution is to make one big "try except" block in main:
			# 
		def handleException(excType, excValue, traceback, logger=logger):
			logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
		sys.excepthook = handleException

	return logger

if __name__ == '__main__':
	# We are now run from a terminal (e.g. a subprocess.Popen), i.e. imported
	args = ParseArguments()

	global logger
	logger = setup_logger(outputdir='/cvar/jhlab/snpsnap/snpsnap/web/app', enabled=True, path_logging_module='/cvar/jhlab/snpsnap/snpsnap')
	app = Processor(args.session_id, args.email_address, args.job_name, args.cmd_annotate, args.cmd_match)
	app.run()



