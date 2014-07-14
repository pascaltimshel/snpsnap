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
path_web_tmp_output = '/local/data/web_tmp' # NEW

file_report = "{base}/{sid}_{type}.{ext}".format(base=path_web_tmp_output, sid=session_id, type='report', ext='json')
# e.g. 2ede5955021a10cb0e1a13882be520eb_report.json

try:
	report_obj = None ## Needed for correct variable scope
	with open(file_report, 'r') as json_data:
		report_obj = json.load(json_data)

	#report_obj.report['mean_input_to_match_ratio'] ---> has keys like:
	#'ratio_freq_bin'
	#'ratio_gene_count'
	#'ratio_dist_nearest_gene_snpsnap'
	#'ratio_friends_ld05' # <--- OBS this key name is variable!


	################ GETTING THE ACTUAL VALUES OF THE REPORT ##################
	# OBS: formatting number. You can format any number as float, but you cannot format floats as int (e.g. {:d})
	fmt_mean_input_freq_bin = "{:.2f}".format( report_obj['mean_input_to_match_ratio']['mean_input_freq_bin'] ) 
	fmt_mean_input_gene_count = "{:.2f}".format( report_obj['mean_input_to_match_ratio']['mean_input_gene_count'] ) 
	fmt_mean_input_dist_nearest_gene_snpsnap = "{:.2f}".format( report_obj['mean_input_to_match_ratio']['mean_input_dist_nearest_gene_snpsnap'] ) 

	fmt_mean_matched_freq_bin = "{:.2f}".format( report_obj['mean_input_to_match_ratio']['mean_matched_freq_bin'] ) 
	fmt_mean_matched_gene_count = "{:.2f}".format( report_obj['mean_input_to_match_ratio']['mean_matched_gene_count'] ) 
	fmt_mean_matched_dist_nearest_gene_snpsnap = "{:.2f}".format( report_obj['mean_input_to_match_ratio']['mean_matched_dist_nearest_gene_snpsnap'] ) 

	fmt_ratio_freq_bin = "{:.2f}".format( report_obj['mean_input_to_match_ratio']['ratio_freq_bin'] ) 
	fmt_ratio_gene_count = "{:.2f}".format( report_obj['mean_input_to_match_ratio']['ratio_gene_count'] ) 
	fmt_ratio_dist_nearest_gene_snpsnap = "{:.2f}".format( report_obj['mean_input_to_match_ratio']['ratio_dist_nearest_gene_snpsnap'] ) 
	
	fmt_mean_input_friends = None
	fmt_mean_matched_friends = None
	fmt_ratio_friends = None
	for key in report_obj['mean_input_to_match_ratio'].keys():
		if 'mean_input_friends' in key:
			fmt_mean_input_friends = "{:.2f}".format( report_obj['mean_input_to_match_ratio'][key] )
		if 'mean_matched_friends' in key:
			fmt_mean_matched_friends = "{:.2f}".format( report_obj['mean_input_to_match_ratio'][key] )
		if 'ratio_friends' in key:
			fmt_ratio_friends = "{:.2f}".format( report_obj['mean_input_to_match_ratio'][key] )
	## Checking that all 'friends' are set
	if not (fmt_mean_input_friends and fmt_mean_matched_friends and fmt_ratio_friends): # if the variables EVALUATE TO FALSE
		raise Exception("statement 'if 'ratio_friends' in key:' did not evaluate to true")

	#Description of how to control column width of tables of bootstrap:
	# --->http://ericsaupe.com/custom-column-widths-in-bootstrap-tables/
	html2parse = """
	  <div style='width:100%;'>
	  <table class='table table-hover'>
	    <thead>
	      <tr>
	        <th class="col-xs-3 text-left" style='font-size:125%;'>Genetic property</th>
	        <th class="col-xs-2 text-left" style='font-size:125%;'>Mean input</th>
	        <th class="col-xs-2 text-left" style='font-size:125%;'>Mean matched</th>
	        <th class="col-xs-2 text-left" style='font-size:125%;'>Ratio (%)*</th>
	      </tr>
	    </thead>
	    <tbody>
	      <tr>
	        <th>Minor Allele Frequency</th>
	        <td>{fmt_mean_input_freq_bin}</td>
	        <td>{fmt_mean_matched_freq_bin}</td>
	        <td>{fmt_ratio_freq_bin}%</td>
	      </tr>
	      <tr>
	        <th>Gene density</th>
	        <td>{fmt_mean_input_gene_count}</td>
	        <td>{fmt_mean_matched_gene_count}</td>
	        <td>{fmt_ratio_gene_count}%</td>
	      </tr>
	      <tr>
	        <th>Distance to nearest gene</th>
	        <td>{fmt_mean_input_dist_nearest_gene_snpsnap}</td>
	        <td>{fmt_mean_matched_dist_nearest_gene_snpsnap}</td>
	        <td>{fmt_ratio_dist_nearest_gene_snpsnap}%</td>
	      </tr>
	      <tr>
	        <th>LD buddies</th>
	        <td>{fmt_mean_input_friends}</td>
	        <td>{fmt_mean_matched_friends}</td>
	        <td>{fmt_ratio_friends}%</td>
	      </tr>
	    </tbody>
	  </table>

	<p class='text-muted'>*Ratio defined as <i>Mean input</i>/<i>Mean matched</i>. <br>
	Requesting a large number of SNPs may lead to a systematic difference between genetic properties of input and matched SNPs indicated by a ratio deviating from 100%.
	<br>
	In order to obtain a ratio close to 100%, lessen the number of requested SNPs or tighten the matching criteria.
	<br>
	See the <a href='documentation.html#snpsnap_matching_bias' target='_blank'>documentation</a> for more information.</p> 
	</div>
	""".format(
		fmt_mean_input_freq_bin=fmt_mean_input_freq_bin,
		fmt_mean_matched_freq_bin=fmt_mean_matched_freq_bin,
		fmt_ratio_freq_bin=fmt_ratio_freq_bin,
		fmt_mean_input_gene_count=fmt_mean_input_gene_count,
		fmt_mean_matched_gene_count=fmt_mean_matched_gene_count,
		fmt_ratio_gene_count=fmt_ratio_gene_count,
		fmt_mean_input_dist_nearest_gene_snpsnap=fmt_mean_input_dist_nearest_gene_snpsnap,
		fmt_mean_matched_dist_nearest_gene_snpsnap=fmt_mean_matched_dist_nearest_gene_snpsnap,
		fmt_ratio_dist_nearest_gene_snpsnap=fmt_ratio_dist_nearest_gene_snpsnap,
		fmt_mean_input_friends=fmt_mean_input_friends,
		fmt_mean_matched_friends=fmt_mean_matched_friends,
		fmt_ratio_friends=fmt_ratio_friends
		)


	print "Content-Type: text/html"
	print ""
	print html2parse

except Exception as e: # DIRTY: but properly the file(s) does not exists
	html2parse = """
	<p class='text-danger text-center'> Sorry, we could not generate the report. 
	Please report this bug to the <a href='contact.html'>SNPsnap team</a>.</p> 
	"""
	#%s""" % e
	print "Content-Type: text/html"
	print ""
	print html2parse


