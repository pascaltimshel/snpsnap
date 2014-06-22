#!/bin/env python

# Import modules for CGI handling 
import cgi, cgitb

cgitb.enable()

import os
import time # potential
import hashlib
import random

os.sys.path.insert(0,'/cvar/jhlab/snpsnap/snpsnap') 
import launchApp


# First try to read content of file upload. Hereafter read the content of textinput
def get_snplist():
	snplist_input_type = ''
	### OBS - strange solution: form['snplist_fileupload'] will raise expection if 'snplist_fileupload' is not parsed via the URL (GET or POST)
	#if 'snplist_fileupload' in form: 
	fileitem = form['snplist_fileupload']

	# Test if the file was uploaded
	if fileitem.filename: # OBS fileitem.file does not seem to work!?
		open(file_snplist, 'w').write(fileitem.file.read())
		#NB: this may crash if the user inputs a binary file?
		snplist_input_type = "fileupload ({filename})".format(filename=fileitem.filename)
	else:
		## Text input: write file to disk
		snplist = form.getvalue('snplist_text', '') # if no input: write out empty file
		open(file_snplist, 'w').write(snplist)
		snplist_input_type = 'text input'
	#snplist_input_type = "<p>%s</p>" % message # TEMPORARY
	return snplist_input_type

def list_args():
  arg_list = "<ul>"
  for key in sorted(form.keys()):
	arg_list += "<li>%s: %s</li>" % (key, form.getvalue(key))
  arg_list += "</ul>"
  #if key == 'snplist_fileupload': continue
  return arg_list

def construct_job_params():
	params = """
	<div style='width:100%;'>
	<table class="table table-hover table-condensed">
	  <thead>
	    <tr>
	      <th></th>
	      <th>Parameter</th>
	      <th>Value</th>
	    </tr>
	  </thead>
	  <tbody>
	    <tr>
	      <th>Input</th>
	      <td>Input type</td>
	      <td>{snplist_input_type}</td>
	    </tr>
	    <tr>
	      <th>Loci definition</th>
	      <td>Distance type</td>
	      <td>{distance_type}</td>
	    </tr>
	    <tr>
	      <td></td>
	      <td>Distance cutoff</td>
	      <td>{distance_cutoff}</td>
	    </tr>
	    <tr>
	      <td></td>
	      <td>Distance type</td>
	      <td>{distance_type}</td>
	    </tr>
	    <tr>
	      <th>Maximum deviations for matching SNPs</th>
	      <td>MAF</td>
	      <td>{max_freq_deviation}</td>
	    </tr>
	    <tr>
	      <td></td>
	      <td>Gene count in loci</td>
	      <td>{max_genes_count_deviation}</td>
	    </tr>
	    <tr>
	      <td></td>
	      <td>Distance to nearest gene</td>
	      <td>{max_distance_deviation}</td>
	    </tr>
	    <tr>
	      <th>Options</th>
	      <td>Number of matching SNP sets</td>
	      <td>{N_sample_sets}</td>
	    </tr>
	    <tr>
	      <td></td>
	      <td>Create set file</td>
	      <td>{set_file}</td>
	    </tr>
	    <tr>
	      <td></td>
	      <td>Annotate input SNPs</td>
	      <td>{annotate}</td>
	    </tr>
	    <tr>
	      <th>Session information</th>
	      <td>Job name</td>
	      <td>{job_name}</td>
	    </tr>
	  </tbody>
	</table>
	</div>
	""".format(	snplist_input_type=snplist_input_type,
				distance_type=distance_type,
				distance_cutoff=distance_cutoff,
				max_freq_deviation=max_freq_deviation, 
				max_genes_count_deviation=max_genes_count_deviation, 
				max_distance_deviation=max_distance_deviation, 
				N_sample_sets=N_sample_sets,
				set_file='yes' if set_file else 'no',
				annotate='yes' if annotate else 'no',
				job_name=job_name
				)
	return params

