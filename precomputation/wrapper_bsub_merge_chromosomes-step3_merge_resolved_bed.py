#!/usr/bin/env python2.7

import sys
import glob
import os

import datetime
import time
import argparse

import pplaunch
import pphelper
import pplogger

import re
import subprocess
import logging


import pdb


#### *OBS* ####
# This script only works with plink2


# def test():
# 	try:
# 		FNULL = open(os.devnull, 'w')
# 		subprocess.Popen(["plink", "--silent", "--noweb"], stdout=FNULL, stderr=subprocess.STDOUT)
# 		FNULL.close()
# 	except Exception as e:
# 		raise Exception("Could not find plink as executable on path. Please check that you have used 'reuse .plink2-1.90b' (PLINK 1 will NOT work for this script!). Error msg: %s" % e.message)


def submit():
	processes = []
	for super_population in param_super_population:
		logger.info( "****** RUNNING: type=%s *******" % super_population )

		### *WRITE* MERGE TEXT FILE ###
		input_merge_file = None
		if gen_test_data:
			input_merge_file="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_test_merged-step2_conflicts_excluded/{super_population}/plink_merge_file.txt".format(super_population=super_population)
		else:
			input_merge_file="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_full_merged-step2_conflicts_excluded/{super_population}/plink_merge_file.txt".format(super_population=super_population)
		with open(input_merge_file, 'w') as f:
			for chromosome in param_chromosome: # **LOOPING OVER CHROMOSOME**#
				if gen_test_data:
					line2write="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_test_merged-step2_conflicts_excluded/{super_population}/ALL.{chromosome}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes".format(super_population=super_population, chromosome=chromosome) # OBS: this is the prefix needed in PLINK
				else:
					line2write="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_full_merged-step2_conflicts_excluded/{super_population}/ALL.{chromosome}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes".format(super_population=super_population, chromosome=chromosome) # OBS: this is the prefix needed in PLINK
				f.write(line2write+"\n")


		### Output dir
		dir_out = None # correct variable scope
		if gen_test_data:
			dir_out="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_test_merged/{super_population}".format(super_population=super_population)
		else:
			dir_out="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_full_merged/{super_population}".format(super_population=super_population)

		### Creating outdir
		if not os.path.exists(dir_out):
			os.makedirs(dir_out) # NOTE use of makedirs(): all intermediate-level directories needed to contain the leaf directory

		### Setting out_prefix
		out_prefix = dir_out + '/' + "ALL.chr_merged.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes" 

		### SAFETY CHECK - checking for existence of .PED file with out_prefix
		if os.path.exists(out_prefix+'.bed'): 
			logger.critical( "%s | bed file %s.bed exists already. Skipping this..." % (super_population, out_prefix) )
			continue

		###################################### PLINK CALL - --make-bed and QC ######################################
		#https://www.cog-genomics.org/plink2/data#merge_list
			# NEW: Also, this can be used without a reference; in that case, the newly created fileset is then treated as the reference by most other PLINK operations.
		#http://pngu.mgh.harvard.edu/~purcell/plink/dataman.shtml#mergelist

		### mege error
		#https://www.cog-genomics.org/plink2/data#merge3

		
		cmd_plink = "/cvar/jhlab/timshel/bin/plink1.9_linux_x86_64/plink --merge-list {input_merge_file} --make-bed --out {out_prefix}".format(input_merge_file=input_merge_file, out_prefix=out_prefix)
		#cmd_plink = "/cvar/jhlab/timshel/bin/plink1.9_linux_x86_64/plink --merge-list {input_merge_file} --list-duplicate-vars --out {out_prefix}".format(input_merge_file=input_merge_file, out_prefix=out_prefix)
		logger.info( "Making plink call:\n%s" % cmd_plink )

		jobname = None
		if gen_test_data:
			jobname = "merge_resolved_test_" + super_population # e.g merge_EUR
		else:
			jobname = "merge_resolved_full_" + super_population # e.g merge_EUR

		processes.append( pplaunch.LaunchBsub(cmd=cmd_plink, queue_name=queue_name, mem=mem, jobname=jobname, projectname='snpsnp', path_stdout=log_dir, file_output=None, no_output=False, email=email, email_status_notification=email_status_notification, email_report=email_report, logger=logger) ) #

	for p in processes:
		p.run()
		time.sleep(args.pause)
	return processes


