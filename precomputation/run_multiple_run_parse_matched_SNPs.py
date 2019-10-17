#!/usr/bin/env python2.7

# Production V1
# This script was written by Pascal June 18 2014.
# The queue parameter is "??"


#logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)

import sys
import os
import subprocess 

import pdb

import collections
import time
import datetime

#param_list=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
#distance_type = 'ld' # choose 'ld' or 'kb'


param_list=[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
distance_type = 'kb' # choose 'ld' or 'kb'

start_time = time.time()

batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')

output_dir_base = "/home/projects/tp/childrens/snpsnap/data/step2/1KG_snpsnap_production_v1"



processes = collections.defaultdict(dict)

for param in param_list:
	log_file = './logs_step3/log_{type}_{cutoff}'.format(type=distance_type, cutoff=param)
	# OBS: overwriting variable - BAD PRACTICE
	out = output_dir_base + '/' + distance_type + str(param) + '/' # e.g /step2/1KG_snpsnap_production_v1/ld0.5/  --> NB: it is unknow why the last slash is included
	
	#./run_parse_matched_SNPs.py --plink_matched_snps_path /home/projects/tp/childrens/snpsnap/data/step2/1KG_test_thin0.02_duprm/ld0.5/
	cmd="./run_parse_matched_SNPs.py --plink_matched_snps_path {out}".format(out=out)
	print "making command: %s" % cmd
	#with open(log_file, 'a') as f:
	f = open(log_file, mode='a', buffering=1) # buffering: 0 means unbuffered, 1 means line buffered, 
	processes[str(param)]['fh'] = f
	f.write( '####################################### %s #######################################\n' % batch_time )
	#f.flush() # this should also work
	#sys.stdout.flush()
	p=subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, shell=True) #bufsize=0 is default
	processes[str(param)]['p'] = p
	processes[str(param)]['pid'] = p.pid

########## ***** QUESTION ****** #############
# - can the filehandle be closed before the subprocess has ended?
# 	---> no I do not think so!
# 	---> safe way is the keep the filehandle open as wait for the process to end

# Consider flushing by writing to pipe
#stdout = PIPE, 
	#         stderr = PIPE)
	# for line in iter(p.stdout.readline, ''):
	#     print line
	# p.stdout.close()

print "I have just submitted the following processes..."
for param in processes.keys():
	#print processes[param]['fh']
	print processes[param]['pid']

print "Now waiting for processes..."
for param in processes.keys():
	p = processes[param]['p']
	print "waiting for pid=%s [param=%s]" % (p.pid, param)
	p.wait()
	elapsed_time = time.time() - start_time
	print "DONE in %s s (%s min)" % (elapsed_time, elapsed_time/60)

print "Now I am completely done"
elapsed_time = time.time() - start_time
print "TOTAL RUNTIME: %s s (%s min)" % (elapsed_time, elapsed_time/60)


