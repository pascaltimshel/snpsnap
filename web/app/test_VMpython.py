#!/usr/bin/python

#!/bin/env python

#source /opt/rh/python27/enable
	# --> use this in your terminal

#!/opt/rh/python27/root/usr/bin/python2.7
#!/opt/rh/python27/root/usr/bin/python

#!/usr/bin/python

#!/usr/bin/env python2.7
#!/usr/bin/env python


# Import modules for CGI handling 
import cgi, cgitb
cgitb.enable()

import os
#import tables
import pandas
import subprocess


import os
import time # potential
import hashlib
import random

import subprocess

#########*********************
#import pandas # TEST ME!!!!
#########*********************

session_id = hashlib.md5(str(random.random())).hexdigest()
path_session = '/cvar/jhlab/snpsnap/web_results'+'/'+session_id
path_session_tmp = path_session+'/tmp'
path_session_output = path_session+'/res'
os.mkdir(path_session)
# os.mkdir(path_session_tmp)
# os.mkdir(path_session_output)



# commands_called = []

# if annotate:
# 	command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} annotate".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff)
# 	commands_called.append(command_shell)
# 	subprocess.Popen(command_shell, shell=True)


print "Content-Type: text/html"     # HTML is following
print                               # blank line, end of headers
print "<html>"
print "<head>"
print "<title>CGI-TESTPAGE</title>"
print "</head>"

print "<body>"
print "<h1>CGI-TESTPAGE</h1>"
print "<h6>This page can be used to test what python version is used and what modules are loaded</h6>"

import platform
import sys # only need for print(sys.version)
print "<p>Python version: %s</p>" % platform.python_version()
print "<p>Python full string: %s</p>" % sys.version

print "<p>List of loaded python modules:</p>"
print "<ul>"
for module in sys.modules.keys():
	print "<li>%s</li>" % module
print "</ul>"


#print ""

print "</body>"
print "</html>"

