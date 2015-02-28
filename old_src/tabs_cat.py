#!/usr/bin/env python2.7


import sys
import os
import subprocess 

import collections
import time
import datetime

import glob
import pandas as pd

import pplogger

import pdb


###################################### THIS SCRIPT IS NO LONGER MAINTAINED ######################################
# This script was last updated in Feb 2015 during production version 2.
# Howver its use is DEPRECATED. The script "tab_gen_ld_buddy_counts.py" contains all the function of this script AND MORE.
	# --> "tab_gen_ld_buddy_counts.py" is part of the official pipeline!

######################################################################################################


###################################### Waiting - batch ######################################
def wait_for_processes(processes):
	""" 
	*OBS* THIS FUNCTION IS TO BE USED IN SCRIPTS WITH A LOGGER!
	- .flush() commands removed
	- print statements substituted for logger() calls
	"""
	logger( "FUNCTION wait_for_processes() CALLED!" )

	logger( "I have just submitted the following processes..." )
	for param in processes.keys():
		log_file = processes[param]['log_file']
		job_no = processes[param]['job_no']
		cmd = processes[param]['cmd']
		pid = processes[param]['pid']

		logger( "[pid={pid}; param={param}; job_no={job_no}; log_file={log_file}]".format(pid=pid, param=param, job_no=job_no, log_file=log_file) )


	logger( "Now waiting for processes..." )
	for param in processes.keys():
		p = processes[param]['p']

		log_file = processes[param]['log_file']
		job_no = processes[param]['job_no']
		cmd = processes[param]['cmd']
		pid = processes[param]['pid']

		logger( "WATING <-- [pid={pid}; param={param}; job_no={job_no}; log_file={log_file}]".format(pid=pid, param=param, job_no=job_no, log_file=log_file) )
		
		p.wait()
		elapsed_time = time.time() - start_time
		logger( "DONE in %s s (%s min)" % (elapsed_time, elapsed_time/60) )





