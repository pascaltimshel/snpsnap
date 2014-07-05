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

file_returncodes = "{base}/{sid}_{type}.{ext}".format(base=path_web_tmp_output, sid=session_id, type='returncodes', ext='json')
# e.g. 2ede5955021a10cb0e1a13882be520eb_returncodes.json

try:
	returncode2parse = 0

	returncodes_obj = None ## Needed for correct variable scope
	with open(file_returncodes, 'r') as json_data:
		returncodes_obj = json.load(json_data) # keys in dict will be 'match' and 'annotate'. values are the return codes

	for key, val in returncodes_obj.items():
		if int(val) != 0: # remember to take int!? not sure...
			returncode2parse = -1

	### RETURNING json string to ajax calls
	print "Content-Type: text/plain" # for raw text use: "Content-Type: text/plain"
	print ""
	print returncode2parse

except Exception as e: # e.g IOError
	print "Content-Type: text/plain"
	print ""
	print 0 # ajax call will react to calues not equal to zero

