#!/bin/env python

import os
import time # potential

import subprocess

#import multiprocessing
import threading

import collections

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



import sys
cmd_match = "python /cvar/jhlab/snpsnap/snpsnap/snpsnap_query.py --user_snps_file /cvar/jhlab/snpsnap/web_tmp/bf1d367b7bac7d6ff60fb2cfc728b090_user_snplist --output_dir /cvar/jhlab/snpsnap/web_results/bf1d367b7bac7d6ff60fb2cfc728b090 --distance_type ld --distance_cutoff 0.5 --status_file /cvar/jhlab/snpsnap/web_tmp/bf1d367b7bac7d6ff60fb2cfc728b090_status.json match --N_sample_sets 1000 --max_freq_deviation 5 --max_distance_deviation 20 --max_genes_count_deviation 20"
cmd_annotate = ''
email_address = 'joe@somemail.com'
session_id = 'bf1d367b7bac7d6ff60fb2cfc728b090'
job_name = 'test_job_multi'




#class Processor(multiprocessing.Process):
class Processor(threading.Thread):
	def __init__(self, session_id, email_address, job_name, cmd_annotate, cmd_set_file):
		#multiprocessing.Process.__init__(self)
		threading.Thread.__init__(self)
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
		print "PROCESSOR: class instance created"

	def send_email(self):
		""" Function to send out email """
		fromaddr = "snpsnap@broadinstitute.org"
		toaddr = self.email_address

		# Create message container - the correct MIME type is multipart/alternative.
		msg = MIMEMultipart('alternative')
		msg['Subject'] = "SNPsnap job complete: %s" % self.job_name
		msg['From'] = fromaddr
		msg['To'] = toaddr

		## create link to result file
		link_result = "http://snpsnap.broadinstitute.org/results/{session_id}".format(session_id=self.session_id)
		## generate status report
		status_report = ""
		for call_type in self.processes:
			status_report += "<h2>{}</h2>".format(call_type)
			for k, v in self.processes[call_type].items():
				status_report += "{}:{}<br/>".format(k, v)

		# Create the body of the message (a plain-text and an HTML version).
		text = "Hi!\nHow are you?\nHere is the link you wanted:\n{link}".format(link=link_result)
		html = """\
		<html>
		  <head></head>
		  <body>
		    <p>Hi!<br/>
		       Your job has completed. See below for further description of the completion<br/>
		       Here is the <a href="{link}">link</a> to the result files.
		    </p>
		    <p>Here is some information for your reference:</p>
		    <p>{status}</p>
		  </body>
		</html>
		""".format(link=link_result, status=status_report)

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


	def run(self):
		## Note that you cannot get the output message from CalledProcessError execption.
		## This is because the output goes to /dev/null.
		## However, we do not want the user to know any more than an error occured.
		## Debugging must be done by me be replicating the example. 
		## (consider sending the formular in the email)

		print "PROCESSOR: inside run()"
		print 'PROCESSOR: My PID: %s' % os.getpid()


		if self.cmd_annotate:
			command_shell = self.cmd_annotate # HACK
			#command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} annotate".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff)
			#self.commands_called.append(command_shell)
			self.processes['annotate']['call'] = command_shell
			with open(os.devnull, "w") as fnull: # same as open('/dev/null', 'w')
				p = subprocess.Popen(command_shell, stdout = fnull, stderr = subprocess.STDOUT, shell=True)
				#self.processes.append(p)
				self.processes['annotate']['process_obj'] = p
		
		print "PROCESSOR: after annotate"


		if self.cmd_set_file:
			command_shell = self.cmd_set_file
			#self.commands_called.append(command_shell)
			self.processes['match']['call'] = command_shell
			with open(os.devnull, "w") as fnull: # same as open('/dev/null', 'w')
				p = subprocess.Popen(command_shell, stdout = fnull, stderr = subprocess.STDOUT, shell=True)
				#self.processes.append(p)
				self.processes['match']['process_obj'] = p

		print "PROCESSOR: after set_file"

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

		print "PROCESSOR: before wait"

		### Now save PID (for potential later use) and WAIT for all processes to finish
		for call_type in self.processes:
			p = self.processes[call_type]['process_obj']
			self.processes[call_type]['pid'] = p.pid
			p.wait() # this will also enable us to get the return code of the process

		print "PROCESSOR: after wait"


		for call_type in self.processes:
			p = self.processes[call_type]['process_obj']
			self.processes[call_type]['returncode'] = p.returncode # not nessesary to save value in dict...
		
		print "PROCESSOR: after returncode"


		## Now all is done: send out email
		self.send_email()

		print "PROCESSOR: after sending mail"


print 'MAIN thread: My PID: %s' % os.getpid()
print "MAIN thread: about to call app launchApp.Processor()"

app = Processor(session_id, email_address, job_name, cmd_annotate, cmd_match)
app.start() #Start the process activity in a SEPERATE process.

print "MAIN thread: call done. Main thread may exit now"

#sys.exit(0)

