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
	snplist_upload_status = "<p>%s</p>" % message # TEMPORARY
	return snplist_upload_status # TEMPORARY

def list_args():
	arg_list = "<ul>"
	for key in sorted(form.keys()):
		arg_list += "<li>%s: %s</li>" % (key, form.getvalue(key))
	arg_list += "</ul>"
	#if key == 'snplist_fileupload': continue
	return arg_list


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
print "<!DOCTYPE html>"
print "<html>"
print "<head>"
print "<title>SNPSNAP - query result</title>"
print "<style>"
print """
body {
  padding-top: 50px;
}
.h1 {
  text-align: center;
}
"""
# .results {
#   padding: 40px 15px;
#   text-align: center;
# }

print "</style>"
## SEE: http://stackoverflow.com/questions/10721244/ajax-posting-to-python-cgi
## IMPORTANT: http://stackoverflow.com/questions/9540957/jquery-ajax-loop-to-refresh-jqueryui-progressbar
#print "<script src='http://ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js'></script>"
print "<script type='text/javascript' src='http://code.jquery.com/jquery-latest.min.js'></script>"
print "<link href='/static/css/bootstrap.min.css' rel='stylesheet'>"
print "<script src='/static/js/bootstrap.min.js'></script>"
print "<script src='/js/get_status_boot.js'></script>"

#print "<script>$(function() { alert('hello') });</script>"
print "</head>"

print "<body>"



print "<div class='container'>" ## START container

    # <div class="navbar navbar-inverse navbar-fixed-top" role="navigation">
    #   <div class="container">
    #     <div class="navbar-header">
    #       <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-collapse">
    #         <span class="sr-only">Toggle navigation</span>
    #         <span class="icon-bar"></span>
    #         <span class="icon-bar"></span>
    #         <span class="icon-bar"></span>
    #       </button>
    #       <a class="navbar-brand" href="#">Project name</a>
    #     </div>
    #     <div class="collapse navbar-collapse">
    #       <ul class="nav navbar-nav">
    #         <li class="active"><a href="#">Home</a></li>
    #         <li><a href="#about">About</a></li>
    #         <li><a href="#contact">Contact</a></li>
    #       </ul>
    #     </div><!--/.nav-collapse -->
    #   </div>
    # </div>

    # <div class="container">

    #   <div class="starter-template">
    #     <h1>Bootstrap starter template</h1>
    #     <p class="lead">Use this document as a way to quickly start any new project.<br> All you get is this text and a mostly barebones HTML document.</p>
    #   </div>

    # </div><!-- /.container -->


print "<h1>Result page</h1>"
print "<h6>By Pascal Timshel</h6>"

print "<p>Your session ID is: %s</p>" % session_id
print "<p> An email will be sent to *%s* when your job is completed. (Most jobs finish within 5 minutes)</p>" % email_address


################ PARSING SESSION ID ##################
print "<input type='hidden' id='session_id' value='%s'>" % session_id
print "<input type='hidden' id='annotate' value='%s'>" % annotate
print "<input type='hidden' id='set_file' value='%s'>" % set_file
##########################

#<!-- <a data-toggle="collapse" data-target="#me" href="#javascript:void(0);"> -->


###################################### PANEL GROUP ######################################
print '<div class="panel-group" id="accordion">' # START panel
###############################################################################################

################## PANEL: PARAMETERS ##################
print """
  <div class="panel panel-default" id='panel_parameters'>
    <div class="panel-heading">
      <h4 class="panel-title">
        <a data-toggle="collapse" data-target="#collapse_parameters" href="#collapse_parameters" onClick="return false;">
          Job Parameters
        </a>
      </h4>
    </div>
    <div id="collapse_parameters" class="panel-collapse collapse"> 
      <div class="panel-body">
      	{args} </br>
      	{extra}
      </div>
    </div>
  </div>
""".format(args=list_args(), extra=snplist_upload_status)


################## PANEL: PROGRESS ##################

