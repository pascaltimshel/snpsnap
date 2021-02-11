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

def test():
	try:
		FNULL = open(os.devnull, 'w')
		subprocess.Popen(["plink", "--silent", "--noweb"], stdout=FNULL, stderr=subprocess.STDOUT)
		FNULL.close()
	except Exception as e:
		raise Exception("Could not find plink as executable on path. Please check that you have used 'use Plink' (this is version 1.07 [USE IT!]; 'use PLINK' gives version v1.08p). Error msg: %s" % e.message)


def submit():
	processes = []
	for super_population in param_super_population:
		logger.info( "****** RUNNING: type=%s *******" % super_population )
		for param in param_list:
			logger.info( "RUNNING: param=%s" % param )

			### FULL DATA
			#cmd = "python {script2call} --chromosome {param} --population {super_population}".format(script2call=script2call, param=param, super_population=super_population)
			
			### TEST DATA
			cmd = "python {script2call} --chromosome {param} --population {super_population} --gen_test_data".format(script2call=script2call, param=param, super_population=super_population)
			logger.info( "making command:\n%s" % cmd )
			
			jobname = "QCbed_" + super_population + "_chr_" + str(param) # e.g QCbed_EUR_chr_21

			processes.append( pplaunch.LaunchBsub(cmd=cmd, queue_name=queue_name, mem=mem, jobname=jobname, projectname='snpsnp', path_stdout=log_dir, file_output=None, no_output=False, email=email, email_status_notification=email_status_notification, email_report=email_report, logger=logger) ) #

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
	arg_parser.add_argument("--pause", type=int, help="Sleep time after run", default=2)
	
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
queue_name = "hour" # [bhour, bweek] priority
# priority: This queue has a per-user limit of 10 running jobs, and a run time limit of three days.
mem="10" # gb      
	### RESULTS from EUR_chr_1 (largest chromosome)
email='joe@somemail.com' # [use an email address 'joe@somemail.com' or 'False'/'None']
email_status_notification=True # [True or False]
email_report=False # # [True or False]

current_script_name = os.path.basename(__file__).replace('.py','')

###################################### ARGUMENTS ######################################
args = ParseArguments()

###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')
log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step1_genQCbed" #OBS: PLEASE MAKE THIS DIR MATCH TO THE dir in gen_QCbed
if not os.path.exists(log_dir):
	logger.warning( "UPS: log dir %s does not exist. I will create it for you..." % log_dir )
	os.mkdir(log_dir)
logger = pplogger.Logger(name=current_script_name, log_dir=log_dir, log_format=1, enabled=True).get()
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################

script2call = "/cvar/jhlab/snpsnap/snpsnap/gen_QCbed.py"
############################# SWITCH ##########################################
# param_super_population = ["EUR", "EAS", "WAFR"]
# param_list = range(1,23) # produces 1, 2, .., 21, 22

param_super_population = ["EUR", "WAFR"]
param_list = [1, 21]


###################################### RUN FUNCTIONS ######################################
# NOW RUN FUNCTIONS
LogArguments()
test() # test that things are ok
processes = submit()

start_time_check_jobs = time.time()
check_jobs(processes, logger) # TODO: parse multiprocess argument?
elapsed_time = time.time() - start_time_check_jobs
logger.info( "Total Runtime for check_jobs: %s s (%s min)" % (elapsed_time, elapsed_time/60) )
logger.critical( "%s: finished" % current_script_name)








