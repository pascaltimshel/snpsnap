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

############################# SWITCH ##########################################
param_list=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
distance_type = 'ld' # choose 'ld' or 'kb'

#param_list=[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
#distance_type = 'kb' # choose 'ld' or 'kb'
##############################################################################



input_dir_base = "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v1"
output_dir_base = "/cvar/jhlab/snpsnap/data/step3/1KG_snpsnap_production_v1"

if not os.path.exists(output_dir_base):
	print "UPS: output path %s does not exist. Fix it! Exiting..." % output_dir_base
	sys.exit(1)

log_dir = "/cvar/jhlab/snpsnap/snpsnap/logs_step5_tabs_compile"
if not os.path.exists(log_dir):
	print "UPS: log dir %s does not exist. Fix it! Exiting..." % log_dir
	sys.exit(1)



processes = collections.defaultdict(dict)

for param in param_list:
	log_file = '{dir}/log_{type}_{cutoff}'.format(dir=os.path.abspath(log_dir), type=distance_type, cutoff=param)

	compile_in = input_dir_base + '/' + distance_type + str(param) + '/' + 'stat_gene_density' # e.g /step3/1KG_snpsnap_production_v1/ld0.5/stat_gene_density
	compile_out = output_dir_base + '/' + distance_type + str(param) # e.g /step3/1KG_snpsnap_production_v1/ld0.5

	#OBS: --no_compression set
	#./tabs_compile.py --input_dir /cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v1/ld0.5/stat_gene_density --hdf5_dir /cvar/jhlab/snpsnap/data/step3/1KG_snpsnap_production_v1 --type ld0.5 --no_compression
	cmd = "./tabs_compile.py --input_dir {input} --hdf5_dir {out} --type {typeANDcutoff} --no_compression".format( input=compile_in, out=output_dir_base, typeANDcutoff=distance_type+str(param) )
	print "making command: %s" % cmd
	
	# f = open(log_file, mode='a', buffering=1) # buffering: 0 means unbuffered, 1 means line buffered, 
	# processes[str(param)]['fh'] = f
	# f.write( '####################################### %s #######################################\n' % batch_time )
	# f.write( "making command: %s\n" % cmd )
	# p=subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, shell=True) #bufsize=0 is default
	# processes[str(param)]['p'] = p
	# processes[str(param)]['pid'] = p.pid



print "I have just submitted the following processes..."
for param in processes.keys():
	print processes[param]['pid']

print "Now waiting for processes..."
for param in processes.keys():
	p = processes[param]['p']
	print "waiting for pid=%s [param=%s]" % (p.pid, param)
	p.wait()
	elapsed_time = time.time() - start_time_script
	print "DONE in %s s (%s min)" % (elapsed_time, elapsed_time/60)


elapsed_time = time.time() - start_time_script
print "%s | TOTAL RUNTIME: %s s (%s min)" % (current_script_name, elapsed_time, elapsed_time/60)


