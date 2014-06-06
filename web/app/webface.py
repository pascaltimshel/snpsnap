#!/usr/bin/python

#!/opt/rh/python27/root/usr/bin/python2.7
#!/opt/rh/python27/root/usr/bin/python

#!/usr/bin/python

#!/usr/bin/env python2.7
#!/usr/bin/env python




# Import modules for CGI handling 
import cgi, cgitb

import os
import time # potential
import hashlib
import random

import subprocess

#import pandas


session_id = hashlib.md5(repr(time.time())).hexdigest()
session_id = hashlib.md5(str(random.random())).hexdigest()
path_session = '/cvar/jhlab/snpsnap/web_results'+'/'+session_id
path_session_tmp = path_session+'/tmp'
path_session_output = path_session+'/res'
os.mkdir(path_session)
os.mkdir(path_session_tmp)
os.mkdir(path_session_output)

file_snplist = path_session_tmp+'/user_snplist'
script2call = "/cvar/jhlab/snpsnap/snpsnap/snpsnap_query.py"

cgitb.enable()

# Create instance of FieldStorage 
form = cgi.FieldStorage() 
#form = cgi.FieldStorage( keep_blank_values = 1 ) # DOES NOT WORK! Why
#form = cgi.FieldStorage(keep_blank_values=True) # DOES NOT WORK! Why?

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

email = form.getvalue('email', '')
job_name = form.getvalue('job_name', '')

annotate = form.getvalue('annotate', '')
set_file = form.getvalue('set_file', '')

#self.fh_output = open(self.file_output, 'w')
#self.process=subprocess.Popen(self.cmd, stdout=self.fh_output, stderr=subprocess.STDOUT, shell=True)

commands_called = []

if annotate:
	command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} annotate".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff)
	commands_called.append(command_shell)
	subprocess.Popen(command_shell, shell=True)

#command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(program=script2call, snplist=filename, outputdir=output_dir, N=N_sample_sets, freq=freq, dist=dist, gene_count=gene_count)


#command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(program=script2call, snplist=filename, outputdir=output_dir, N=N_sample_sets, freq=freq, dist=dist, gene_count=gene_count)
	

print "Content-Type: text/html"     # HTML is following
print                               # blank line, end of headers
print "<html>"
print "<head>"
print "<title>SNPSNAP - query result</title>"
print "<style>"
print "p.todo {color:red; font-weight:bold;}"
print "</style>"
print "</head>"

print "<body>"
print "<h1>Result page</h1>"
print "<h6>By Pascal Timshel</h6>"

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

print "<p>Your session ID is: %s</p>" % session_id
print "<p> An email will be sent to *%s* when your job is completed. (Most jobs finish within 5 minutes)</p>" % email

print "<p class='todo'>Here goes the ***PROGRESS BAR***</p>"

for c in commands_called:
	print "<p>%s</p>" % c

print "</body>"
print "</html>"


#print "<p> </p>"







# def get_snplist():
# 	fileitem = form['snplist_fileupload']
# 	# Test if the file was uploaded
# 	if fileitem.filename:
# 		# strip leading path from file name to avoid directory traversal attacks
# 		fn = os.path.basename(fileitem.filename)
# 		open('/cvar/jhlab/snpsnap/upload/' + fn, 'wb').write(fileitem.file.read())
# 		message = 'The file "' + fn + '" was uploaded successfully'
# 	else:
# 		message = 'No file was uploaded. Using text input instead'

# 	print "<h3>%s</h3>" % message
