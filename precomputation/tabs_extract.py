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


current_script_name = os.path.basename(__file__)
start_time_script = time.time()
batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')

###################################### Param statements ######################################
param_list=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
distance_type = 'ld' # choose 'ld' or 'kb'

#param_list=[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
#distance_type = 'kb' # choose 'ld' or 'kb'
###############################################################################

input_path = '/cvar/jhlab/snpsnap/data/transfer'
output_path = '/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v1'
if not os.path.exists(output_path):
	print "UPS: output path %s does not exist. Fix it! Exiting..." % output_path
	sys.exit(1)


###################################### SUBPROCCESS - PARALLEL ######################################
processes = collections.defaultdict(dict)

for param in param_list:
	start_time = time.time()

	path_extract = output_path + '/' + distance_type + str(param) ## e.g /step2/1KG_snpsnap_production_v1/ld0.5/
	if not os.path.exists(path_extract):
		print "path_extract %s does NOT exists. Creating new"
		os.makedirs(path_extract)
	else:
		print "path_extract %s exists. Skipping param"
		continue
	
	tar_filename = input_path + '/' + 'stat_gene_density_{type}_{cutoff}.{ext}'.format(type=distance_type, cutoff=param, ext='tar.gz')


	# (tar: for extracting use -x instead of -c)
	cmd_tar = "tar -zxvf {archive_name} -C {outdir}".format(archive_name=tar_filename, outdir=path_extract)
	print "making command: %s" % cmd_tar
	p=subprocess.Popen(cmd_tar, stdout=None, stderr=subprocess.STDOUT, shell=True)
	processes[str(param)]['p'] = p
	processes[str(param)]['pid'] = p.pid


print "I have just submitted the following processes..."
for param in processes.keys():
	print processes[param]['pid']

print "Now waiting for processes..."
for param in processes.keys():
	p = processes[param]['p']
	print "waiting for pid=%s [param=%s]" % (p.pid, param)
	p.wait()
	elapsed_time = time.time() - start_time
	print "DONE in %s s (%s min)" % (elapsed_time, elapsed_time/60)


elapsed_time = time.time() - start_time_script
print "%s | TOTAL RUNTIME: %s s (%s min)" % (current_script_name, elapsed_time, elapsed_time/60)


