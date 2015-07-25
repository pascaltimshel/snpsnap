#!/usr/bin/env python2.7

# Production Version 2
# Date of creation: 02/25/2015

import sys
import os
import subprocess 

import pdb

import collections
import time
import datetime

import pplaunch
import pphelper
import pplogger

###################################### USAGE ######################################

# ??

######################################  ######################################
#param_list_ld = [0.5, 0.9]
param_list_ld = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
param_list_kb = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

######################################  ######################################
start_time = time.time()

batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')

##### script2call
script2call = "run_parse_matched_SNPs_broad.py"

##### IMPORTANT DIRECTORY
#output_dir_base = "/home/projects/tp/childrens/snpsnap/data/step2/1KG_snpsnap_production_v1"
#output_dir_base = "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2"
output_dir_base = "/cvar/jhlab/snpsnap/data/production_v2_chrX_standalone-altQC/step2" # SHOULD MATCH the output dir of "plink_matched_SNPs_broad.py" --> "--plink_matched_snps_path"


processes = collections.defaultdict(dict)

super_populations = ["EUR"]
#super_populations = ["EAS"]
#super_populations = ["WAFR"]
distance_types = ["ld", "kb"]
#distance_types = ["ld"]





###################################### Waiting - batch ######################################
def wait_for_processes(processes):
	print "FUNCTION wait_for_processes() CALLED!"

	print "I have just submitted the following processes..."
	for param in processes.keys():
		log_file = processes[param]['log_file']
		job_no = processes[param]['job_no']
		cmd = processes[param]['cmd']
		pid = processes[param]['pid']

		print "[pid={pid}; param={param}; job_no={job_no}; log_file={log_file}]".format(pid=pid, param=param, job_no=job_no, log_file=log_file)


	print "Now waiting for processes..."
	for param in processes.keys():
		p = processes[param]['p']

		log_file = processes[param]['log_file']
		job_no = processes[param]['job_no']
		cmd = processes[param]['cmd']
		pid = processes[param]['pid']

		print "WATING <-- [pid={pid}; param={param}; job_no={job_no}; log_file={log_file}]".format(pid=pid, param=param, job_no=job_no, log_file=log_file)
		
		### Flushing
		# f.flush() # this should also work
		sys.stdout.flush()

		p.wait()
		elapsed_time = time.time() - start_time
		print "DONE in %s s (%s min)" % (elapsed_time, elapsed_time/60)




###################################### MAIN LOOP ######################################

job_no = 0


for super_population in super_populations:
	################## Distance type loop ##################
	for distance_type in distance_types:
		if distance_type == "ld":
			param_list = param_list_ld
		elif distance_type == "kb":
			param_list = param_list_kb
		else:
			raise Exception("Unexpected distance_type")
		################## Distance cut-off loop ##################
		for param in param_list:
			
			## Incrementing job_no
			job_no += 1

			pipeline_identifer = "{super_population}_{distance_type}_{distance_cutoff}".format(super_population=super_population, distance_type=distance_type, distance_cutoff=param)
				# --> "pipeline_identifer" is used as KEYS in processes
				# --> MUST BE UNIQUE


			###################################### LOG DIR - IMPORTANT TO SET IT CORRECTLY ######################################
			#log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step3_run_multiple_run_parse_matched_SNPs/{super_population}".format(super_population=super_population)
			log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2_chrX_standalone-altQC/step3_run_multiple_run_parse_matched_SNPs/{super_population}".format(super_population=super_population)
			if not os.path.exists(log_dir):
				os.makedirs(log_dir)
			log_file = log_dir + "/log_{super_population}_{type}_{cutoff}_{batch_time}".format(type=distance_type, cutoff=param, super_population=super_population, batch_time=batch_time)
			#####################################################################################


			### Constructing command ###
			#out = output_dir_base + '/' + distance_type + str(param) + '/' # e.g /step2/1KG_snpsnap_production_v1/ld0.5/  --> NB: it is unknow why the last slash is included
			out = "{output_dir_base}/{super_population}/{distance_type}{param}/".format(output_dir_base=output_dir_base, super_population=super_population, distance_type=distance_type, param=param) # e.g /step2/1KG_snpsnap_production_v2/EUR/ld0.5/  --> NB: it is unknow why the last slash is included
			
			#./run_parse_matched_SNPs.py --plink_matched_snps_path /home/projects/tp/childrens/snpsnap/data/step2/1KG_test_thin0.02_duprm/ld0.5/
			cmd="python {script2call} --plink_matched_snps_path {out}".format(out=out, script2call=script2call)
			print "making command: %s" % cmd
			

			#with open(log_file, 'a') as f:
			f = open(log_file, mode='a', buffering=1) # buffering: 0 means unbuffered, 1 means line buffered, 
			processes[pipeline_identifer]['fh'] = f
			f.write( '####################################### %s #######################################\n' % batch_time )

			p=subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, shell=True) #bufsize=0 is default

			processes[pipeline_identifer]['log_file'] = log_file
			processes[pipeline_identifer]['job_no'] = job_no
			processes[pipeline_identifer]['cmd'] = cmd
			processes[pipeline_identifer]['p'] = p
			processes[pipeline_identifer]['pid'] = p.pid

			time.sleep(1) # *NEW altQC*

			### Waiting every 5th job
			if (job_no % 5 == 0):
				wait_for_processes(processes)
				print "resetting processes by re-initialyzing the defauldict"
				processes = collections.defaultdict(dict) # resetting processes

	print "Waiting for last round of processes"
	wait_for_processes(processes)
	print "Done waiting"

			# ################## NEW - ADDED FROM BROAD ##################
			# start_time_process = time.time()
			# print "waiting for pid=%s [param=%s]" % (p.pid, param)
			# ### Flushing
			# f.flush() # this should also work
			# sys.stdout.flush()
			# ### Waiting ---> *OBS*: if you do not wait, then you need A LOT of memory!
			# #p.wait()
			# elapsed_time_process = time.time() - start_time_process
			# print "DONE in %s s (%s min)" % (elapsed_time_process, elapsed_time_process/60)


print "Now I am completely done"
elapsed_time = time.time() - start_time
print "TOTAL RUNTIME: %s s (%s min)" % (elapsed_time, elapsed_time/60)


