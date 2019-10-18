#!/bin/env python

# Import modules for CGI handling 
import cgi, cgitb
import json

import time
import datetime

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

session_id = form.getvalue('session_id', '')
#a0bb9cfb7b31469ce5426659b984266d

path_tmp_output = '/cvar/jhlab/snpsnap/web_tmp'
file_status = path_tmp_output+'/'+session_id+'_status.json'

status_obj = None
with open(file_status, 'r') as json_data:
	status_obj = json.load(json_data)
#body = json.dumps

status2parse = int(status_obj[-1]["match"]*float(100))

with open('/cvar/jhlab/snpsnap/snpsnap/web/call_stat.txt', 'a') as f:
	timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')
	f.write( '%s | some one called me: %s. status is: %s\n' % (timestamp, session_id, status2parse) ) 


#http://stackoverflow.com/questions/17347404/python-cgi-and-json-dumps
# print "Status: 200 OK"
#print "Content-Type: application/json"
print "Content-Type: text/plain"
# print "Length:", len(body)
print ""
print status2parse
#print status_obj # prints whole json object


#http://stackoverflow.com/questions/10718572/post-json-to-python-cgi

#http://stackoverflow.com/questions/10721244/ajax-posting-to-python-cgi
	#--> good