# Create instance of FieldStorage 
form = cgi.FieldStorage() 
#form = cgi.FieldStorage( keep_blank_values = 1 ) # DOES NOT WORK! Why
#form = cgi.FieldStorage(keep_blank_values=True) # DOES NOT WORK! Why?

########### SESSION ID ###########
#session_id = hashlib.md5(repr(time.time())).hexdigest()
session_id = hashlib.md5(str(random.random())).hexdigest()

########## PATHS ############
#### ***OBS***: if you change these paths you MUST change them in launchApp.py status_json.py and report_json.py 
path_session_output = '/cvar/jhlab/snpsnap/web_results'+'/'+session_id
path_web_tmp_output = '/cvar/jhlab/snpsnap/web_tmp'
#os.mkdir('/local/data/web_results')
#os.mkdir('/local/data/web_tmp')

#path_session_output = '/local/data/web_results'+'/'+session_id # New June 21 - after Andrew Teixeira. Only present here!
#path_web_tmp_output = '/local/data/web_tmp' # New June 21 - Fix in 'launchApp.py', report_html.py', 'status_json.py'
os.mkdir(path_session_output)

url_results = 'results/{sid}.zip'.format(sid=session_id) # used in PANEL: RESULTS

#file_snplist = os.path.join(path_web_tmp_output, "{}_{}".format(session_id, 'user_snplist') ) # version1
#file_snplist = "{}/{}_{}".format(path_web_tmp_output, session_id, 'user_snplist') # version2
file_snplist = path_web_tmp_output+'/'+session_id+'_user_snplist' # version3
file_prefix_web_tmp = path_web_tmp_output+'/'+session_id




snplist_input_type = get_snplist() # read input snplist and write to file in /tmp
# Now get more arguments
distance_type = form.getvalue('distance_type', '')
distance_cutoff = form.getvalue('distance_cutoff', '')
max_freq_deviation = form.getvalue('max_freq_deviation', '')
max_genes_count_deviation = form.getvalue('max_genes_count_deviation', '')
max_distance_deviation = form.getvalue('max_distance_deviation', '')
N_sample_sets = form.getvalue('N_sample_sets', '')

email_address = form.getvalue('email_address', '')
job_name = form.getvalue('job_name', '')
if job_name == '': # setting 'default' job name
	job_name = 'no_name'
elif len(job_name) >= 50: # only allow up to 50 character long job_name
	job_name = job_name[:50]

annotate = form.getvalue('annotate', '')
set_file = form.getvalue('set_file', '')

cmd_annotate = '' # OBS: important that default value evaluates to false in Bool context
cmd_match = ''
script2call = "/cvar/jhlab/snpsnap/snpsnap/snpsnap_query.py"
if annotate:
	cmd_annotate = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} --web {file_prefix_web_tmp} annotate".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff, file_prefix_web_tmp=file_prefix_web_tmp)

if set_file:
	cmd_match = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} --web {file_prefix_web_tmp} match --N_sample_sets {N_sample_sets} --max_freq_deviation {max_freq_deviation} --max_distance_deviation {max_distance_deviation} --max_genes_count_deviation {max_genes_count_deviation} --set_file".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff, file_prefix_web_tmp=file_prefix_web_tmp,\
																																																																												N_sample_sets=N_sample_sets, max_freq_deviation=max_freq_deviation, max_distance_deviation=max_distance_deviation, max_genes_count_deviation=max_genes_count_deviation)
