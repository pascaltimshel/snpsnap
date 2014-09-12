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

	################ GETTING THE ACTUAL VALUES OF THE REPORT ##################
	# OBS: formatting number. You can format any number as float, but you cannot format floats as int (e.g. {:d})
	fmt_mean_input_freq_bin = "{:.2f}".format( report_obj['mean_input_to_match_ratio']['mean_input_freq_bin'] ) 
	fmt_mean_input_gene_count = "{:.2f}".format( report_obj['mean_input_to_match_ratio']['mean_input_gene_count'] ) 
	fmt_mean_input_dist_nearest_gene_snpsnap = "{:.2f}".format( report_obj['mean_input_to_match_ratio']['mean_input_dist_nearest_gene_snpsnap'] ) 


	### Generating 'recommentation' string to the user
	if n_user_input_snps == n_clumped_loci:
		str_independence = "<span class='text-succes'>Your input SNPs are independent</span>"
	else:
		str_independence = "<span class='text-danger'>The number of independent loci is less than the number input SNPs. For intended usage of SNPsnap, input SNPs should be independent becuase SNPsnap is not accounting for the correlation between input SNPs. Please consider clumping your input SNPs to form independent loci.</span>"

	#Contextual colors: <p class="text-danger">...</p>
	#Contextual backgrounds: <p class="bg-danger">...</p>


	#Description of how to control column width of tables of bootstrap:
	# --->http://ericsaupe.com/custom-column-widths-in-bootstrap-tables/
	html2parse = """
	  <div style='width:100%;'>
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
		        <td>{SOMETHING}</td>
		      </tr>
		      <tr>
		        <th>Clumped Loci**</th>
		        <td>{SOMETHING}</td>
		      </tr>
		    </tbody>
		  </table>

		<p class='text-muted'>
			*Number of <i>valid</i> user input SNPs found in SNPsnap's SNP database.<br>
			**Number of loci after clumping based on user-specified parameters.
		</p>

		<p>
			<strong>Input loci independence</strong>: {str_independence}
		</p>

		<p>
			Note that the file <span class="code_files">input_snps_clumped.txt</span> contains all the information shown on this page
		</p>

	</div>
	""".format(
		SOMETHING=SOMETHING,
		SOMETHING=SOMETHING,
		str_independence=str_independence
		)

	print "Content-Type: text/html"
	print ""
	print html2parse

except Exception as e: # DIRTY: but properly the file(s) does not exists
	html2parse = """
	<p class='text-danger text-center'> Sorry, we could not generate the report. 
	Please report this bug to the <a href='contact.html'>SNPsnap team</a>.</p> 
	"""
	html2parse = html2parse + "<p>%s</p>" % e
	print "Content-Type: text/html"
	print ""
	print html2parse


