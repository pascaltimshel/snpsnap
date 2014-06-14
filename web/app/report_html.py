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

path_tmp_output = '/cvar/jhlab/snpsnap/web_tmp'
file_report = "{base}/{sid}_{type}.{ext}".format(base=path_tmp_output, sid=session_id, type='report', ext='json')
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
		'very good': '/img/rating/rating_very_good.png',
		'good': '/img/rating/rating_good.png',
		'ok': '/img/rating/rating_ok.png',
		'poor': '/img/rating/rating_poor.png',
		'very poor': '/img/rating/rating_very_poor.png',
	}

	rating_img = {} # this dict will contain two keys
	for report_param in ['insufficient_rating', 'match_size_rating']:
		for rating in img_path.keys():
			if report_obj['report'][report_param] == rating:
			#if report_obj[report_param] == rating:
				rating_img[report_param] = img_path[rating]
		# if report_obj[key] == 'very good':
		# 	rating_img[key] = img_path['']



	html2parse = """
	  <div style='width:100%;'>
	  <table class='table table-hover'>
	    <thead>
	      <tr>
	        <th><p class="text-danger text-left" style='font-size:125%;'>Evaluation type</p></th>
	        <th><p class="text-danger text-center" style='font-size:125%;'>Rating</p></th>
	      </tr>
	    </thead>
	    <tbody>
	      <tr>
	        <th>Insufficient Matches</th>
	        <td><img src='{img_insufficient_rating}' class="img-responsive" alt="Responsive image"></td>
	      </tr>
	      <tr>
	        <th>Match Size</th>
	        <td><img src='{img_match_size_rating}' class="img-responsive" alt="Responsive image"></td>
	      </tr>
	    </tbody>
	  </table>

	<p class='text-muted'>You may safely ignore the <i>Match Size</i> rating if the <i>Insufficient Matches</i> rating is better than <q>Ok</q>. 
	See the <a href='#'>docs</a> for more information.</p> 
	</div>
	""".format(
		img_insufficient_rating=rating_img['insufficient_rating'],
		img_match_size_rating=rating_img['match_size_rating']
		)

	print "Content-Type: text/html"
	print ""
	print html2parse

except Exception as e: # DIRTY: but properly the file(s) does not exists
	html2parse = """
	<p class='text-danger text-center'> Sorry, we could not generate the report. 
	Please report this bug to the <a href='#'>webmaster</a>.</p> 
	"""
	#%s""" % e
	print "Content-Type: text/html"
	print ""
	print html2parse