str_bar_match = """
<div class='row' id='row_progress_match'>
	<div class='col-md-1'>
		<p class="text-primary"><strong>Match</strong></p>
	</div>
	<div class='col-md-1'>
		<p class="text-info"></p>
	</div>
	<div class='col-md-10'>
		<div class='progress progress-striped active' id='progress_bar_match'>
			<div class='progress-bar' style='width: 0%'></div>
		</div>
	</div>
</div>
"""	

str_bar_set_file = """
<div class='row' id='row_progress_set_file'>
	<div class='col-md-1'>
		<p class="text-primary"><strong>Set_file</strong></p>
	</div>
	<div class='col-md-1'>
		<p class="text-info"></p>
	</div>
	<div class='col-md-10'>
		<div class='progress progress-striped active' id='progress_bar_set_file'>
			<div class='progress-bar' style='width: 0%'></div>
		</div>
	</div>
</div>
"""	


str_bar_annotate = """
<div class='row' id='row_progress_annotate'>
	<div class='col-md-1'>
		<p class="text-primary"><strong>Annotate</strong></p>
	</div>
	<div class='col-md-1'>
		<p class="text-info"></p>
	</div>
	<div class='col-md-10'>
		<div class='progress progress-striped active' id='progress_bar_annotate'>
			<div class='progress-bar' style='width: 0%'></div>
		</div>
	</div>
</div>
"""	

###### Now print PROGRESS panel
print """
  <div class="panel panel-default" id='panel_progress'>
    <div class="panel-heading">
      <h4 class="panel-title">
        <a data-toggle="collapse" data-target="#collapse_progress" href="#collapse_progress" onClick="return false;">
          Report
        </a>
      </h4>
    </div>
    <div id="collapse_progress" class="panel-collapse collapse in"> 
      <div class="panel-body">
      	{match}
      	{set_file}
      	{annotate}
      </div>
    </div>
  </div>
""".format(match=str_bar_match, set_file=str_bar_set_file, annotate=str_bar_annotate)


################## PANEL: REPORT ##################
print """
  <div class="panel panel-default" id='panel_report'>
    <div class="panel-heading">
      <h4 class="panel-title">
        <a data-toggle="collapse" data-target="#collapse_report" href="#collapse_report" onClick="return false;">
          Results
        </a>
      </h4>
    </div>
    <div id="collapse_report" class="panel-collapse collapse in"> 
      <div class="panel-body">
      </div>
    </div>
  </div>
"""

################## PANEL: RESULTS ##################
url_results = '/results/{sid}'.format(sid=session_id)
link_results = "<a href='{url}' style='color:green;'>Download result files</a>".format(url=url_results)
str_results = "Your job is done! {link}".format(link=link_results)

print """
  <div class="panel panel-default" id='panel_results'>
    <div class="panel-heading">
      <h4 class="panel-title">
        <a data-toggle="collapse" data-target="#collapse_results" href="#collapse_results" onClick="return false;">
          Job status
        </a>
      </h4>
    </div>
    <div id="collapse_results" class="panel-collapse collapse in"> 
      <div class="panel-body">
      {results}
      </div>
    </div>
  </div>
""".format(results=str_results)


###################################### PANEL GROUP - END ######################################
print '</div>'
###############################################################################################


print "</div>" ## END container

print "</body>"
print "</html>"















####### This worked for bootstrap v.2.3 ###########
# print "<div class='results'>" # START results

# print "<h2>Here is the progress for match</h2>"
# print "<div id='progress_bar_match'>"
# print "<div class='progress progress-striped active'>"
# #print "<div class='progress progress-striped active' id='progress_bar_match'>"
# print "<div class='bar'></div>"
# print "</div>"
# print "</div>"

# print "<h2>Here is the progress for set_file</h2>"
# print "<div id='progress_bar_set_file' style='display:none;'>"
# print "<div class='progress progress-striped active'>"
# print "<div class='bar'></div>"
# print "</div>"
# print "</div>"


# print "<h2>Here is the progress for annotate</h2>"
# print "<div id='progress_bar_annotate' style='display:none;'>"
# print "<div class='progress progress-striped active'>"
# print "<div class='bar'></div>"
# print "</div>"
# print "</div>"

# print "</div>" # END results
#####################################################
