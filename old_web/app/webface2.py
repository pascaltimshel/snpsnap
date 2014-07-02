#!/bin/env python

# Import modules for CGI handling 
import cgi, cgitb

import os
import time # potential
import hashlib
import random

import subprocess


# Create instance of FieldStorage 
form = cgi.FieldStorage() 
#form = cgi.FieldStorage( keep_blank_values = 1 ) # DOES NOT WORK! Why
#form = cgi.FieldStorage(keep_blank_values=True) # DOES NOT WORK! Why?


session_id = hashlib.md5(repr(time.time())).hexdigest()
session_id = hashlib.md5(str(random.random())).hexdigest()
path_session_output = '/cvar/jhlab/snpsnap/web_results'+'/'+session_id
path_tmp_output = '/cvar/jhlab/snpsnap/web_tmp'
os.mkdir(path_session_output)

#file_snplist = os.path.join(path_tmp_output, "{}_{}".format(session_id, 'user_snplist') ) # version1
#file_snplist = "{}/{}_{}".format(path_tmp_output, session_id, 'user_snplist') # version2
file_snplist = path_tmp_output+'/'+session_id+'_user_snplist' # version3
file_status = path_tmp_output+'/'+session_id+'_status.json'
script2call = "/cvar/jhlab/snpsnap/snpsnap/snpsnap_query.py"

cgitb.enable()


# First try to read content of file upload. Hereafter read the content of textinput
def get_snplist():
	#if 'snplist_fileupload' in form: 
	#	fileitem = form['snplist_fileupload']
	fileitem = form['snplist_fileupload']
	# Test if the file was uploaded
	if fileitem.filename: # OBS fileitem.file does not seem to work!?
		open(file_snplist, 'w').write(fileitem.file.read())
		#NB: this may crash if the user inputs a binary file?
		message = 'The file "' + fileitem.filename + '" was uploaded successfully' # TEMPORARY
	else:
		message = 'No file was uploaded. Using text input instead' # TEMPORARY
		snplist = form.getvalue('snplist_text', '') # if no input: write out empty file
		open(file_snplist, 'w').write(snplist)
	snplist_upload_status = "<h3>%s</h3>" % message # TEMPORARY
	return snplist_upload_status # TEMPORARY

def print_args():
	for key in sorted(form.keys()):
		#if key == 'snplist_fileupload': continue
		print "%s: %s<br/>" % (key, form.getvalue(key))



snplist_upload_status = get_snplist() # read input snplist and write to file in /tmp
# Now get more arguments
distance_cutoff = form.getvalue('distance_cutoff', '')
distance_type = form.getvalue('distance_type', '')
max_distance_deviation = form.getvalue('max_distance_deviation', '')
max_freq_deviation = form.getvalue('max_freq_deviation', '')
max_genes_count_deviation = form.getvalue('max_genes_count_deviation', '')
N_sample_sets = form.getvalue('N_sample_sets', '')

email_address = form.getvalue('email_address', '')
job_name = form.getvalue('job_name', '')


annotate = form.getvalue('annotate', '')
set_file = form.getvalue('set_file', '')



#def print_java_script():



print "Content-Type: text/html"
print
print "<html>"
print "<head>"
print "<title>SNPSNAP - query result</title>"
print "<style>"
print "p.todo {color:red; font-weight:bold;}"
print "</style>"
## SEE: http://stackoverflow.com/questions/10721244/ajax-posting-to-python-cgi
## IMPORTANT: http://stackoverflow.com/questions/9540957/jquery-ajax-loop-to-refresh-jqueryui-progressbar
#print "<script src='http://ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js'></script>"
print "<script type='text/javascript' src='http://code.jquery.com/jquery-latest.min.js'></script>"
print "<script src='/js/get_status.js'></script>"

#print "<script>$(function() { alert('hello') });</script>"
print "</head>"

print "<body>"
print "<h1>Result page</h1>"
print "<h6>By Pascal Timshel</h6>"

################ PARSING SESSION ID ##################
print "<input type='hidden' id='session_id' value='%s'>" % session_id
##########################

print_args() # just for debuggin

print snplist_upload_status # just for debug

	

print "<p> Textarea is :</p>"
print """
<div style="color:blue;">
	%s
</div>
""" % cgi.escape('MISTAKE')

import platform
import sys # only need for print(sys.version)
print "<p>Python version: %s</p>" % platform.python_version()
print "<p>Python full string: %s</p>" % sys.version

print "<p class='todo'>Here goes the ***PROGRESS BAR***</p>"


commands_called = []
processes = []

if annotate:
	command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} annotate".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff)
	commands_called.append(command_shell)
	with open(os.devnull, "w") as fnull: # same as open('/dev/null', 'w')
		p = subprocess.Popen(command_shell, stdout = fnull, stderr = subprocess.STDOUT, shell=True)
		processes.append(p)
	#subprocess.Popen(command_shell, shell=True)



if set_file:
	command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} match --N_sample_sets {N_sample_sets} --max_freq_deviation {max_freq_deviation} --max_distance_deviation {max_distance_deviation} --max_genes_count_deviation {max_genes_count_deviation} --set_file".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff, \
																																																																											N_sample_sets=N_sample_sets, max_freq_deviation=max_freq_deviation, max_distance_deviation=max_distance_deviation, max_genes_count_deviation=max_genes_count_deviation)
	commands_called.append(command_shell)
	with open(os.devnull, "w") as fnull: # same as open('/dev/null', 'w')
		p = subprocess.Popen(command_shell, stdout = fnull, stderr = subprocess.STDOUT, shell=True)
		processes.append(p)
else:
	command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} --status_file {file_status} match --N_sample_sets {N_sample_sets} --max_freq_deviation {max_freq_deviation} --max_distance_deviation {max_distance_deviation} --max_genes_count_deviation {max_genes_count_deviation}".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff, file_status=file_status, \
																																																																											N_sample_sets=N_sample_sets, max_freq_deviation=max_freq_deviation, max_distance_deviation=max_distance_deviation, max_genes_count_deviation=max_genes_count_deviation)
	commands_called.append(command_shell)
	with open(os.devnull, "w") as fnull: # same as open('/dev/null', 'w')
		p = subprocess.Popen(command_shell, stdout = fnull, stderr = subprocess.STDOUT, shell=True)
		processes.append(p)


for c in commands_called:
	print "<p>%s</p>" % c

print "<p>Here is the list of process IDs:</p>"
for p in processes:
	print "%s</b>" % p.pid

#### Outcommented: we do not want to wait...
## print "<p>Now waiting for processes</p>"
## for p in processes:
## 	print "Waiting process: %s</b>" % p.pid
## 	p.wait()
## 	print "Process finished. Return code: %s" % p.returncode


print "</br>"
#print "<div id='myprogress'><progress value='22' max='100'></progress></div>"
print """
<h2>Here is the progress for match</h2>
<progress id='match_progress' value='0' max='100'></progress>
<div id='match_percentage'></div>"""
print "</br>"

print "<p>Your session ID is: %s</p>" % session_id
print "<p> An email will be sent to *%s* when your job is completed. (Most jobs finish within 5 minutes)</p>" % email_address



print "</body>"
print "</html>"






