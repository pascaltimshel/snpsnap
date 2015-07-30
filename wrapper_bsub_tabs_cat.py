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

	for super_population in super_populations:
		logger.info( "****** RUNNING: super_population=%s *******" % super_population )
		################## Distance type loop ##################
		for distance_type in distance_types:
			logger.info( "****** RUNNING: type=%s *******" % distance_type )
			if distance_type == "ld":
				param_list = param_list_ld
			elif distance_type == "kb":
				param_list = param_list_kb
			else:
				raise Exception("Unexpected distance_type")
			################## Distance cut-off loop ##################
			for param in param_list:
				logger.info( "RUNNING: param=%s" % param )

				cmd = "python tabs_cat.py --super_population {super_population} --distance_type {distance_type} --distance_cutoff {distance_cutoff}".format(super_population=super_population, distance_type=distance_type, distance_cutoff=param)
				logger.info( "making command:\n%s" % cmd )
				
				jobname = "tabs_cat_{super_population}_{distance_type}_{distance_cutoff}".format(super_population=super_population, distance_type=distance_type, distance_cutoff=param)

				processes.append( pplaunch.LaunchBsub(cmd=cmd, queue_name=queue_name, mem=mem, jobname=jobname, projectname='snpsnap', path_stdout=log_dir, file_output=None, no_output=False, email=email, email_status_notification=email_status_notification, email_report=email_report, logger=logger) ) #

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
#queue_name = "priority" # [bhour, bweek] priority
#queue_name = "hour" # [bhour, bweek] priority
#queue_name = "week" # [bhour, bweek] priority
if os.environ["HOST"] == "gold":
	#queue_name = "MEDPOP"
	#queue_name = "priority"
	queue_name = "hour"
elif os.environ["HOST"] == "copper":
	queue_name = "week"
else: # default queue
	queue_name = "week"

# priority: This queue has a per-user limit of 10 running jobs, and a run time limit of three days.
#mem=20 # 10 GB worked for EUR/EAS 
mem=5 # 10 GB worked for EUR/EAS 
email='pascal.timshel@gmail.com' # [use an email address 'pascal.timshel@gmail.com' or 'False'/'None']
email_status_notification=False # [True or False]
email_report=False # # [True or False]

###################################### ARGUMENTS ######################################
args = ParseArguments()


############################# SWITCH ##########################################

super_populations = ["EUR"]
#super_populations = ["EAS"]
#super_populations = ["WAFR"]
distance_types = ["ld", "kb"]


param_list_ld = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
param_list_kb = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

#distance_types = ["ld"]
#param_list_ld = [0.5, 0.9]



###################################### CONSTANTS ######################################
batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')

current_script_name = os.path.basename(__file__).replace('.py','')

###################################### SETUP logging ######################################
#log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/logs_bsub_tabs_compile_priority" #OBS VARIABLE
#log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step4_wrapper_tabs_cat"
log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2_chrX_standalone-altQC/step4_wrapper_tabs_cat"
if not os.path.exists(log_dir):
	os.makedirs(log_dir)

log_name = "{current_script_name}_{timestamp}".format(current_script_name=current_script_name, timestamp=batch_time)

logger = pplogger.Logger(name=current_script_name, log_dir=log_dir, log_format=1, enabled=True).get()
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################





###################################### RUN FUNCTIONS ######################################
# NOW RUN FUNCTIONS
LogArguments()
processes = submit()

start_time_check_jobs = time.time()
check_jobs(processes, logger) # TODO: parse multiprocess argument?
elapsed_time = time.time() - start_time_check_jobs
logger.info( "Total Runtime for check_jobs: %s s (%s min)" % (elapsed_time, elapsed_time/60) )
logger.critical( "%s: finished" % current_script_name)








