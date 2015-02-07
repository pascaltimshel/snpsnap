#!/bin/env python


class FormValidationError(Exception):
	""" Exception raised for errors in the form input from the website
	The arguments for instantiating the class is 'args': tuple of arguments given to the exception constructor. """
	# ** question: how does the inheritance work when the __init__ of the parrent class is not called?
	# SEE more at: http://stackoverflow.com/questions/1319615/proper-way-to-declare-custom-exceptions-in-modern-python
	# https://docs.python.org/2/library/exceptions.html
	# https://docs.python.org/2/tutorial/errors.html#user-defined-exceptions
	pass

###################################### HEADER OF PAGE ######################################
snpsnap_header = """
<!DOCTYPE html>
<html lang="en">
<head>
	<!-- ############################ SPECIAL FOR BOOTFACE ######################### -->
	<!-- <BASE href="http://snpsnap.broadinstitute.org/mpg/snpsnap/"> -->
	<BASE href="http://www.broadinstitute.org/mpg/snpsnap/">
	<!-- ################################################################################### -->

	<title>SNPsnap</title>
	<meta charset="utf-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<meta name="description" content="SNPsnap - matching SNPs based on genetic properties. Enhance your SNP-based enrichment analysis.">
	<meta name="author" content="Broad Institute of MIT and Harvard">
	<meta name="keywords" content="Broad Institute of MIT and Harvard, history, Genome Center, Whitehead Institute/MIT Center for Genome Research, Human Genome Project, Eric Lander, Institute of Chemistry and Cell Biology, Stuart Schreiber, Initiative for Chemical Genetics, Harvard University, Harvard medical School, MIT, Massachusetts Institute of Technology, Human Genome Project" />

	<!-- FAVICON -->
	<link rel="shortcut icon" href="img/broad_logo/BroadSeal-20140621-favicon.ico">
	<link rel="icon" type="image/png" href="img/broad_logo/favicon-32x32.png" sizes="32x32">

	<!-- Custom styles for SNPsnap -->
	<link href="css/jumbotron-narrow.css" rel="stylesheet">
	<link href="css/snpsnap.css" rel="stylesheet">

	<!-- GOOGLE FONTS -->
	<link href="http://fonts.googleapis.com/css?family=Crimson+Text" rel="stylesheet" type="text/css">

	<!-- GOOGLE ANALYTICS -->
	<script src="js/snpsnap_googleanalytics.js"></script>

	<!-- jQuery -->
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.0/jquery.min.js"></script>

	<!-- Bootstrap core CSS -->
	<link href="static/css/bootstrap.min.css" rel="stylesheet">
	<!-- Bootstrap core JavaScript - must come AFTER jQuery -->
	<script src="static/js/bootstrap.min.js"></script>

	<!-- ############################ SPECIAL FOR BOOTFACE ######################### -->

	<script src='js/results.js'></script>
	<!-- ################################################################################### -->

</head>
"""



###################################### NAV OF PAGE ######################################
snpsnap_match_nav = """
<div class="container-non-responsive">

<div class="row">
	<div class="col-xs-6"><h1 class='allerta'>SNPsnap</h1></div>
	<div class="col-xs-6"><img class="img-responsive min-limits" src="img/broad_logo/BroadLogo.png"></div>
</div>
<br>
	
<div class="header">
	<ul class="nav nav-pills">
		<li><a href="index.html">Home</a></li>
		<li class="active"><a href="match_snps.html">Match SNPs</a></li>
		<li><a href="faq.html">FAQ</a></li>
		<li><a href="documentation.html">Documentation</a></li>
		<li><a href="contact.html">Contact</a></li>
	</ul>
</div>
"""
###############################################################################################

###################################### FOOTER ######################################

snpsnap_footer = """
 <!-- ############## FOOTER ################### -->
<div class="footer">
	<div class="col-xs-3"><p>&copy; Broad 2014</p></div>
	<div class="col-xs-8"></div>
	<div class="col-xs-1"><img class="img-responsive footer_min_limits" src="img/broad_logo/BroadSeal.png"></div>
</div>
 <!-- end FOOTER -->
"""
###############################################################################################