else: 
	cmd_match = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} --web {file_prefix_web_tmp} match --N_sample_sets {N_sample_sets} --max_freq_deviation {max_freq_deviation} --max_distance_deviation {max_distance_deviation} --max_genes_count_deviation {max_genes_count_deviation}".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff, file_prefix_web_tmp=file_prefix_web_tmp, \
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
	script2call = "/cvar/jhlab/snpsnap/snpsnap/launchApp.py"
	cmd_launch = [script2call,
				'--session_id', session_id,
				'--email_address', email_address,
				'--job_name', job_name,
				'--cmd_annotate', cmd_annotate,
				'--cmd_match', cmd_match
				]
	#cmd_formatted = '{program} {p_session_id} "{session_id}" {p_email_address} "{email_address}" {p_job_name} "{job_name}" {p_cmd_annotate} "{cmd_annotate}" {p_cmd_match} "{cmd_match}"'.format()
	cmd_formatted = '{} {} "{}" {} "{}" {} "{}" {} "{}" {} "{}"'.format(*cmd_launch)
	sys.stderr.write("called command: %s\n" % cmd_launch)
	sys.stderr.write("FORMATTED called command: %s\n" % cmd_formatted)
	p = subprocess.Popen(cmd_launch, stdout = fnull, stderr = subprocess.STDOUT)
	sys.stderr.write("process PID is %s\n" % p.pid)




print "Content-Type: text/html"
print
print "<!DOCTYPE html>"
print "<html>"
print "<head>"
# print "<style>"
# print """
# body {
#   padding-top: 50px;
# }
# .h1 {
#   text-align: center;
# }
## """
## .results {
##   padding: 40px 15px;
##   text-align: center;
## }
# print "</style>"


## SEE: http://stackoverflow.com/questions/10721244/ajax-posting-to-python-cgi
## IMPORTANT: http://stackoverflow.com/questions/9540957/jquery-ajax-loop-to-refresh-jqueryui-progressbar
############# THIS WORKED - OUTCOMMENTED June 18 ##################
# print "<script type='text/javascript' src='http://code.jquery.com/jquery-latest.min.js'></script>"
# print "<link href='/static/css/bootstrap.min.css' rel='stylesheet'>"
# print "<script src='/static/js/bootstrap.min.js'></script>"

## CONSIDER USING A BASE TAG ON THIS SITE
# <BASE href="http://www.aviary.com/products/intro.html">


print """
<BASE href="http://snpsnap.broadinstitute.org/mpg/snpsnap/">

<!-- FAVICON -->
<link rel="shortcut icon" href="img/broad_logo/BroadSeal-20140621-favicon.ico">
<link rel="icon" type="image/png" href="img/broad_logo/favicon-32x32.png" sizes="32x32">

<title>SNPsnap</title>

<!-- Bootstrap core CSS -->
<link href="static/css/bootstrap.min.css" rel="stylesheet">

<!-- Custom styles for SNPsnap -->
<link href="css/jumbotron-narrow.css" rel="stylesheet">
<link href="css/snpsnap.css" rel="stylesheet">


<!-- GOOGLE FONTS -->
<link href="http://fonts.googleapis.com/css?family=Crimson+Text" rel="stylesheet" type="text/css">


<!-- Bootstrap core JavaScript -->
<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.0/jquery.min.js"></script>
<script src="static/js/bootstrap.min.js"></script>


"""

###################################### MY JAVASCRIPTS ######################################
print "<script src='js/results.js'></script>"
###############################################################################################

###################################### HEAD - END ######################################
print "</head>"
###############################################################################################


###################################### BODY - START ######################################
print "<body>"
###############################################################################################


###################################### CONTAINER - START ######################################
print "<div class='container'>"
###############################################################################################


# print """
# <div class="row">
# 	<div class="col-xs-6"><h1 class='allerta'>SNPsnap</h1></div>
# 	<div class="col-xs-6"><img class="img-responsive" src="img/broad_logo/BroadLogo.png"></div>
# </div>
# 	</br>
	
# 	<div class="header">
# 		<ul class="nav nav-pills pull-right">
# 			<li><a href="/index_boot.html">Home</a></li>
# 			<li class="active"><a href="/match.html">Match SNPs</a></li>
# 			<li><a href="#">Documentation</a></li>
# 			<li><a href="#">FAQ</a></li>
# 			<li><a href="#">Contact</a></li>
# 		</ul>
# 	</div>
# 	</br>
# """

