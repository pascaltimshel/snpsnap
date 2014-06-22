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
set_file = form.getvalue('set_file', '')
annotate = form.getvalue('annotate', '')

path_web_tmp_output = '/cvar/jhlab/snpsnap/web_tmp'
#path_web_tmp_output = '/local/data/web_tmp'

file_status_match = "{base}/{sid}_{type}.{ext}".format(base=path_web_tmp_output, sid=session_id, type='status_match', ext='json')
file_status_annotate = "{base}/{sid}_{type}.{ext}".format(base=path_web_tmp_output, sid=session_id, type='status_annotate', ext='json')
# e.g. 2ede5955021a10cb0e1a13882be520eb_status_match.json


### Function for printing out args to Apache log file at /etc/httpd/logs/error_log
# def print_args():
# 	for key in sorted(form.keys()):
# 		#if key == 'snplist_fileupload': continue
# 		sys.stderr.write( "%s: %s<br/>" % (key, form.getvalue(key)) + "\n" )

# print_args()

try:
	status_obj = None ## Needed for correct variable scope
	with open(file_status_match, 'r') as json_data:
		status_obj = json.load(json_data)

	## ***OBS: HACK
	if not set_file:
		status_obj['set_file'] = {'pct_complete':0, 'status':'complete'}
		# This enables me to set the 'overall' completion status

	if annotate:
		with open(file_status_annotate, 'r') as json_data:
			tmp = json.load(json_data)
			status_obj['annotate'] = tmp['annotate'] ## OBS: key must be in sync with snpsnap_query.py status keywords!
	else:
		## ***OBS: HACK
		status_obj['annotate'] = {'pct_complete':0, 'status':'complete'} ## OBS: dirty code. 
		# This enables me to set the 'overall' completion status  

	#### FORMATTING PROCENTATGE COMPLETE
	for val in status_obj.values():
		val['pct_complete'] = int(val['pct_complete']) ### Formatting numbers

	## ***OBS: BAD CODE
	## TODO: rewrite this later
	status_all_complete = True
	for val in status_obj.values():
		if val['status'] != 'complete':
			status_all_complete = False

	status_obj['status_all_complete'] = status_all_complete

	### DUMPING dict of dict as json string
	status2parse = json.dumps(status_obj)

	# with open('/cvar/jhlab/snpsnap/web_logs/call_stat.txt', 'a') as f:
	# 	timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')
	# 	f.write( '%s | someone called me: %s. status is: %s\n' % (timestamp, session_id, status2parse) ) 

	### RETURNING json string to ajax calls
	print "Content-Type: application/json" # for raw text use: "Content-Type: text/plain"
	print ""
	print status2parse

except Exception as e: # DIRTY: but properly the file(s) does not exists
	status_obj = {}
	status_obj['match'] = {'pct_complete':0, 'status':'initialyzing'} ## OBS: dirty code.
	status_obj['set_file'] = {'pct_complete':0, 'status':'initialyzing'} ## OBS: dirty code.
	status_obj['annotate'] = {'pct_complete':0, 'status':'initialyzing'} ## OBS: dirty code.
	
	### RETURNING json string to ajax calls
	print "Content-Type: application/json"
	print ""
	print json.dumps(status_obj)


#http://stackoverflow.com/questions/17347404/python-cgi-and-json-dumps

#http://stackoverflow.com/questions/10718572/post-json-to-python-cgi

#http://stackoverflow.com/questions/10721244/ajax-posting-to-python-cgi
	#--> good