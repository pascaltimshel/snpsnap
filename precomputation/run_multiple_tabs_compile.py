#!/usr/bin/env python2.7


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
param_list_ld=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
param_list_kb=[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

param_dict_meta = {'ld':param_list_ld, 'kb':param_list_kb}
##############################################################################


input_dir_base = "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v1"
output_dir_base = "/cvar/jhlab/snpsnap/data/step3/1KG_snpsnap_production_v1_subprocess"

if not os.path.exists(output_dir_base):
	print "UPS: output path %s does not exist. Fix it! Exiting..." % output_dir_base
	sys.exit(1)

log_dir = "/cvar/jhlab/snpsnap/snpsnap/logs_step5_tabs_compile_subprocess"
if not os.path.exists(log_dir):
	print "UPS: log dir %s does not exist. Fix it! Exiting..." % log_dir
	sys.exit(1)



for distance_type in param_dict_meta.keys():
	print "****** RUNNING: type=%s *******" % distance_type
	param_list = param_dict_meta[distance_type]
	for param in param_list:
		start_time = time.time()
		print "RUNNING: param=%s" % param
		compile_in = input_dir_base + '/' + distance_type + str(param) + '/' + 'combined.tab' # e.g /step3/1KG_snpsnap_production_v1/ld0.5/combined.tab
		compile_out = output_dir_base + '/' + distance_type + str(param) # e.g /step3/1KG_snpsnap_production_v1/ld0.5
		if not os.path.exists(compile_out): # OBS: tabs_compile.py output_dir MUST exists
			os.mkdir(compile_out)

		#./tabs_compile.py --combined_tabfile /cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v1/ld0.5/combined.tab --output_dir /cvar/jhlab/snpsnap/data/step3/1KG_snpsnap_production_v1/ld0.5 --distance_type ld --distance_cutoff 0.5 --log_dir /cvar/jhlab/snpsnap/snpsnap/logs_step5_tabs_compile --no_compression
		cmd = "./tabs_compile.py --combined_tabfile {input} --output_dir {output} --distance_type {type} --distance_cutoff {cutoff} --log_dir {log_dir} --no_compression".format(input=compile_in, output=compile_out, type=distance_type, cutoff=param, log_dir=log_dir)
		#OBS: --no_compression set
		print "making command:\n%s" % cmd
		
		FNULL = open(os.devnull, 'w')
		p=subprocess.Popen(cmd, stdout=FNULL, stderr=subprocess.STDOUT, shell=True) #bufsize=0 is default

		print "waiting for pid=%s [param=%s]" % (p.pid, param)
		p.wait()
		elapsed_time = time.time() - start_time
		print "DONE in %s s (%s min)" % (elapsed_time, elapsed_time/60)


	elapsed_time = time.time() - start_time_script
	print "%s | DONE WITH DISTANCE TYPE ??. RUNTIME: %s s (%s min)" % (current_script_name, elapsed_time, elapsed_time/60)


elapsed_time = time.time() - start_time_script
print "%s | TOTAL RUNTIME: %s s (%s min)" % (current_script_name, elapsed_time, elapsed_time/60)



############# Old stuff #######################

# log_file = '{dir}/log_{type}_{cutoff}'.format(dir=os.path.abspath(log_dir), type=distance_type, cutoff=param)

# compile_in = input_dir_base + '/' + distance_type + str(param) + '/' + 'stat_gene_density' # e.g /step3/1KG_snpsnap_production_v1/ld0.5/stat_gene_density
# compile_out = output_dir_base + '/' + distance_type + str(param) # e.g /step3/1KG_snpsnap_production_v1/ld0.5

# #OBS: --no_compression set
# #./tabs_compile.py --input_dir /cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v1/ld0.5/stat_gene_density --hdf5_dir /cvar/jhlab/snpsnap/data/step3/1KG_snpsnap_production_v1 --type ld0.5 --no_compression
# cmd = "./tabs_compile.py --input_dir {input} --hdf5_dir {out} --type {typeANDcutoff} --no_compression".format( input=compile_in, out=output_dir_base, typeANDcutoff=distance_type+str(param) )
# print "making command: %s" % cmd


