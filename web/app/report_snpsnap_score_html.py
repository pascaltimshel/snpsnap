#!/bin/env python

# Import modules for CGI handling 
import cgi, cgitb
import json

import time
import datetime

import sys # only tmp use

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

session_id = form.getvalue('session_id', '')

#path_web_tmp_output = '/cvar/jhlab/snpsnap/web_tmp'
path_web_tmp_output = '/local/data/web_tmp' # NEW

file_report = "{base}/{sid}_{type}.{ext}".format(base=path_web_tmp_output, sid=session_id, type='report', ext='json')
# e.g. 2ede5955021a10cb0e1a13882be520eb_report.json

try:
	## TODO: make try: execpt: block
	report_obj = None ## Needed for correct variable scope
	with open(file_report, 'r') as json_data:
		report_obj = json.load(json_data)

	## This is what the json file contains
	# "insufficient_rating":insufficient_rating,
	# "insufficient_matches_pct":insufficient_matches_pct, 
	# "insufficient_N":insufficient_N,
	# "N_snps":N_snps,
	# 'insufficient_scale_str':insufficient_scale_str,
	# "match_size_rating":match_size_rating,
	# "match_size_median_pct":match_size_median_pct,
	# "match_size_median":match_size_median,
	# "N_sample_sets":N_sample_sets,
	# 'match_size_scale_str':match_size_scale_str

	## NEW
	# "insufficient_rating":insufficient_rating,
	# "insufficient_matches_pct":insufficient_matches_pct, 
	# "insufficient_matches":insufficient_matches,
	# "match_size_rating":match_size_rating,
	# "match_size_median_pct":match_size_median_pct,
	# "match_size_median":match_size_median

	#insufficient_rating_img = None
	#match_size_rating_img = None
	img_path = {
		'very good': 'img/rating_v3/rating_very_good.png',
		'good': 'img/rating_v3/rating_good.png',
		'ok': 'img/rating_v3/rating_ok.png',
		'poor': 'img/rating_v3/rating_poor.png',
		'very poor': 'img/rating_v3/rating_very_poor.png',
	}

	rating_img = {} # this dict will contain two keys
	for report_param in ['insufficient_rating', 'match_size_rating']:
		for rating in img_path.keys():
			if report_obj['report'][report_param] == rating:
			#if report_obj[report_param] == rating:
				rating_img[report_param] = img_path[rating]
		# if report_obj[key] == 'very good':
		# 	rating_img[key] = img_path['']


	################ GETTING THE ACTUAL VALUES OF THE REPORT ##################
	fmt_value_insufficient = "{:.2f}".format( report_obj['report']['insufficient_matches_pct'] ) # OBS: formatting number. You can format any number as float, but you cannot format floats as int (e.g. {:d})
	fmt_value_match_size = "{:.2f}".format( report_obj['report']['match_size_median_pct'] ) # OBS: formatting number. You can format any number as float, but you cannot format floats as int (e.g. {:d})

	###### 07/10/2014 - MAY BE DELETED ######
	# <th class="col-xs-3"><p class="text-left" style='font-size:125%;'>SNPsnap score</p></th>
	# <th class="col-xs-2"><p class="text-left" style='font-size:125%;'>Value</p></th>
	# <th class="col-xs-7"><p class="text-center" style='font-size:125%;'>Rating</p></th>

	#Description of how to control column width of tables of bootstrap:
	# --->http://ericsaupe.com/custom-column-widths-in-bootstrap-tables/
	html2parse = """
	  <div style='width:100%;'>
	  <table class='table table-hover'>
	    <thead>
	      <tr>
	        <th class="col-xs-3 text-left" style='font-size:125%;'>SNPsnap score</th>
	        <th class="col-xs-2 text-left" style='font-size:125%;'>Value</th>
	        <th class="col-xs-7 text-center" style='font-size:125%;'>Rating</th>
	      </tr>
	    </thead>
	    <tbody>
	      <tr>
	        <th>Insufficient-matches</th>
	        <td>{fmt_value_insufficient}%</td>
	        <td><img src='{img_insufficient_rating}' style="max-width:420px; max-height:21px" alt="SNPsnap score image"></td>
	      </tr>
	      <tr>
	        <th>Match-size</th>
	        <td>{fmt_value_match_size}%</td>
	        <td><img src='{img_match_size_rating}' style="max-width:420px; max-height:21px" alt="SNPsnap score image"></td>
	      </tr>
	    </tbody>
	  </table>

	<p class='text-muted'>You may safely ignore the <i>Match-size</i> rating if the <i>Insufficient-matches</i> rating is better than <q>Ok</q>. 
	See the <a href='documentation.html#snpsnap_score' target='_blank'>documentation</a> for more information.</p> 
	</div>
	""".format(
		img_insufficient_rating=rating_img['insufficient_rating'],
		fmt_value_insufficient=fmt_value_insufficient,
		img_match_size_rating=rating_img['match_size_rating'],
		fmt_value_match_size=fmt_value_match_size
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


	###### BEFORE 07/05/2014: may be deleted ##########
	# html2parse = """
	#   <div style='width:100%;'>
	#   <table class='table table-hover'>
	#     <thead>
	#       <tr>
	#         <th><p class="text-danger text-left" style='font-size:125%;'>Evaluation type</p></th>
	#         <th><p class="text-danger text-center" style='font-size:125%;'>Rating</p></th>
	#       </tr>
	#     </thead>
	#     <tbody>
	#       <tr>
	#         <th>Insufficient Matches</th>
	#         <td><img src='{img_insufficient_rating}' class="img-responsive" alt="Responsive image"></td>
	#       </tr>
	#       <tr>
	#         <th>Match Size</th>
	#         <td><img src='{img_match_size_rating}' class="img-responsive" alt="Responsive image"></td>
	#       </tr>
	#     </tbody>
	#   </table>

	# <p class='text-muted'>You may safely ignore the <i>Match Size</i> rating if the <i>Insufficient Matches</i> rating is better than <q>Ok</q>. 
	# See the <a href='documentation.html'>documentation</a> for more information.</p> 
	# </div>
	# """.format(
	# 	img_insufficient_rating=rating_img['insufficient_rating'],
	# 	img_match_size_rating=rating_img['match_size_rating']
	# 	)

