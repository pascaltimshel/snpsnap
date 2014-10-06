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
		subprocess.Popen(["vcftools", "-help"], stdout=FNULL, stderr=subprocess.STDOUT)
	except Exception as e:
		raise Exception("Could not find vcftools as executable on path. Please check that you have used 'use VCFtools'. Error msg: %s" % e.message)


def submit():
	processes = []
	for super_population in param_super_population:
		logger.info( "****** RUNNING: type=%s *******" % super_population )
		for param in param_list:
			logger.info( "RUNNING: param=%s" % param )
			gzvcf_file = "ALL.chr{chr_no}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz".format(chr_no=param)
			gzvcf_in = input_dir_base + '/' + gzvcf_file
			keep = input_dir_base + '/' + "my.panel.population.{super_population}.list".format(super_population=super_population)
			
			out_dir = output_dir_base + '/' + super_population
			if not os.path.exists(out_dir):
				os.mkdir(out_dir)
			out_file = out_dir + '/' + "ALL.chr{chr_no}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes".format(chr_no=param)
			
			if glob.glob(out_file+".*"): # if the list is non-empty. will match .ped, .map and .log files
				logger.warning( "%s | chr%s | out_file: %s seem to exists already. Skipping it..." % (super_population, param, out_file) )
				logger.warning( "%s | chr%s | globbing matches:\n%s" % ( super_population, param, "\n".join(glob.glob(out_file+".*")) ) )
				continue

			#cmd = ["vcftools", "--vcf", gzvcf_in, "--out", out_file, "--keep", keep, "--plink"]
			cmd = "vcftools --gzvcf {gzvcf_in} --out {out_file} --keep {keep} --plink".format(gzvcf_in=gzvcf_in, out_file=out_file, keep=keep)
			logger.info( "making command:\n%s" % cmd )
			
			jobname = super_population + "_chr_" + str(param) # e.g EUR_chr_21

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
queue_name = "priority" # [bhour, bweek] priority
#queue_name = "hour" # [bhour, bweek] priority
# priority: This queue has a per-user limit of 10 running jobs, and a run time limit of three days.
mem="4" # gb      
	### RESULTS from EUR_chr_1 (largest chromosome) - on priority
	# CPU time   :   2928.47 sec. ---> *** later on this took more than 3600s - when running on hour and the job was terminated!
	#    Max Memory :      2488 MB
	#    Max Swap   :      2609 MB
	### chr_21 only took 400 sec and Max Memory 440 MB
email='pascal.timshel@gmail.com' # [use an email address 'pascal.timshel@gmail.com' or 'False'/'None']
email_status_notification=True # [True or False]
email_report=False # # [True or False]

current_script_name = os.path.basename(__file__).replace('.py','')

###################################### ARGUMENTS ######################################
args = ParseArguments()

###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')
log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step1_vfc2ped" #OBS VARIABLE
logger = pplogger.Logger(name=current_script_name, log_dir=log_dir, log_format=1, enabled=True).get()
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################

############################# SWITCH ##########################################
param_super_population = ["EUR", "EAS", "WAFR"]
param_list = range(1,23) # produces 1, 2, .., 21, 22

#param_super_population = ["EUR", "WAFR"]
#param_list = [1, 21] # produces 1, 2, .., 21, 22


##############################################################################

input_dir_base = "/cvar/jhlab/snpsnap/data/genotypes_raw_production_v2/ftp"
output_dir_base = "/cvar/jhlab/snpsnap/data/step1/production_v2"

if not os.path.exists(output_dir_base):
	logger.warning( "UPS: output path %s does not exist. Fix it! Exiting..." % output_dir_base )
	sys.exit(1)

if not os.path.exists(log_dir):
	logger.warning( "UPS: log dir %s does not exist. Fix it! Exiting..." % log_dir )
	sys.exit(1)



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








