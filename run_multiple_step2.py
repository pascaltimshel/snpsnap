#!/usr/bin/env python2.7


# Production V1
# This script was written by Pascal June 10.
# The queue parameter is "idle"

import sys
import os
import subprocess 

import pdb

import collections
import time
import datetime

#lds2run=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
#lds2run=[0.5]

start_time = time.time()

batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')

out = "/home/projects/tp/childrens/snpsnap/data/step2/1KG_snpsnap_production_v1"

processes = collections.defaultdict(dict)

for p_ld in lds2run:
	log_file = './logs_step2/log_{type}_{cutoff}'.format(type='ld', cutoff=p_ld)
	cmd="./plink_matched_SNPs.py --output_dir_path {out} --distance_type {type} --distance_cutoff {cutoff}".format(out=out, type='ld', cutoff=p_ld)
	print "making command: %s" % cmd
	#with open(log_file, 'a') as f:
	f = open(log_file, 'a')
	processes[str(p_ld)]['fh'] = f
	f.write( '####################################### %s #######################################\n' % batch_time )
	sys.stdout.flush()
	p=subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, shell=True)
	processes[str(p_ld)]['p'] = p
	processes[str(p_ld)]['pid'] = p.pid

# Consider flushing by writing to pipe
#stdout = PIPE, 
	#         stderr = PIPE)
	# for line in iter(p.stdout.readline, ''):
	#     print line
	# p.stdout.close()

print "I have just submitted the following processes..."
for p_ld in processes.keys():
	#print processes[p_ld]['fh']
	print processes[p_ld]['pid']

print "Now waiting for processes..."
for p_ld in processes.keys():
	p = processes[p_ld]['p']
	print "waiting for pid=%s [param=%s]" % (p.pid, p_ld)
	p.wait()
	elapsed_time = time.time() - start_time
	print "DONE in %s s (%s min)" % (elapsed_time, elapsed_time/60)

print "Now I am completely done"
elapsed_time = time.time() - start_time
print "TOTAL RUNTIME: %s s (%s min)" % (elapsed_time, elapsed_time/60)