def cat_tabs():

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

				logger.info( 'cat_tabs: proccessing param=%s' % param)


				### NEW FEB 2015* - production_v2
				inpath_base = "{base}/{super_population}/{distance_type}{distance_cutoff}".format(base=input_dir_base, super_population=super_population, distance_type=distance_type, distance_cutoff=param) # e.g DIR: /data/step2/1KG_snpsnap_production_v2/EUR/ld0.5
				inpath_stat_gene_density = inpath_base + '/' + 'stat_gene_density' # DIR: e.g /data/step2/1KG_snpsnap_production_v2/EUR/ld0.5/stat_gene_density
				outpath_combined_tab = inpath_base + '/' + 'combined.tab' # FILE: e.g /data/step2/1KG_snpsnap_production_v2/EUR/ld0.5/combined.tab

				### *BEFORE FEB 2015* production_v1
				# inpath_base = input_dir_base + '/' + distance_type + str(param) # e.g DIR: /data/step2/1KG_snpsnap_production_v1/ld0.5
				# inpath_stat_gene_density = inpath_base + '/' + 'stat_gene_density' # DIR: e.g /data/step2/1KG_snpsnap_production_v1/ld0.5/stat_gene_density
				# outpath_combined_tab = inpath_base + '/' + 'combined.tab' # FILE: e.g /data/step2/1KG_snpsnap_production_v1/ld0.5/combined.tab
				################################################################################################################################		

				################## Checking if file exists ##################
				if os.path.exists(outpath_combined_tab):
					logger.warning ( "outpath_combined_tab exists. Skipping cat'ing new" )
					continue

				#############################################################

				##### Writing out header to file. OVERWRITING ANY EXISTING FILE! #####
				### *NEW FEB 2015* - ENSEMBL file for GENCODE genes. added: protein_coding, HGNC symbols and 2 x SNP_location_flags
				# dist_nearest_gene_snpsnap_protein_coding
				# ID_nearest_gene_snpsnap_protein_coding
				# HGNC_nearest_gene_snpsnap
				# HGNC_nearest_gene_snpsnap_protein_coding
				# flag_snp_within_gene
				# flag_snp_within_gene_protein_coding

				header_str = "rsID freq_bin snp_chr snp_position gene_count dist_nearest_gene_snpsnap dist_nearest_gene_snpsnap_protein_coding dist_nearest_gene dist_nearest_gene_located_within loci_upstream loci_downstream ID_nearest_gene_snpsnap ID_nearest_gene_snpsnap_protein_coding ID_nearest_gene ID_nearest_gene_located_within HGNC_nearest_gene_snpsnap HGNC_nearest_gene_snpsnap_protein_coding LD_boddies flag_snp_within_gene flag_snp_within_gene_protein_coding ID_genes_in_matched_locus"
				### *BEFORE FEB 2015* - old ENSEMBL file
				#header_str = "rsID freq_bin snp_chr snp_position gene_count dist_nearest_gene_snpsnap dist_nearest_gene dist_nearest_gene_located_within loci_upstream loci_downstream ID_nearest_gene_snpsnap ID_nearest_gene ID_nearest_gene_located_within LD_boddies ID_genes_in_matched_locus"
				header_str_tab_sep = "\t".join(header_str.split())
				with open(outpath_combined_tab, 'w') as f:
					f.write(header_str_tab_sep+'\n')
				#################################################

				tabfiles = glob.glob(inpath_stat_gene_density+"/*.tab")
				if not len(tabfiles) == 50:
					logger.error( "Error: did not find 50 .tab files as expected in path: %s" % inpath_stat_gene_density )
					logger.error( "Number of tabfiles found: %s" % len(tabfiles) )
					logger.error( "Aborting script..." )
					sys.exit(1)
				# Sorting on freq bin
				# It is EXTREMELY important to SORT the tab files before 
				tabfiles.sort(key=lambda x: int(x.split('/')[-1].split('freq')[-1].split('-')[0]))

				############### BE AWARE OF TOO long command line ##############
				#  - command: Argument list too long
				#xargs --show-limits
				#getconf ARG_MAX
				#	--> 131072
				# using xargs?
				#cat filelist | xargs cat >> bigfile.dat
				################################################################

				# creating cat cmd. APPENDING TO FILE containing header.
				cmd = "cat {files} >> {out}".format(files=" ".join(tabfiles), out=outpath_combined_tab)
				#logger.info( "making command: %s" % cmd )
				
				### USE THIS for getting stdout and stderr from cat commando
				#p=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
				# (stdout, stderr) = p.communicate() # OBS: stderr should be empty because we send stderr to subprocess.STDOUT
				# if stdout:
				# 	logger.info(stdout)
				# if stderr:
				# 	logger.warning('****I did see some stderr!')
				# 	logger.error(stderr)
				
				### USE this to inherrit stdout/stderr from subprocess
				p=subprocess.Popen(cmd, stdout=None, stderr=subprocess.STDOUT, shell=True)

				processes[pipeline_identifer]['log_file'] = "dummy"
				processes[pipeline_identifer]['job_no'] = job_no
				processes[pipeline_identifer]['cmd'] = cmd
				processes[pipeline_identifer]['p'] = p
				processes[pipeline_identifer]['pid'] = p.pid

				### Waiting every 5th job
				if (job_no % 5 == 0):
					wait_for_processes(processes)
					logger( "resetting processes by re-initialyzing the defauldict" )
					processes = collections.defaultdict(dict) # resetting processes




###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')
log_dir='/cvar/jhlab/snpsnap/snpsnap/logs_step5_tabs_cat'
if not os.path.exists(log_dir):
	os.makedirs(log_dir)
logger = pplogger.Logger(name=current_script_name, log_dir=log_dir, log_format=0, enabled=True).get() #
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################

###################################### CONSTANTS ######################################
start_time_script = time.time()
batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')

############################# PARAM LIST ##########################################
super_populations = ["EUR"]
#distance_types = ["ld", "kb"]
distance_types = ["ld"]

param_list_ld = [0.5, 0.9]
#param_list_ld = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
#param_list_kb = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

###################################################################################

#input_dir_base = "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v1"
input_dir_base = "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2"

############################# FUNCTION CALLS ##########################################
job_no = 0
processes = collections.defaultdict(dict)

cat_tabs()
###################################################################################

elapsed_time = time.time() - start_time_script
logger.info( "%s | TOTAL RUNTIME: %s s (%s min)" % (current_script_name, elapsed_time, elapsed_time/60) )





