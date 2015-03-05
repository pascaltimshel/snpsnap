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


import glob
import re




def parse_plink2_log_file(plink_log_file):
	"""
	Note: I do *NOT* think it is sufficient to check that the 'End time' token is present.
	It is best to specifically check that the '... done.' is present.
	"""
	###################################### Example plink LD log file ######################################
	# PLINK v1.90b2l 64-bit (26 Sep 2014)
	# 13 arguments: --bfile /cvar/jhlab/snpsnap/data/step1/production_v2_QC_full_merged_duplicate_rm/WAFR/ALL.chr_merged.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes --ld-snp-list /cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/WAFR/ld0.1/snplists/freq6-7-part0-611910.rsID --ld-window 99999 --ld-window-kb 1000 --ld-window-r2 0.1 --out /cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/WAFR/ld0.1/ldlists/freq6-7-part0-611910 --r2
	# Hostname: cage
	# Working directory: /cvar/jhlab/snpsnap/snpsnap
	# Start time: Wed Mar  4 04:25:16 2015

	# Random number seed: 1425461116
	# 516240 MB RAM detected; reserving 258120 MB for main workspace.
	# 16211334 variants loaded from .bim file.
	# 405 people (0 males, 0 females, 405 ambiguous) loaded from .fam.
	# Ambiguous sex IDs written to
	# /cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/WAFR/ld0.1/ldlists/freq6-7-part0-611910.nosex
	# .
	# Using up to 47 threads (change this with --threads).
	# Before main variant filters, 405 founders and 0 nonfounders present.
	# Calculating allele frequencies... done.
	# 16211334 variants and 405 people pass filters and QC.
	# Note: No phenotypes present.
	# --r2 to
	# /cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/WAFR/ld0.1/ldlists/freq6-7-part0-611910.ld
	# ... done.

	# End time: Wed Mar  4 04:31:43 2015
	############################################################################################################
	

	# About flags
	# https://docs.python.org/2/howto/regex.html#compilation-flags
	# Anchors: \A only ever matches at the start of the string. Likewise, \Z only ever matches at the end of the string
	# http://www.regular-expressions.info/anchors.html

	# In multiline mode, ^ matches the position immediately following a newline and $ matches the position immediately preceding a newline
	#>>> re.search("^(.*)$^.*$", multiline_string, re.M)    # won't match
	#>>> re.search("^(.*)$\n^.*$", multiline_string, re.M)  # will match

	pattern_start_time = re.compile(r"^Start time: (.*)$", re.MULTILINE)
	pattern_end_time = re.compile(r"^End time: (.*)$", re.MULTILINE)
	pattern_process_r2 = re.compile(r"^--r2 to$\n^(.*.ld)$\n^\.\.\. done\.$", re.MULTILINE)

	with open(plink_log_file, 'r') as f:
	    log_data = f.read() # reading whole file into STRING


	    ### Getting group matches
	    # "If a group is contained in a part of the pattern that did not match, the corresponding result is None"
	    plink_time_start = pattern_start_time.search(log_data).group(0)
	    plink_time_end = pattern_end_time.search(log_data).group(0)
	        # --> variables will be "None" if no match
	    
	    if pattern_process_r2.search(log_data): # we found a match
	        plink_ld_status = True
	    else:
	        plink_ld_status = False
	    
	return plink_ld_status, plink_time_start, plink_time_end
	# types of output: bool [True/False], string, string



def validate_plink_ld_log_file(batch_id, path_main, unit_test_file):
	""" 
	One-to-One mapping: 
	One batch_snplist gives rise to one outfilename (ld file)
	"""

	outfilename = path_main + "/ldlists/" + batch_id + ".log" # batch_id --> e.g. freq0-1-part-0-1000
	

	if not os.path.exists(outfilename): # file does not exist
		status_string = "status = no previous outfilename | {outfilename}".format(outfilename=outfilename)
		unit_test_file['NO_PREVIOUS_FILE'].append(status_string)
		return True # submit job is there is no existing outfilename
	else: # file exists
		plink_ld_status, plink_time_start, plink_time_end = parse_plink2_log_file(plink_log_file=outfilename)
		if plink_ld_status == True:
			status_string = "status = OK | [{plink_time_start}] | [{plink_time_end}] | {outfilename}".format(plink_time_start=plink_time_start, plink_time_end=plink_time_end, outfilename=outfilename)
			unit_test_file['FILE_EXISTS_OK'].append(status_string)
			return True
		else:
			status_string = "status = *BAD* | [{plink_time_start}] | [{plink_time_end}] | {outfilename}".format(plink_time_start=plink_time_start, plink_time_end=plink_time_end, outfilename=outfilename)
			unit_test_file['FILE_EXISTS_BAD'].append(status_string)
			return False # submit job if parse_plink2_log_file() tells us that the log file was not complete



###################################### MAIN LOOP ######################################