print """
<div class="row">
	<div class="col-xs-6"><h1 class='allerta'>SNPsnap</h1></div>
	<div class="col-xs-6"><img class="img-responsive" src="img/broad_logo/BroadLogo.png"></div>
</div>
	</br>
	
	<div class="header">
		<ul class="nav nav-pills pull-right">
			<li><a href="index.html">Home</a></li>
			<li class="active"><a href="match_snps.html">Match SNPs</a></li>
			<li><a href="faq.html">FAQ</a></li>
			<li><a href="documentation.html">Documentation</a></li>
			<li><a href="contact.html">Contact</a></li>
		</ul>
	</div>
	</br>
"""



#print "<div class='container'>" ## START container

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


print "<h1>Job submitted</h1>"

#print "<p>Your session ID is: %s</p>" % session_id
print "<p> An email will be sent to <strong>%s</strong> when the job is completed.</p>" % email_address


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
		{args}
	  </div>
	</div>
  </div>
""".format(args=construct_job_params())
#""".format(args=list_args(), extra=snplist_input_type)


################## PANEL: PROGRESS ##################

str_bar_match = """
<div class='row' id='row_progress_match'>
	<div class='col-xs-1'>
		<p class="text-primary"><strong>Match</strong></p>
	</div>
	<div class='col-xs-2'>
		<p class="text-info"></p>
	</div>
	<div class='col-xs-9'>
		<div class='progress progress-striped active' id='progress_bar_match'>
			<div class='progress-bar' style='width: 0%'></div>
		</div>
	</div>
</div>
"""	

str_bar_set_file = """
<div class='row' id='row_progress_set_file'>
	<div class='col-xs-1'>
		<p class="text-primary"><strong>Set_file</strong></p>
	</div>
	<div class='col-xs-2'>
		<p class="text-info"></p>
	</div>
	<div class='col-xs-9'>
		<div class='progress progress-striped active' id='progress_bar_set_file'>
			<div class='progress-bar' style='width: 0%'></div>
		</div>
	</div>
</div>
"""	


str_bar_annotate = """
<div class='row' id='row_progress_annotate'>
	<div class='col-xs-1'>
		<p class="text-primary"><strong>Annotate</strong></p>
	</div>
	<div class='col-xs-2'>
		<p class="text-info"></p>
	</div>
	<div class='col-xs-9'>
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
		  Job Status
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
		  Report
		</a>
	  </h4>
	</div>
	<div id="collapse_report" class="panel-collapse collapse in"> 
	  <div class="panel-body" id='snpsnap_report'>
	  </div>
	</div>
  </div>
"""

################## PANEL: RESULTS ##################
#url_results = '/results/{sid}.zip'.format(sid=session_id)
#link_results = "<a href='{url}' style='color:green;'>Download result files</a>".format(url=url_results) # version1
#str_results = "Your job is done!</br>{link}".format(link=link_results) # version1
#str_results = "<button type='button' class='btn btn-success'>{link}</button>".format(link=link_results)  # version2 - not complete?
#str_results = "<a class='btn btn-success' href='{url}'><i class='icon-download'></i>Download results</a>".format(url=url_results) # version3 - works only for bootstrap 2
str_results = "<a href='{url}' class='btn btn-default btn-success'><span class='glyphicon glyphicon-download'></span> Download Results</a>".format(url=url_results) # verison4 - works for bootstrap 3!

print """
  <div class="panel panel-default" id='panel_results'>
	<div class="panel-heading">
	  <h4 class="panel-title">
		<a data-toggle="collapse" data-target="#collapse_results" href="#collapse_results" onClick="return false;">
		  Results
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


###################################### FOOTER ######################################

print """
<div class="footer">
<div class="col-xs-3"><p>&copy; Broad 2014</p></div>
<div class="col-xs-8"></div>
<div class="col-xs-1"><img class="img-responsive" src="img/broad_logo/BroadSeal.png"></div>
</div> 
"""
###############################################################################################


###################################### CONTAINER - END ######################################
print "</div>" 
###############################################################################################


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