def run():
	# Import modules for CGI handling 
	import cgi, cgitb

	### OBS - displed this as a part of finalization 07/04/2014 ####
	#cgitb.enable()

	import os
	import time # potential
	import hashlib
	import random

	os.sys.path.insert(0,'/cvar/jhlab/snpsnap/snpsnap') 
	import launchApp

	import subprocess
	import sys

	import re # used for formula validation

	import collections # NEW 09/11/2014 - for Report() class
	import json # NEW 09/11/2014 - for Report() class

	class Report():
		def __init__(self, filebasename):
			## NOTE: filebasename is file_prefix_web_tmp
			#*OBS*; filebasename will have the value like: '/cvar/jhlab/snpsnap/web_tmp/2ede5955021a10cb0e1a13882be520eb'.
			self.fname = "{name_parsed}_{subcommand}.{ext}".format(name_parsed=filebasename, subcommand='bootface', ext='json')
			self.report = collections.defaultdict(dict) # two-level dict
			# VALID CATEGORIES for bootface: 
			#loci_definition
			#match_criteria
			#options

		def write_json_report(self):
			with open(self.fname, 'w') as f:
				json.dump(self.report, f, indent=3)

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
		      <th>Maximum deviations for matching SNPs</th>
		      <td>Minor Allele Frequency</td>
		      <td>{max_freq_deviation}</td>
		    </tr>
		    <tr>
		      <td></td>
		      <td>Gene density</td>
		      <td>{max_genes_count_deviation}</td>
		    </tr>
		    <tr>
		      <td></td>
		      <td>Distance to nearest gene</td>
		      <td>{max_distance_deviation}</td>
		    </tr>
		    <tr>
		      <td></td>
		      <td>LD buddies</td>
		      <td>{max_ld_buddy_count_deviation}</td>
		    </tr>
		    <tr>
		      <th>Options</th>
		      <td>Requested number of matched SNPs</td>
		      <td>{N_sample_sets}</td>
		    </tr>
		    <tr>
		      <td></td>
		      <td>Annotate matched SNPs</td>
		      <td>{set_file}</td>
		    </tr>
		    <tr>
		      <td></td>
		      <td>Annotate input SNPs</td>
		      <td>{annotate}</td>
		    </tr>
		    <tr>
		      <td></td>
		      <td>Report independent loci</td>
		      <td>{clump}</td>
		    </tr>
		    <tr>
		      <td></td>
		      <td>Clumping LD threshold</td>
		      <td>{clump_r2}</td>
		    </tr>
		    <tr>
		      <td></td>
		      <td>Clumping kb threshold</td>
		      <td>{clump_kb}</td>
		    </tr>
		    <tr>
		      <th>SNP Exclusions</th>
		      <td>Exclude input SNPs in matched SNPs</td>
		      <td>{exclude_input_SNPs}</td>
		    </tr>
		    <tr>
		      <td></td>
		      <td>Exclude HLA SNPs</td>
		      <td>{exclude_HLA_SNPs}</td>
		    </tr>
		    <tr>
		      <th>Session information</th>
		      <td>Job name</td>
		      <td>{job_name}</td>
		    </tr>
		    <tr>
		      <td></td>
		      <td>Session ID</td>
		      <td>{session_id}</td>
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
					max_ld_buddy_count_deviation=max_ld_buddy_count_deviation,
					N_sample_sets=N_sample_sets,
					set_file='yes' if set_file else 'no',
					annotate='yes' if annotate else 'no',
					clump='yes' if clump else 'no',
					clump_r2=clump_r2 if clump else 'NA',
					clump_kb=clump_kb if clump else 'NA',
					exclude_input_SNPs='yes' if exclude_input_SNPs else 'no',
					exclude_HLA_SNPs='yes' if exclude_HLA_SNPs else 'no',
					job_name=job_name,
					session_id=session_id
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
	#path_session_output = '/cvar/jhlab/snpsnap/web_results'+'/'+session_id
	#path_web_tmp_output = '/cvar/jhlab/snpsnap/web_tmp'

	path_session_output = '/local/data/web_results'+'/'+session_id # New June 21 - after Andrew Teixeira. Fix in 'bootface.py', 'launchApp.py'
	path_web_tmp_output = '/local/data/web_tmp' # New June 21 - Fix in 'bootface.py', 'launchApp.py', report_html.py', 'status_json.py'
	os.mkdir(path_session_output)


	#file_snplist = os.path.join(path_web_tmp_output, "{}_{}".format(session_id, 'user_snplist') ) # version1
	#file_snplist = "{}/{}_{}".format(path_web_tmp_output, session_id, 'user_snplist') # version2
	file_snplist = path_web_tmp_output+'/'+session_id+'_user_snplist' # version3
	file_prefix_web_tmp = path_web_tmp_output+'/'+session_id


	##############################################################################
	############################## READING WEB ARGUMENTS #########################
	##############################################################################

	snplist_input_type = get_snplist() # read input snplist and write to file in /tmp
	# Now get more arguments
	distance_type = form.getvalue('distance_type', '')
	distance_cutoff = form.getvalue('distance_cutoff', '')

	max_freq_deviation = form.getvalue('max_freq_deviation', '')
	max_genes_count_deviation = form.getvalue('max_genes_count_deviation', '')
	max_distance_deviation = form.getvalue('max_distance_deviation', '')
	max_ld_buddy_count_deviation = form.getvalue('max_ld_buddy_count_deviation', '')
	
	ld_buddy_cutoff = form.getvalue('ld_buddy_cutoff', '')
	N_sample_sets = form.getvalue('N_sample_sets', '')

	email_address = form.getvalue('email_address', '')
	job_name = form.getvalue('job_name', '')
	if job_name == '': # setting 'default' job name
		job_name = 'no_name'
	elif len(job_name) >= 100: # only allow up to 100 character long job_name
		job_name = job_name[:100]
	
	match_job_name = re.match("^[A-Za-z0-9_]+$", job_name)
	if match_job_name is None:
		raise FormValidationError("Job name", "Job name must match regular expression character set [A-Za-z0-9_]")

	###################### URL Results - remember that the HTML <base> tag is used #############
	#url_results = 'results/{sid}.zip'.format(sid=session_id) # used in PANEL: RESULTS
	url_results = "results/{session_id}/{prefix}_{job}.zip".format(session_id=session_id, prefix='SNPsnap', job=job_name)

	###### CHECKBOXES ########
	# INFO: type "checkbox" and "radio": will have value 'on' for selected checkbox elements without value attributes
	# REF: http://www.eskimo.com/~scs/cclass/handouts/cgi.html
	exclude_input_SNPs = form.getvalue('exclude_input_SNPs', '') # value will be 'on' if parsed (and no value attribute is specified)
	exclude_HLA_SNPs = form.getvalue('exclude_HLA_SNPs', '') # value will be 'on' if parsed (and no value attribute is specified)
	
	annotate = form.getvalue('annotate', '') # value will be 'on' if parsed (and no value attribute is specified)
	set_file = form.getvalue('set_file', '') # value will be 'on' if parsed (and no value attribute is specified)

	clump = form.getvalue('clump', '')
	clump_r2 = form.getvalue('clump_r2', '')
	clump_kb = form.getvalue('clump_kb', '')

	##############################################################################
	############################## WRITING REPORT ###########################
	##############################################################################
	
	################## Creating report_object ##################
	report_obj = Report(filebasename=file_prefix_web_tmp)

	################## OPTIONS ##################
	report_news =	{'required_matched_SNPs':N_sample_sets, #*** OBS: different name!
					'exclude_input_SNPs':exclude_input_SNPs,
					'exclude_HLA_SNPs':exclude_HLA_SNPs,
					'annotate_matched_SNPs':set_file,
					'annotate_input_SNPs':annotate
					}
	report_obj.report['options'].update(report_news)

	################## LOCI DEFINITION ##################
	report_news =	{'distance_type':distance_type,
					'distance_cutoff':distance_cutoff
					}
	report_obj.report['loci_definition'].update(report_news)

	################## MATCHING CRITERIA ##################
	report_news =	{'max_freq_deviation':max_freq_deviation,
					'max_distance_deviation':max_distance_deviation,
					'max_genes_count_deviation':max_genes_count_deviation,
					'max_ld_buddy_count_deviation':max_ld_buddy_count_deviation, # NEW
					'ld_buddy_cutoff':ld_buddy_cutoff # NEW 09/11/2014
					}
	report_obj.report['match_criteria'].update(report_news)
	
	################## CLUMPING ##################
	report_news =	{'clump':clump,
					'clump_r2':clump_r2,
					'clump_kb':clump_kb
					}
	report_obj.report['clumping'].update(report_news)
	

	################## WEB ##################
	report_news =	{'session_id':session_id,
						'job_name':job_name,
						'email_address':email_address
						}
	report_obj.report['web'].update(report_news)

	################## Writing report ##################
	report_obj.write_json_report()

	##############################################################################
	############################## GENERATING COMMANDS ###########################
	##############################################################################

	script2call = "/cvar/jhlab/snpsnap/snpsnap/snpsnap_query.py"	
	## this is the base for all the sub options that can be added to SNPsnap
	cmd_base = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} --web {file_prefix_web_tmp}".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff, file_prefix_web_tmp=file_prefix_web_tmp)
	## REMEMBER: cmd_base is modfied 'globally', so all addon's MUST be true for the rest of commands
	##### Adding more stuff to cmd_base ####
	if exclude_HLA_SNPs:
		option = "--exclude_HLA_SNPs"
		cmd_base = "{base} {addon}".format(base=cmd_base, addon=option) # or #cmd_base = " ".join([cmd_base, option])
	###### INTERNAL LOGGER SWITCH ###
	logger = True # 'False' or 'True' ---> log_file will be written to /local/data/web_logs
	if logger:
		file_path = "/local/data/web_logs"+"/"+session_id ### OBS - HARD CODED PATH!!
		option = "--log_file {file_path}".format(file_path=file_path) # OBS: the log filename will be something like 'logger.SESSIONID_match.log' or 'logger.SESSIONID_annotate.log'
		cmd_base = "{base} {addon}".format(base=cmd_base, addon=option)
	else:
		option = "--NoLogger"
		cmd_base = "{base} {addon}".format(base=cmd_base, addon=option) # or #cmd_base = " ".join([cmd_base, option])
	#################################

	####### ANNOTATE COMMAND #######
	cmd_annotate = '' # OBS: important that default value evaluates to false in Bool context
	if annotate:
		subcommand = "annotate"
		cmd_annotate = "{base} {addon}".format(base=cmd_base, addon=subcommand)

	####### MATCH COMMAND #######
	cmd_match = "{base} match --N_sample_sets {N_sample_sets} --ld_buddy_cutoff {ld_buddy_cutoff} --max_freq_deviation {max_freq_deviation} --max_distance_deviation {max_distance_deviation} --max_genes_count_deviation {max_genes_count_deviation} --max_ld_buddy_count_deviation {max_ld_buddy_count_deviation}".format(base=cmd_base, N_sample_sets=N_sample_sets, ld_buddy_cutoff=ld_buddy_cutoff, max_freq_deviation=max_freq_deviation, max_distance_deviation=max_distance_deviation, max_genes_count_deviation=max_genes_count_deviation, max_ld_buddy_count_deviation=max_ld_buddy_count_deviation)
	if set_file:
		option = "--set_file"
		cmd_match = "{base} {addon}".format(base=cmd_match, addon=option)
	if exclude_input_SNPs: 
		option = "--exclude_input_SNPs"
		cmd_match = "{base} {addon}".format(base=cmd_match, addon=option)

	####### CLUMP COMMAND #######
	cmd_clump = '' # OBS: important that default value evaluates to false in Bool context
	if clump:
		subcommand = "clump --clump_r2 {clump_r2} --clump_kb {clump_kb}".format(clump_r2=clump_r2, clump_kb=clump_kb)
		cmd_clump = "{base} {addon}".format(base=cmd_base, addon=subcommand)




	###################### FORK'ING ##################################
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
	with open(os.devnull, "w") as fnull: # same as open('/dev/null', 'w')
		script2call = "/cvar/jhlab/snpsnap/snpsnap/launchApp.py"
		cmd_launch = [script2call,
					'--session_id', session_id,
					'--email_address', email_address,
					'--job_name', job_name,
					'--cmd_annotate', cmd_annotate,
					'--cmd_match', cmd_match,
					'--cmd_clump', cmd_clump
					]
		#cmd_formatted = '{program} {p_session_id} "{session_id}" {p_email_address} "{email_address}" {p_job_name} "{job_name}" {p_cmd_annotate} "{cmd_annotate}" {p_cmd_match} "{cmd_match}"'.format()
		#cmd_formatted = '{} {} "{}" {} "{}" {} "{}" {} "{}" {} "{}"'.format(*cmd_launch) # before --clump
		cmd_formatted = '{} {} "{}" {} "{}" {} "{}" {} "{}" {} "{}" {} "{}"'.format(*cmd_launch)
		sys.stderr.write("called command: %s\n" % cmd_launch)
		sys.stderr.write("FORMATTED called command: %s\n" % cmd_formatted)
		p = subprocess.Popen(cmd_launch, stdout = fnull, stderr = subprocess.STDOUT)
		sys.stderr.write("process PID is %s\n" % p.pid)




	print "Content-Type: text/html"
	print

	print snpsnap_header

	## SEE: http://stackoverflow.com/questions/10721244/ajax-posting-to-python-cgi
	## IMPORTANT: http://stackoverflow.com/questions/9540957/jquery-ajax-loop-to-refresh-jqueryui-progressbar

	###################################### BODY - START ######################################
	print "<body>"
	###############################################################################################


	###################################### HEADER OF PAGE ######################################
	print snpsnap_match_nav
	###############################################################################################


	print "<h2 class='text-center'>SNPsnap is now matching your SNPs</h2>"

	#print "<p>Your session ID is: %s</p>" % session_id
	print "<p> An email will be sent to <strong>%s</strong> when the job is completed.<br>You will be able to download the results as soon your job finish. You can download the results from the bottom of this page or via the below link.</p>" % email_address
	print """<p class='text-muted'><i>If you browse back you will not be able to retrieve this site again.<br>
	However, you will still receive an email notification about your job completion.
	</i></p>"""
	
	### Display results URL as "raw text"
	print "<p>Results URL: <code>{url}</code></p>".format(url="http://www.broadinstitute.org/mpg/snpsnap/"+url_results)

	### Give the user a warning about the instability of SNPsnap emailing server
	print """
	<p class="text-danger">SNPsnap have been experiencing issues with the email notification server. 
	We encourage all users to copy the above result download link and store it temporarily. 
	This will enable users to fetch the results even if the email does not reach the user's inbox.
	<br>
	Typical jobs finish within 10-60 minutes after which the download link becomes active and you can download the results.
	</p>
	"""

	################ PARSING SESSION ID ##################
	print "<input type='hidden' id='session_id' value='%s'>" % session_id
	print "<input type='hidden' id='annotate' value='%s'>" % annotate
	print "<input type='hidden' id='set_file' value='%s'>" % set_file
	print "<input type='hidden' id='clump' value='%s'>" % clump
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


	################## PANEL: PROGRESS ##################

	### class="text-primary"
	str_bar_match = """
	<div class='row' id='row_progress_match'>
		<div class='col-xs-3'>
			<p><strong>Matching SNPs</strong></p>
		</div>
		<div class='col-xs-2'>
			<p class="text-info"></p>
		</div>
		<div class='col-xs-7'>
			<div class='error_description'></div> <!-- PLACEHOLDER FOR AN ERROR Message -->
			<div class='progress progress-striped active' id='progress_bar_match'>
				<div class='progress-bar' style='width: 0%'></div>
			</div>
		</div>
	</div>
	"""

	str_bar_bias = """
	<div class='row' id='row_progress_bias' style='display:none;'>
		<div class='col-xs-3'>
			<p><strong>Calculating match bias</strong></p>
		</div>
		<div class='col-xs-2'>
			<p class="text-info"></p>
		</div>
		<div class='col-xs-7'>
			<div class='error_description'></div> <!-- PLACEHOLDER FOR AN ERROR Message -->
			<div class='progress progress-striped active' id='progress_bar_bias'>
				<div class='progress-bar' style='width: 0%'></div>
			</div>
		</div>
	</div>""" # NOTE THAT bias is HIDDEN BY DEFAUL! (style='display:none;')

	str_bar_set_file = """
	<div class='row' id='row_progress_set_file'>
		<div class='col-xs-3'>
			<p><strong>Annotating Matched SNPs</strong></p>
		</div>
		<div class='col-xs-2'>
			<p class="text-info"></p>
		</div>
		<div class='col-xs-7'>
			<div class='error_description'></div> <!-- PLACEHOLDER FOR AN ERROR Message -->
			<div class='progress progress-striped active' id='progress_bar_set_file'>
				<div class='progress-bar' style='width: 0%'></div>
			</div>
		</div>
	</div>
	"""	


	str_bar_annotate = """
	<div class='row' id='row_progress_annotate'>
		<div class='col-xs-3'>
			<p><strong>Annotating Inputs SNPs</strong></p>
		</div>
		<div class='col-xs-2'>
			<p class="text-info"></p>
		</div>
		<div class='col-xs-7'>
			<div class='error_description'></div> <!-- PLACEHOLDER FOR AN ERROR Message -->
			<div class='progress progress-striped active' id='progress_bar_annotate'>
				<div class='progress-bar' style='width: 0%'></div>
			</div>
		</div>
	</div>
	"""	

	str_bar_clump = """
	<div class='row' id='row_progress_clump'>
		<div class='col-xs-3'>
			<p><strong>Clumping Input SNPs</strong></p>
		</div>
		<div class='col-xs-2'>
			<p class="text-info"></p>
		</div>
		<div class='col-xs-7'>
			<div class='error_description'></div> <!-- PLACEHOLDER FOR AN ERROR Message -->
			<div class='progress progress-striped active' id='progress_bar_clump'>
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
			{bias}
			{set_file}
			{annotate}
			{clump}
		  </div>
		</div>
	  </div>
	""".format(match=str_bar_match, bias=str_bar_bias, set_file=str_bar_set_file, annotate=str_bar_annotate, clump=str_bar_clump)


	################## PANEL: SNPSNAP SCORE ##################
	#<div class="panel-body" id='snpsnap_report'>
	print """
	  <div class="panel panel-default" id='panel_snpsnap_score'>
		<div class="panel-heading">
		  <h4 class="panel-title">
			<a data-toggle="collapse" data-target="#collapse_snpsnap_score" href="#collapse_snpsnap_score" onClick="return false;">
			  SNPsnap Scores
			</a>
		  </h4>
		</div>
		<div id="collapse_snpsnap_score" class="panel-collapse collapse in"> 
		  <div class="panel-body">
		  </div>
		</div>
	  </div>
	"""

	################## PANEL: INPUT TO MATCHED RATIO ##################
	print """
	  <div class="panel panel-default" id='panel_input_to_matched_ratio'>
		<div class="panel-heading">
		  <h4 class="panel-title">
			<a data-toggle="collapse" data-target="#collapse_input_to_matched_ratio" href="#collapse_input_to_matched_ratio" onClick="return false;">
			  Matching Bias
			</a>
		  </h4>
		</div>
		<div id="collapse_input_to_matched_ratio" class="panel-collapse collapse in"> 
		  <div class="panel-body">
		  </div>
		</div>
	  </div>
	"""

	################## PANEL: INPUT LOCI INDEPENDENCE ##################
	print """
	  <div class="panel panel-default" id='panel_input_loci_independence'>
		<div class="panel-heading">
		  <h4 class="panel-title">
			<a data-toggle="collapse" data-target="#collapse_input_loci_independence" href="#collapse_input_loci_independence" onClick="return false;">
			  Input Loci Independence
			</a>
		  </h4>
		</div>
		<div id="collapse_input_loci_independence" class="panel-collapse collapse in"> 
		  <div class="panel-body">
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
	str_result_botton = "<a href='{url}' class='btn btn-default btn-success'><span class='glyphicon glyphicon-download'></span> Download Results</a>".format(url=url_results) # verison4 - works for bootstrap 3!

	print """
	  <div class="panel panel-default" id='panel_results'>
		<div class="panel-heading">
		  <h4 class="panel-title">
			<a data-toggle="collapse" data-target="#collapse_results" href="#collapse_results" onClick="return false;">
			  Download
			</a>
		  </h4>
		</div>
		<div id="collapse_results" class="panel-collapse collapse in"> 
		  <div class="panel-body">
		  	  {results}
			  <div style="margin-bottom:5px; margin-top:5px;">
			  	<p class="text-muted">All files are tab delimited with the .txt file extension and can be directly imported to Excel.</p>
			  	<p class="text-muted">You may print or save this result page for later reference. Note that the file <span class="code_files">snpsnap_summary.txt</span> contains all the information shown on this page.</p>
			  </div>
		  </div>
		</div>
	  </div>
	""".format(results=str_result_botton)


	###################################### PANEL GROUP - END ######################################
	print '</div>'
	###############################################################################################


	###################################### FOOTER ######################################

	print snpsnap_footer
	###############################################################################################


	###################################### CONTAINER - END ######################################
	print "</div>" 
	###############################################################################################


	print "</body>"
	print "</html>"


def html_error(e):
	(error_type, error_msg) = e.args
	print "Content-Type: text/html"
	print

	print snpsnap_header
	print "<body>" # BODY - START 
	print snpsnap_match_nav # HEADER OF PAGE

	print """
	<h1 class='text-error'>Invalid formular</h1>
	
	<div style='width:100%;'>
	<table class="table table-hover table-condensed">
	  <thead>
	    <tr>
	      <th>Error type</th>
	      <th>Message</th>
	    </tr>
	  </thead>
	  <tbody>
	    <tr>
	      <td>{e_type}</td>
	      <td>{e_msg}</td>
	    </tr>
	  </tbody>
	 </table>
	</div>
	""".format(e_type=error_type, e_msg=error_msg)

	# for exceptions see: https://docs.python.org/2/tutorial/errors.html

	print snpsnap_footer # FOOTER
	print "</div>" # CONTAINER - END

	print "</body>"
	print "</html>"


if __name__ == "__main__":
	try:
		run()
	except FormValidationError as e:
		html_error(e)
