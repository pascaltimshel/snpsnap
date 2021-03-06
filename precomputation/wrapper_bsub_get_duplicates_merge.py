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
		### INPUT dir params ###
		input_prefix = None # correct variable scope
		if gen_test_data:
			input_prefix="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_test_merged/{super_population}/ALL.{chromosome}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes".format(super_population=super_population, chromosome="chr_merged")
		else:
			input_prefix="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_full_merged/{super_population}/ALL.{chromosome}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes".format(super_population=super_population, chromosome="chr_merged")

		input_bim = input_prefix + ".bim"

		if not os.path.exists(input_bim):
			logger.critical( "%s | input_bim: %s DOES NOT EXISTS.  Exiting..." % (super_population, input_bim) )
			#raise Exception("out_prefix files exists")
			sys.exit(0) # exit gracefully - we have allready done this computation

		### CHECKING FOR EXISTENCE OF DUPLICATES TEXT FILE - will just give a WARNING. Files will be overwritten ###
		file_duplicates = None
		if gen_test_data:
			file_duplicates="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_test_merged/{super_population}/ALL.{chromosome}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.{ext}".format(super_population=super_population, chromosome="chr_merged", ext="duplicates.txt") # OBS MUST MATCH WITH WHAT get_duplicates.py produces!
		else:
			file_duplicates="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_full_merged/{super_population}/ALL.{chromosome}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.{ext}".format(super_population=super_population, chromosome="chr_merged", ext="duplicates.txt") # OBS MUST MATCH WITH WHAT get_duplicates.py produces!

		if os.path.exists(file_duplicates):
			logger.warning( "%s | file_duplicates: %s exists. THIS FILE WILL BE overwritten" % (super_population, file_duplicates) )

		cmd_get_duplicates = "python {script2call} --input {input_bim}".format(script2call=script2call, input_bim=input_bim)
		logger.info( "making call to get_duplicates.py:\n%s" % cmd_get_duplicates )

		jobname = None
		if gen_test_data:
			jobname = "get_dup_test_" + super_population
		else:
			jobname = "get_dup_full_" + super_population

		processes.append( pplaunch.LaunchBsub(cmd=cmd_get_duplicates, queue_name=queue_name, mem=mem, jobname=jobname, projectname='snpsnp', path_stdout=log_dir, file_output=None, no_output=False, email=email, email_status_notification=email_status_notification, email_report=email_report, logger=logger) ) #

		###################################### MAKING PLINK "list duplicates" call ######################################
		# https://www.cog-genomics.org/plink2/data#list_duplicate_vars
		# https://www.cog-genomics.org/plink2/formats#dupvar

		################## Simple version --> ids-only AND suppress-first ##################
		# This version of output can be used for input to PLINK "--exclude <SNPLIST>"
		# Generates file: <prefix>.dupvar
		jobname = None
		if gen_test_data:
			jobname = "get_dup_plink_simple_test_" + super_population
		else:
			jobname = "get_dup_plink_simple_full_" + super_population
		cmd_plink = "/cvar/jhlab/timshel/bin/plink_linux_x86_64_v1.90b3d/plink --bfile {input_prefix} --list-duplicate-vars ids-only suppress-first --out {input_prefix}".format(input_prefix=input_prefix)
		logger.info( "Making SIMPLE plink call:\n%s" % cmd_plink )
		processes.append( pplaunch.LaunchBsub(cmd=cmd_plink, queue_name=queue_name, mem=mem, jobname=jobname, projectname='snpsnp', path_stdout=log_dir, file_output=None, no_output=False, email=email, email_status_notification=email_status_notification, email_report=email_report, logger=logger) ) #

		################## More "advanced" output ##################
		# Generates file: <prefix>.my-advanced.dupvar
		output_dupvar_advanced = input_prefix + ".my-advanced"

		jobname = None
		if gen_test_data:
			jobname = "get_dup_plink_advanced_test_" + super_population
		else:
			jobname = "get_dup_plink_advanced_full_" + super_population
		cmd_plink = "/cvar/jhlab/timshel/bin/plink_linux_x86_64_v1.90b3d/plink --bfile {input_prefix} --list-duplicate-vars --out {output_dupvar_advanced}".format(input_prefix=input_prefix, output_dupvar_advanced=output_dupvar_advanced)
		logger.info( "Making ADVANCED plink call:\n%s" % cmd_plink )
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
email='joe@somemail.com' # [use an email address 'joe@somemail.com' or 'False'/'None']
email_status_notification=True # [True or False]
email_report=False # # [True or False]

current_script_name = os.path.basename(__file__).replace('.py','')

###################################### ARGUMENTS ######################################
args = ParseArguments()

#gen_test_data = True 
gen_test_data = False

script2call = "/cvar/jhlab/snpsnap/snpsnap/get_duplicates.py"


###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')
log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step1_get_duplicates_merge" 
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
# OBS: no "param_chromosome"

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








