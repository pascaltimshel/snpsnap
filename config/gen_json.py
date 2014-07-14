#!/usr/bin/env python

import os
import sys
import json

CONFIG = {}
CONFIG["DEBUG_LOG_DIR"] = ""


#bootface
########## PATHS ############
#### ***OBS***: if you change these paths you MUST change them in launchApp.py status_json.py and report_json.py 
path_session_output = '/cvar/jhlab/snpsnap/web_results'+'/'+session_id
path_web_tmp_output = '/cvar/jhlab/snpsnap/web_tmp'
os.mkdir(path_session_output)

#file_snplist = os.path.join(path_web_tmp_output, "{}_{}".format(session_id, 'user_snplist') ) # version1
#file_snplist = "{}/{}_{}".format(path_web_tmp_output, session_id, 'user_snplist') # version2
file_snplist = path_web_tmp_output+'/'+session_id+'_user_snplist' # version3
file_prefix_web_tmp = path_web_tmp_output+'/'+session_id




script2call = "/cvar/jhlab/snpsnap/snpsnap/snpsnap_query.py"

script2call = "/cvar/jhlab/snpsnap/snpsnap/web/app/launchApp.py"

################## PANEL: RESULTS ##################
url_results = '/results/{sid}'.format(sid=session_id)