def check_jobs(processes, logger):
	logger.info("PRINTING IDs")
	list_of_pids = []
	for p in processes:
		logger.info(p.id)
		list_of_pids.append(p.id)

	logger.info( " ".join(list_of_pids) )

	if args.multiprocess:
		logger.info( "Running report_status_multiprocess " )
		pplaunch.LaunchBsub.report_status_multiprocess(list_of_pids, logger) # MULTIPROCESS
	else:
		logger.info( "Running report_status" )
		pplaunch.LaunchBsub.report_status(list_of_pids, logger) # NO MULTIPROCESS




def ParseArguments():
	arg_parser = argparse.ArgumentParser(description="Python submission Wrapper")
	arg_parser.add_argument("--logger_lvl", help="Set level for logging", choices=['debug', 'info', 'warning', 'error'], default='info') # TODO: make the program read from STDIN via '-'
	arg_parser.add_argument("--multiprocess", help="Swtich; [default is false] if set use report_status_multiprocess. Requires interactive multiprocess session", action='store_true')
	#TODO: implement formatting option
	arg_parser.add_argument("--format", type=int, choices=[0, 1, 2, 3], help="Formatting option parsed to pplaunch", default=1)
	arg_parser.add_argument("--pause", type=int, help="Sleep time after run", default=0)
	
	args = arg_parser.parse_args()
	return args

def LogArguments():
	# PRINT RUNNING DESCRIPTION 
	now = datetime.datetime.now()
	logger.critical( '# ' + ' '.join(sys.argv) )
	logger.critical( '# ' + now.strftime("%a %b %d %Y %H:%M") )
	logger.critical( '# CWD: ' + os.getcwd() )
	logger.critical( '# COMMAND LINE PARAMETERS SET TO:' )
	for arg in dir(args):
		if arg[:1]!='_':
			logger.critical( '# \t' + "{:<30}".format(arg) + "{:<30}".format(getattr(args, arg)) ) ## LOGGING



###################################### Global params ######################################
#queue_name = "week" # [bhour, bweek] priority
#queue_name = "hour" # [bhour, bweek] priority
queue_name = "priority" # [bhour, bweek] priority
# priority: This queue has a per-user limit of 10 running jobs, and a run time limit of three days.
mem="20" # ---> max memory for full (EUR) = 3 GB [*Max Swap=24 GB!!!*]. Runtime=1min
	### RESULTS from EUR_chr_1 (largest chromosome)
email='joe@somemail.com' # [use an email address 'joe@somemail.com' or 'False'/'None']
email_status_notification=True # [True or False]
email_report=False # # [True or False]

current_script_name = os.path.basename(__file__).replace('.py','')

###################################### ARGUMENTS ######################################
args = ParseArguments()

#gen_test_data = True ### SUPER IMPORTANT - controls generation of test data.
gen_test_data = False ### SUPER IMPORTANT - controls generation of test data.

###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')
log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step1_merge_chromosomes_resolved" #OBS
if not os.path.exists(log_dir):
	os.mkdir(log_dir)
log_name = None
if gen_test_data:
	log_name = current_script_name + '_test'
else:
	log_name = current_script_name + '_full'


logger = pplogger.Logger(name=log_name, log_dir=log_dir, log_format=1, enabled=True).get()
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################

############################# SWITCH ##########################################

param_super_population = ["EUR", "EAS", "WAFR"]
param_chromosome = ["chr"+str(chrID) for chrID in range(1,23)+["X"]] 
	# ---> *IMPORTANT NOTE* Y-chromosome removed.




###################################### RUN FUNCTIONS ######################################
# NOW RUN FUNCTIONS
LogArguments()
#test() # test that things are ok
processes = submit()

start_time_check_jobs = time.time()
check_jobs(processes, logger) # TODO: parse multiprocess argument?
elapsed_time = time.time() - start_time_check_jobs
logger.info( "Total Runtime for check_jobs: %s s (%s min)" % (elapsed_time, elapsed_time/60) )
logger.critical( "%s: finished" % current_script_name)








