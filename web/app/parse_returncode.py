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

## Example of content of json file:
#{"annotate": 0, "clump": 1, "match": 0} --> here the "clump" failed!
#{"annotate": 0, "clump": 0, "match": 0} --> here the all is OK!

try:
	returncodes_obj = None ## Needed for correct variable scope
	with open(file_returncodes, 'r') as json_data:
		returncodes_obj = json.load(json_data) # keys in dict will be 'match' and 'annotate' (and possibly later added subcommands). values are the return codes

	returncodes_obj["dummy"] = 0 # IMPORTANT: results.js will only try to access the 'match'/'annotate'/'clump' keys (elements) if the 'dummy' key is zero
	#^READ THIS: We set the 'dummy' key so that results.js CAN always access the element - independent of what happens in the 'try/except' clause

	### DUMPING dict of dict as json string
	returncode2parse = json.dumps(returncodes_obj)

	### RETURNING json string to ajax calls
	print "Content-Type: application/json" # for raw text use: "Content-Type: text/plain"
	print ""
	print returncode2parse

except Exception as e: # e.g IOError
	print "Content-Type: application/json"
	print ""
	returncodes_obj = {"dummy":999} ## this just has to be any number DIFFERENT from zero
	returncode2parse = json.dumps(returncodes_obj)
	print returncode2parse




############## BEFORE 09/15/2014 ########## - worked fine. Only parsing txt

# try:
# 	returncode2parse = 0

# 	returncodes_obj = None ## Needed for correct variable scope
# 	with open(file_returncodes, 'r') as json_data:
# 		returncodes_obj = json.load(json_data) # keys in dict will be 'match' and 'annotate'. values are the return codes

# 	for key, val in returncodes_obj.items():
# 		if int(val) != 0: # remember to take int!? not sure...
# 			returncode2parse = -1

# 	### RETURNING json string to ajax calls
# 	print "Content-Type: text/plain" # for raw text use: "Content-Type: text/plain"
# 	print ""
# 	print returncode2parse

# except Exception as e: # e.g IOError
# 	print "Content-Type: text/plain"
# 	print ""
# 	print 0 # ajax call will react to calues not equal to zero