def validate():
	for super_population in super_populations:
		logger.info( "super_population={}".format(super_population) )

		################################ *IMPORTANT*: PATH TO STATUS FILE #############################################
		# *THIS IS IMPORTANT FOR THE VALIDATION* #
		# This script will *APPEND* a "status line" to a file that is SHARED within a super_population. That is, all distance measures writes to the same file.
		# *Note that this approach is not *thread* safe* 

		path_status = log_dir + '/{super_population}'.format(super_population=super_population)
		if not os.path.exists(path_status):
			os.makedirs(path_status)
		file_status = path_status + "/status_file_{}.txt".format(batch_time)


		################## Distance type loop ##################
		for distance_type in distance_types:
			logger.info( "distance_type={}".format(distance_type) )
			if distance_type == "ld":
				param_list = param_list_ld
			elif distance_type == "kb":
				param_list = param_list_kb
			else:
				raise Exception("Unexpected distance_type")
			################## Distance cut-off loop ##################
			for param in param_list:
				logger.info( "param={}".format(param) )
				
				# pipeline_identifer = "{super_population}_{distance_type}_{distance_cutoff}".format(super_population=super_population, distance_type=distance_type, distance_cutoff=param)

				path_main = input_dir_base + "/{super_population}/{distance_type}{distance_cutoff}".format(super_population=super_population, distance_type=distance_type, distance_cutoff=param) # e.g. /cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/ld0.5
				glob_batch_ids = glob.glob(path_main+"/snplists/*.rsID") # e.g. /cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/ld0.5/snplists/*.rsID
				### file names that should match this:
				# /cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/WAFR/ld0.1/snplists/freq5-6-part0-733569.rsID
				# /cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/WAFR/ld0.1/snplists/freq6-7-part0-611910.rsID
				# /cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/WAFR/ld0.1/snplists/freq8-9-part0-464415.rsID
				### sorting inplace
				glob_batch_ids.sort(key=lambda x: int(x.split('/')[-1].split('freq')[-1].split('-')[0]))
				### extracting the batch_id: e.g. batch_id --> freq8-9-part0-464415
				batch_ids = [os.path.basename(x).replace('.rsID', '') for x in glob_batch_ids]
					# alt1: os.path.splitext()[0]
					# alt2: .replace('.rsID', '')

				### IMPORTANT - (Re)initialyzing default dict - THE DICT IS "per distance measure"
				unit_test_file = collections.defaultdict(list)
				### Master keys in dict
				# unit_test_file['NO_PREVIOUS_FILE']
				# unit_test_file['FILE_EXISTS_OK']
				# unit_test_file['FILE_EXISTS_BAD']
				for batch_id in batch_ids:
					validate_plink_ld_log_file(batch_id, path_main, unit_test_file) # THIS WILL POPULATE THE "unit_test_file" dict

				################## Setting flag for population - only used for logging ##################
				if "NO_PREVIOUS_FILE" in unit_test_file: # check for key in master keys
					dict_valid_super_population[super_population] = "NOT VALID"
				elif "FILE_EXISTS_BAD" in unit_test_file: # check for key in master keys
					dict_valid_super_population[super_population] = "NOT VALID"
				else:
					dict_valid_super_population[super_population] = "VALID"


				### SET FLAG FOR ENTERIE POPULATION/OR LD [give detailts]

				block_str = '============================= %s ===================================' % batch_time
				################## LOGGER Display STATS ##########################
				# logger.info( '\n'.join([block_str]*3) )
				# logger.info( "#################### **** STATS from 'unit_test_file' **** ####################" )
				# for stat_key, stat_list in unit_test_file.items():
				# 	for elem in stat_list:
				# 		logger.info( "{}\t{}".format( stat_key, elem ) )
				# 	logger.info( block_str )
				# for stat_key, stat_list in unit_test_file.items():
				# 	logger.info( "{}: {}".format( stat_key, len(stat_list) ) )
				# logger.info( block_str )

				################## WRITE STATS ##########################
				with open(file_status, "a") as f: # *IMPORTANT*: open in append-mode [remember that file_status should time stamp, so different runs on of this script different days does not write to the same file]
					f.write( '\n'.join([block_str]*3) + "\n")
					f.write( "#################### **** STATS from 'unit_test_file' **** ####################" + "\n")
					for stat_key, stat_list in unit_test_file.items():
						for elem in stat_list:
							f.write( "{}\t{}".format( stat_key, elem ) + "\n")
						f.write( block_str + "\n")
					for stat_key, stat_list in unit_test_file.items():
						f.write( "{}: {}".format( stat_key, len(stat_list) ) + "\n")
					f.write( block_str + "\n")

######################################  ######################################
start_time = time.time()
batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')



######################################  ######################################
#param_list_ld = [0.5, 0.9]
param_list_ld = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
param_list_kb = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

super_populations = ["EUR"]
#super_populations = ["EAS"]
#super_populations = ["WAFR"]
distance_types = ["ld", "kb"]
#distance_types = ["ld"]


input_dir_base = "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2"


###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')
log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step2_validation_plink_ld_log_files" # *OBS*: this log dir WILL BE USED AS BASE DIR OF THE STATUS FILES
if not os.path.exists(log_dir):
	os.makedirs(log_dir)
log_name = current_script_name + "_{batch_time}".format(batch_time=batch_time)

logger = pplogger.Logger(name=log_name, log_dir=log_dir, log_format=1, enabled=True).get()
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################


dict_valid_super_population = {}
### Run function
validate()

logger.info( "Will display results for dict_valid_super_population now..." )
for key, value in dict_valid_super_population.items():
	logger.info( "{}:{}".format(key, value) )


logger.info("Now I am completely done")
elapsed_time = time.time() - start_time
logger.info("TOTAL RUNTIME: %s s (%s min)" % (elapsed_time, elapsed_time/60))




###################################### GARBAGE ######################################

			# for i in range(0,50,1): # 0...49. allways 50 freq bins. No problem here.
			# 	suffix = "%s-%s"%(i,i+1) # e.g. 0-1
			# 	ldfiles_prefix = os.path.abspath(path+"/ldlists/freq") + suffix
			# 	snplist_prefix = os.path.abspath(path+"/snplists/freq") + suffix # e.g. # e.g. ...long-path.../snplist/freq0-1, where the whole file is e.g. freq9-10-part40000-50000.rsID
			# 	### getting files
			# 	snplist_files = glob.glob(snplist_prefix+"*.rsID") # catching all files with CORRECT prefix



