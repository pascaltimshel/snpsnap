#!/bin/env python

# Import modules for CGI handling 
import cgi, cgitb
import json

import time
import datetime

# Create instance of FieldStorage 
form = cgi.FieldStorage() 
session_id = form.getvalue('session_id', '')

# FILE PATH
path_web_tmp_output = '/local/data/web_tmp' 

file_report = "{base}/{sid}_{file_type}_{subcommand}.{ext}".format(base=path_web_tmp_output, sid=session_id, file_type='report', subcommand='clump', ext='json') # NEW 09/11/2014
# e.g. 2ede5955021a10cb0e1a13882be520eb_report_match.json

try:
	report_obj = None ## Needed for correct variable scope
	with open(file_report, 'r') as json_data:
		report_obj = json.load(json_data)

	### KEYS in report_obj for 'clumping'
	n_input_loci = report_obj["clumping"]["n_input_loci"] # --> integer
	n_clumped_loci = report_obj["clumping"]["n_clumped_loci"] #  --> integer
	user_snps_are_all_independent_loci = report_obj["clumping"]["user_snps_are_all_independent_loci"] # --> boolean value (flag)

	### Generating 'recommentation' string to the user
	str_explanation = ''
	str_header = ''
	if user_snps_are_all_independent_loci:
		# str_header = "<span class='text-success'>Your input SNPs are independent</span>"
		str_header = "<span class='bg-success'>Your input SNPs are independent</span>" # also try "bg-info" (light blue)
	else:
		str_header = "<span class='bg-danger'>Your input SNPs are <i>not</i> independent</span>"
		str_explanation = "<span class='text-danger'>The number of independent loci is less than the number input SNPs. For intended usage of SNPsnap, input SNPs should be independent because SNPsnap is not accounting for the correlation between input SNPs. Please consider clumping your input SNPs to derive independent loci.</span>"


	#Contextual colors: <p class="text-danger">...</p>
	#Contextual backgrounds: <p class="bg-danger">...</p>

	#<strong>Input loci independence</strong>: {str_explanation}
	# <h3>Input loci independence</h3>
	# <p class="text-center">{str_explanation}</p>

	#Description of how to control column width of tables of bootstrap:
	# --->http://ericsaupe.com/custom-column-widths-in-bootstrap-tables/
	html2parse = """
	<div style='width:60%;'>
		  <table class='table table-hover'>
		    <thead>
		      <tr>
		        <th class="col-xs-3 text-left" style='font-size:125%;'></th>
		        <th class="col-xs-2 text-left" style='font-size:125%;'>Number of Loci</th>
		      </tr>
		    </thead>
		    <tbody>
		      <tr>
		        <th>Input Loci*</th>
		        <td>{n_input_loci}</td>
		      </tr>
		      <tr>
		        <th>Clumped Loci**</th>
		        <td>{n_clumped_loci}</td>
		      </tr>
		    </tbody>
		  </table>
	</div>

	<p class='text-muted'>
		*Number of <i>valid</i> user input SNPs found in SNPsnap's SNP database.<br>
		**Number of loci after clumping based on user-specified parameters.
	</p>

	<h4>{str_header}</h4>
	<p>{str_explanation}</p>

	<p class='text-muted'>
		See the file <span class="code_files">input_snps_clumped.txt</span> for details on the clumped loci.
	</p>
	""".format(
		n_input_loci=n_input_loci,
		n_clumped_loci=n_clumped_loci,
		str_header=str_header,
		str_explanation=str_explanation
		)

	print "Content-Type: text/html"
	print ""
	print html2parse

except Exception as e: # DIRTY: but properly the file(s) does not exists
	import traceback  # REMEMBER TO IMPORT tracback

	## FOR DEBUGGING
	# with open('/local/data/web_tmp/zzzzzzz_report_clump_tmp.tmp', 'w') as f:
	# 	f.write("%s\n" % e)
	# 	f.write(file_report+"\n")
	# 	f.write( "<p>Class: %s ||| Docstring: %s ||| Message: %s</p>\n" % ( e.__class__, e.__doc__, e.message) )
	# 	f.write( "<p>Class: %s ||| Docstring: %s ||| Message: %s</p>\n" % ( type(e.__class__), type(e.__doc__), type(e.message)) )
	# 	f.write( "<p>Class: %s ||| Docstring: %s ||| Message: %s</p>\n" % ( cgi.escape(str(e.__class__), True), cgi.escape(e.__doc__, True), cgi.escape(e.message, True) ) )
	# 	f.write( traceback.format_exc() + "\n" ) #traceback.format_exc() --> like traceback.print_exc() but returns a string instead of printing to a file.
		

	html2parse = """
	<p class='text-danger text-center'> Sorry, we could not generate the report. 
	Please report this bug to the <a href='contact.html'>SNPsnap team</a>.</p> 
	"""
	### DEBUGGING MESSAGE #1 - works ok, pretty clean, less informative, no paths:
	#html2parse = html2parse + "<p>Class: %s<br>Docstring: %s<br>Message: %s</p>" % ( cgi.escape(str(e.__class__)), cgi.escape(e.__doc__), cgi.escape(e.message) )
	### DEBUGGING MESSAGE #2 - RECOMMENDED, TRACEBACK informative, (shows paths and line numbers):
	#html2parse = html2parse + "%s</p>" % traceback.format_exc()
	print "Content-Type: text/html"
	print ""
	print html2parse

