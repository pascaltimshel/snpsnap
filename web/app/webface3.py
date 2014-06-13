#!/bin/env python

# Import modules for CGI handling 
import cgi, cgitb

import os
import time # potential
import hashlib
import random


import launchApp


# Create instance of FieldStorage 
form = cgi.FieldStorage() 
#form = cgi.FieldStorage( keep_blank_values = 1 ) # DOES NOT WORK! Why
#form = cgi.FieldStorage(keep_blank_values=True) # DOES NOT WORK! Why?


#session_id = hashlib.md5(repr(time.time())).hexdigest()
session_id = hashlib.md5(str(random.random())).hexdigest()
path_session_output = '/cvar/jhlab/snpsnap/web_results'+'/'+session_id
path_tmp_output = '/cvar/jhlab/snpsnap/web_tmp'
os.mkdir(path_session_output)

#file_snplist = os.path.join(path_tmp_output, "{}_{}".format(session_id, 'user_snplist') ) # version1
#file_snplist = "{}/{}_{}".format(path_tmp_output, session_id, 'user_snplist') # version2
file_snplist = path_tmp_output+'/'+session_id+'_user_snplist' # version3
file_status = path_tmp_output+'/'+session_id+'_status'


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
if len(job_name) >= 50: # only allow up to 50 character long job_name
	job_name = job_name[:50]

annotate = form.getvalue('annotate', '')
set_file = form.getvalue('set_file', '')

cmd_annotate = '' # OBS: important that default value evaluates to false in Bool context
cmd_match = ''
script2call = "/cvar/jhlab/snpsnap/snpsnap/snpsnap_query.py"
if annotate:
	cmd_annotate = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} --status_file {file_status} annotate".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff, file_status=file_status)

if set_file:
	cmd_match = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} --status_file {file_status} match --N_sample_sets {N_sample_sets} --max_freq_deviation {max_freq_deviation} --max_distance_deviation {max_distance_deviation} --max_genes_count_deviation {max_genes_count_deviation} --set_file".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff, file_status=file_status,\
																																																																												N_sample_sets=N_sample_sets, max_freq_deviation=max_freq_deviation, max_distance_deviation=max_distance_deviation, max_genes_count_deviation=max_genes_count_deviation)
else: 
	cmd_match = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} --status_file {file_status} match --N_sample_sets {N_sample_sets} --max_freq_deviation {max_freq_deviation} --max_distance_deviation {max_distance_deviation} --max_genes_count_deviation {max_genes_count_deviation}".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff, file_status=file_status, \
																																																																													N_sample_sets=N_sample_sets, max_freq_deviation=max_freq_deviation, max_distance_deviation=max_distance_deviation, max_genes_count_deviation=max_genes_count_deviation)


###################### FORKING ##################################
### This is a mess. Tried out the deamon process. It did not work...
#app = launchApp.Processor(session_id, email_address, job_name, cmd_annotate, cmd_match)
#app.start() #Start the process activity in a SEPERATE process.
#app.daemonize()

### Use this - the simplest solution. However, the browser stil waits for the process... (!)
#app = launchApp.Processor(session_id, email_address, job_name, cmd_annotate, cmd_match)
#app.fork_me()


############### SUBPROCESS TRAIL 1 ####################
# import subprocess
# import sys
# with open(os.devnull, "w") as fnull: # same as open('/dev/null', 'w')
# 	script2call = "/cvar/jhlab/snpsnap/snpsnap/web/app/launchApp.py"
# 	cmd_launch = "python {} --session_id {} --email_address {} --job_name {} --cmd_annotate {} cmd_match {}".format(script2call, session_id, email_address, job_name, cmd_annotate, cmd_match)
# 	sys.stderr.write("called command: %s\n" % cmd_launch)
# 	subprocess.Popen(cmd_launch, stdout = fnull, stderr = subprocess.STDOUT, shell=True)

############### SUBPROCESS  ####################
import subprocess
import sys
with open(os.devnull, "w") as fnull: # same as open('/dev/null', 'w')
	script2call = "/cvar/jhlab/snpsnap/snpsnap/web/app/launchApp.py"
	cmd_launch = [script2call,
				'--session_id', session_id,
				'--email_address', email_address,
				'--job_name', job_name,
				'--cmd_annotate', cmd_annotate,
				'--cmd_match', cmd_match
				]
	sys.stderr.write("called command: %s\n" % cmd_launch)
	p = subprocess.Popen(cmd_launch, stdout = fnull, stderr = subprocess.STDOUT)
	sys.stderr.write("process PID is %s\n" % p.pid)




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
print "<script src='/js/get_status_json.js'></script>"

#print "<script>$(function() { alert('hello') });</script>"
print "</head>"

print "<body>"
print "<h1>Result page</h1>"
print "<h6>By Pascal Timshel</h6>"

################ PARSING SESSION ID ##################
print "<input type='hidden' id='session_id' value='%s'>" % session_id
print "<input type='hidden' id='annotate' value='%s'>" % annotate
print "<input type='hidden' id='set_file' value='%s'>" % set_file
##########################

print_args() # just for debuggin

print snplist_upload_status # just for debug


#print "<div id='myprogress'><progress value='22' max='100'></progress></div>"

# print "<h2>Here is the progress for match</h2>"
# print "<progress id='progress_bar_match' value='0' max='100'></progress>"
# print "<div id='status_pct_match'></div>"
# print "</br>"
print "</br>"

print "<h2>Here is the progress for match</h2>"
print "<div id='progress_bar_match'>"
print "<progress value='0' max='100'></progress>"
print "<div id='status_pct_match'></div>"
print "</div>"
print "</br>"

print "<h2>Here is the progress for set_file</h2>"
print "<div id='progress_bar_set_file' style='display:none;'>"
print "<progress value='0' max='100'></progress>"
print "<div id='status_pct_set_file'></div>"
print "</div>"
print "</br>"

print "<h2>Here is the progress for annotate</h2>"
print "<div id='progress_bar_annotate' style='display:none;'>"
print "<progress value='0' max='100'></progress>"
print "<div id='status_pct_annotate'></div>"
print "</div>"
print "</br>"

#### RESULT LINKS
print "<div id='link_results' style='display:none;'>"
print "<h2>Your job is done! Files are available at: </h2>"
link_results = '/results/{sid}'.format(sid=session_id)
print "<a href='{link}' style='color:green;'>download result files</a>".format(link=link_results)
print "</div>"

print "<p>Your session ID is: %s</p>" % session_id
print "<p> An email will be sent to *%s* when your job is completed. (Most jobs finish within 5 minutes)</p>" % email_address



print "</body>"
print "</html>"
















# try:
# 	pid = os.fork()
# 	if pid > 0:
# 			# exit first parent
# 			sys.exit(0)
# except OSError, e:
# 	#sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
# 	sys.exit(1)

# # decouple from parent environment
# os.chdir("/")
# os.setsid()
# os.umask(0)

# # do second fork
# try:
# 	pid = os.fork()
# 	if pid > 0:
# 		# exit from second parent
# 		sys.exit(0)
# except OSError, e:
# 	#sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
# 	sys.exit(1)

