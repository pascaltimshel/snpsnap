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


def submit():
	processes = []
	for super_population in param_super_population:
		logger.info( "****** RUNNING: type=%s *******" % super_population )

		### *.missnp FILE.
		### *IMPORTANT*: this file is assumed to be in the production_v2_QC_{test,full}_merged DIRECTORY.
		### NOTICE THE extension of the file: "-merge.missnp"
		### NOTICE: all chromosomes form the same super_population share the same file_merge_conflicts
		file_merge_conflicts = None
		if gen_test_data:
			file_merge_conflicts="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_test_merged/{super_population}/ALL.{chromosome}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes-merge.missnp".format(super_population=super_population, chromosome="chr_merged")
		else:
			file_merge_conflicts="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_full_merged/{super_population}/ALL.{chromosome}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes-merge.missnp".format(super_population=super_population, chromosome="chr_merged")

		################## Loop over chromosomes ##################
		for chromosome in param_chromosome:
			logger.info( "RUNNING: chromosome=%s" % chromosome )

			### INPUT dir params ###
			input_bed = None # correct variable scope
			if gen_test_data:
				input_bed="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_test/{super_population}/ALL.{chromosome}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes".format(super_population=super_population, chromosome=chromosome)
			else:
				input_bed="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_full/{super_population}/ALL.{chromosome}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes".format(super_population=super_population, chromosome=chromosome)

			if not os.path.exists(input_bed+'.bed'):
				logger.critical( "%s | chr%s | input_bed: %s DOES NOT EXISTS.  Exiting..." % (super_population, chromosome, input_bed) )
				#raise Exception("out_prefix files exists")
				raise Exception("see logging message")


			### Output dir
			dir_out = None # correct variable scope
			if gen_test_data:
				dir_out="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_test_merged-step2_conflicts_excluded/{super_population}".format(super_population=super_population)
			else:
				dir_out="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_full_merged-step2_conflicts_excluded/{super_population}".format(super_population=super_population)

			### Creating outdir
			if not os.path.exists(dir_out):
				os.makedirs(dir_out) # NOTE use of makedirs(): all intermediate-level directories needed to contain the leaf directory

			### Setting out_prefix
			out_prefix = dir_out + "/ALL.{chromosome}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes".format(super_population=super_population, chromosome=chromosome)

			### CHECKING FOR EXISTENCE OF MERGED_EXCLUDED PLINK FILES (.bed) ###
			if os.path.exists(out_prefix+'.bed'):
				logger.warning( "%s | chr%s | out_prefix: %s exists. THIS FILE WILL BE overwritten" % (super_population, chromosome, out_prefix) )

			cmd_plink = "/cvar/jhlab/timshel/bin/plink1.9_linux_x86_64/plink --bfile {input_bed} --exclude {file_merge_conflicts} --make-bed --out {out_prefix}".format(input_bed=input_bed, file_merge_conflicts=file_merge_conflicts, out_prefix=out_prefix)
			#cmd_plink = "/cvar/jhlab/timshel/bin/plink1.9_linux_x86_64/plink --merge-list {input_merge_file} --list-duplicate-vars --out {out_prefix}".format(input_merge_file=input_merge_file, out_prefix=out_prefix)
			logger.info( "Making plink call:\n%s" % cmd_plink )

			jobname = None
			if gen_test_data:
				jobname = "exclude_merge_conflicts_test_" + super_population + "_" + chromosome # e.g get_dup_EUR_chr21
			else:
				jobname = "exclude_merge_conflicts_full_" + super_population + "_" + chromosome # e.g get_dup_EUR_chr21

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
queue_name = "priority" # [bhour, bweek] priority
#queue_name = "week" # [bhour, bweek] priority
#queue_name = "hour" # [bhour, bweek] priority
# priority: This queue has a per-user limit of 10 running jobs, and a run time limit of three days.
mem="10" # gb      
	### RESULTS from EUR_chr_1 (largest chromosome)
email='pascal.timshel@gmail.com' # [use an email address 'pascal.timshel@gmail.com' or 'False'/'None']
email_status_notification=True # [True or False]
email_report=False # # [True or False]

current_script_name = os.path.basename(__file__).replace('.py','')

###################################### ARGUMENTS ######################################
args = ParseArguments()

#gen_test_data = True 
gen_test_data = False


###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')
log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step1_exclude_merge_conflicts" 
if not os.path.exists(log_dir):
	os.mkdir(log_dir)
log_name = None
if gen_test_data:
	log_name = current_script_name + '_test'
else:
	log_name = current_script_name + '_full'

logger = pplogger.Logger(name=current_script_name, log_dir=log_dir, log_format=1, enabled=True).get()
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################

############################# SWITCH ##########################################

param_super_population = ["EUR", "EAS", "WAFR"]
#param_chromosome = range(1,23) # produces 1, 2, .., 21, 22
param_chromosome = ["chr"+str(chrID) for chrID in range(1,23)+["X"]] 
	# ---> *IMPORTANT NOTE* Y-chromosome removed. Plink2 (and plink1) fails to process it because all variants are removed after filtering

###################################### PARAMETERS ######################################

###################################### RUN FUNCTIONS ######################################
# NOW RUN FUNCTIONS
LogArguments()
processes = submit()

start_time_check_jobs = time.time()
check_jobs(processes, logger) # TODO: parse multiprocess argument?
elapsed_time = time.time() - start_time_check_jobs
logger.info( "Total Runtime for check_jobs: %s s (%s min)" % (elapsed_time, elapsed_time/60) )
logger.critical( "%s: finished" % current_script_name)








