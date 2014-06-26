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


def cat_tabs():

	processes = collections.defaultdict(dict)

	for param in param_list:
		logger.info( 'cat_tabs: proccessing param=%s' % param)

		inpath_base = input_dir_base + '/' + distance_type + str(param) # e.g DIR: /data/step3/1KG_snpsnap_production_v1/ld0.5
		inpath_stat_gene_density = inpath_base + '/' + 'stat_gene_density' # DIR: e.g /data/step3/1KG_snpsnap_production_v1/ld0.5/stat_gene_density
		outpath_combined_tab = inpath_base + '/' + 'combined.tab' # FILE: e.g /data/step3/1KG_snpsnap_production_v1/ld0.5/combined.tab
		################################################################################################################################		

		################## Checking if file exists ##################
		if os.path.exists(outpath_combined_tab):
			logger.warning ( "outpath_combined_tab exists. Skipping cat'ing new" )
			continue

		#############################################################

		# Writing out header to file. OVERWRITING ANY EXISTING FILE!
		header_str = "rsID freq_bin snp_chr snp_position gene_count dist_nearest_gene_snpsnap dist_nearest_gene dist_nearest_gene_located_within loci_upstream loci_downstream ID_nearest_gene_snpsnap ID_nearest_gene ID_nearest_gene_located_within LD_boddies ID_genes_in_matched_locus"
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
		cmd_cat = "cat {files} >> {out}".format(files=" ".join(tabfiles), out=outpath_combined_tab)
		#logger.info( "making command: %s" % cmd_cat )
		
		### USE THIS for getting stdout and stderr from cat commando
		#p=subprocess.Popen(cmd_cat, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
		# (stdout, stderr) = p.communicate() # OBS: stderr should be empty because we send stderr to subprocess.STDOUT
		# if stdout:
		# 	logger.info(stdout)
		# if stderr:
		# 	logger.warning('****I did see some stderr!')
		# 	logger.error(stderr)
		
		### USE this to inherrit stdout/stderr from subprocess
		p=subprocess.Popen(cmd_cat, stdout=None, stderr=subprocess.STDOUT, shell=True)
		processes[str(param)]['p'] = p
		processes[str(param)]['pid'] = p.pid

	logger.info( "I have just submitted the following processes..." )
	for param in sorted(processes.keys()):
		logger.info( processes[param]['pid'] )

	logger.info( "Now waiting for processes..." )
	for param in sorted(processes.keys()):
		p = processes[param]['p']
		logger.info( "pid=%s [param=%s]: WAITING..." % (p.pid, param) )
		p.wait()
		elapsed_time = time.time() - start_time_script
		logger.info( "pid=%s [param=%s]: DONE! | elapsed time since start: %s min" % (p.pid, param, elapsed_time/60) )




###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')
log_dir='/cvar/jhlab/snpsnap/snpsnap/logs_step5_tabs_cat'
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
param_list=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
distance_type = 'ld' # choose 'ld' or 'kb'

#param_list=[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
#distance_type = 'kb' # choose 'ld' or 'kb'
###################################################################################

input_dir_base = "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v1"

############################# FUNCTION CALLS ##########################################
cat_tabs()
###################################################################################

elapsed_time = time.time() - start_time_script
logger.info( "%s | TOTAL RUNTIME: %s s (%s min)" % (current_script_name, elapsed_time, elapsed_time/60) )





