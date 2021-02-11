#!/usr/bin/env python2.7

import sys
import glob
import os

import datetime
import time
import argparse

#from plaunch import LaunchBsub, LaunchSubprocess, HelperUtils
from pplaunch import LaunchBsub, LaunchSubprocess
from pphelper import HelperUtils
from pplogger import Logger

import re
import subprocess
import logging
#current_script_name = os.path.basename(__file__).replace('.py','')
#logging.getLogger('').addHandler(logging.NullHandler())
#logger = logging.getLogger() # This includes the submodule (launch_subprocess) logger too
#logger.setLevel(logging.ERROR)
#logger.disabled = True

#handler = logging.StreamHandler()
#handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: BLABLABLASSD %(message)s'))
#logger.addHandler(handler)


import pdb



# Submit
def submit():
	files = glob.glob(path_snplist+'/*.txt') #OBS: folder also contains "not_mapped.log"
	#files = ['/home/unix/ptimshel/git/snpsnap/samples/sample_10randSNPs_fewmatches.list']
	files.sort()
	processes = []
	for (counter, filename) in enumerate(files, start=1):
		pheno = os.path.splitext(os.path.basename(filename))[0]
		logger.info( "processing file #%d/#%d: %s" % (counter, len(files), pheno) )
		user_snps_file = filename # full path
		output_dir = path_output_sub+"/"+pheno
		HelperUtils.mkdirs(output_dir)
		#TODO: consider the potential problems with 'use' environment
		#TODO: reuse Python-2.7 && bsub [...]
			# Put this inside LaunchBsub!!
		command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(program=script2call, snplist=filename, outputdir=output_dir, N=10000, freq=1, dist=5, gene_count=5)
		processes.append( LaunchBsub(cmd=command_shell, queue_name=queue_name, walltime=walltime, mem=mem, jobname=pheno, projectname='snpsnp', path_stdout=path_stdout, file_output=pheno+'.txt', no_output=False, email=email, logger=logger) ) #
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
		LaunchBsub.report_status_multiprocess(list_of_pids, logger) # MULTIPROCESS
	else:
		logger.info( "Running report_status" )
		LaunchBsub.report_status(list_of_pids, logger) # NO MULTIPROCESS




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
			## LOGGING
			logger.critical( '# \t' + "{:<30}".format(arg) + "{:<30}".format(getattr(args, arg)) )



###################################### Global params ######################################
queue_name = "hour" # [bhour, bweek] priority
#queue_name = "priority" # [bhour, bweek] priority
walltime="59" # hh:mmm, e.g. [24:00=1day | 10:00=10hrs | 120=2hrs | 1:0=1hrs
mem="1" # gb
#email='joe@somemail.com'
email=False

script2call = "/home/unix/ptimshel/git/snpsnap/snpsnap_query.py" # Updated path
current_script_name = os.path.basename(__file__).replace('.py','')

path_snplist = "/cvar/jhlab/snpsnap/data/input_lists/gwascatalog_140201_listsBIGbim"
path_output_main = "/cvar/jhlab/snpsnap/data/query/gwascatalog"

path_output_sub = path_output_main + "/output"
HelperUtils.mkdirs(path_output_sub)
path_stdout = path_output_main + "/stdout"
HelperUtils.mkdirs(path_stdout)

###################################### ARGUMENTS ######################################
args = ParseArguments()

###################################### LOGGER ######################################
## Setup-logger
#logger = Logger(__name__, path_stdout).get() # gives __name__ == main
logger = Logger(current_script_name, path_stdout).get()
#loglevel = getattr(logging, args.logger_lvl.upper(), logging.INFO) # returns some numeric value
loglevel = getattr(logging, args.logger_lvl.upper()) # returns some numeric value
logger.setLevel(loglevel)
#logger.setLevel(logging.INFO)
#logger.setLevel(logging.WARNING)


###################################### RUN FUNCTIONS ######################################
# NOW RUN FUNCTIONS
LogArguments()
processes = submit()

start_time_check_jobs = time.time()
check_jobs(processes, logger) # TODO: parse multiprocess argument?
elapsed_time = time.time() - start_time_check_jobs
logger.info( "Total Runtime for check_jobs: %s s (%s min)" % (elapsed_time, elapsed_time/60) )
logger.critical( "%s: finished" % current_script_name)








