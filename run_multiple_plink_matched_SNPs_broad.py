#!/usr/bin/env python2.7


# Production V1
# This script was written by Pascal June 10.
# The queue parameter is "idle"


#logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)

import sys
import os
import subprocess 

import pdb

import collections
import time
import datetime

###################################### USAGE ######################################

# THIS SCRIPT SHOULD BE RUN ON AN INTERACTIVE NODE: it uses memory because the ".bim" file must be read in (multiple) subprocesses from this script

######################################  ######################################

# param_list=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
# distance_type = 'ld' # choose 'ld' or 'kb'

#param_list=[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
#distance_type = 'kb' # choose 'ld' or 'kb'

start_time = time.time()

batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')

#out = "/home/projects/tp/childrens/snpsnap/data/step2/1KG_snpsnap_production_v1"

processes = collections.defaultdict(dict)

log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step2_run_multiple_plink_matched_SNPs"

super_populations = ["EUR"]
distance_types = ["ld", "kb"]

for super_population in super_populations:
	################## Distance type loop ##################
	for distance_type in distance_types:
		if distance_type == "ld":
			param_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
		elif distance_type == "kb":
			param_list=[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
		else:
			raise Exception("Unexpected distance_type")
		################## Distance cut-off loop ##################
		for param in param_list:
			log_file = log_dir + "/log_{super_population}_{type}_{cutoff}_{batch_time}".format(type=distance_type, cutoff=param, super_population=super_population, batch_time=batch_time)
			cmd="python plink_matched_SNPs_broad.py --distance_type {type} --distance_cutoff {cutoff} --super_population {super_population}".format(type=distance_type, cutoff=param, super_population=super_population)
			#cmd="./plink_matched_SNPs.py --output_dir_path {out} --distance_type {type} --distance_cutoff {cutoff}".format(out=out, type=distance_type, cutoff=param)
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

			### New added Broad!
			start_time_process = time.time()
			print "waiting for pid=%s [param=%s]" % (p.pid, param)
			p.wait()
			elapsed_time_process = time.time() - start_time_process
			print "DONE in %s s (%s min)" % (elapsed_time_process, elapsed_time_process/60)

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


################## OUTCOMMENTED February 2015 - Broad ##################
# print "I have just submitted the following processes..."
# for param in processes.keys():
# 	#print processes[param]['fh']
# 	print processes[param]['pid']

# print "Now waiting for processes..."
# for param in processes.keys():
# 	p = processes[param]['p']
# 	print "waiting for pid=%s [param=%s]" % (p.pid, param)
# 	p.wait()
# 	elapsed_time = time.time() - start_time
# 	print "DONE in %s s (%s min)" % (elapsed_time, elapsed_time/60)

print "Now I am completely done"
elapsed_time = time.time() - start_time
print "TOTAL RUNTIME: %s s (%s min)" % (elapsed_time, elapsed_time/60)


