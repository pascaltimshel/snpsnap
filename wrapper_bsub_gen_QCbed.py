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
		for chromosome in param_chromosome:
			logger.info( "RUNNING: chromosome=%s" % chromosome )

			### INPUT dir params ###
			input_ped="/cvar/jhlab/snpsnap/data/step1/production_v2/{super_population}/ALL.chr{chromosome}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes".format(super_population=super_population, chromosome=chromosome) # OBS: this is the prefix needed in PLINK

			dir_out = None # correct variable scope
			if gen_test_data:
				dir_out="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_test/{super_population}".format(super_population=super_population)
			else:
				dir_out="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_full/{super_population}".format(super_population=super_population)

			### Creating outdir
			if not os.path.exists(dir_out):
				os.makedirs(dir_out) # NOTE use of makedirs(): all intermediate-level directories needed to contain the leaf directory

			### Setting out_prefix
			out_prefix = dir_out + '/' + os.path.basename(input_ped) # e.g. /cvar/jhlab/snpsnap/data/step1/production_v2_QC_full/EUR/ALL.chr1.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes

			### SAFETY CHECK - checking for existence of .PED file with out_prefix (e.g, if --make-bed has previously been called and .bed, .bim. .fam files exists)
			#previous_files = glob.glob(out_prefix+'.*')
			if os.path.exists(out_prefix+'.bed'): 
				logger.critical( "%s | chr%s | out_prefix: %s.ped exists already. Skipping this..." % (super_population, chromosome, out_prefix) )
				#logger.critical( "%s | chr%s | globbing matches:\n%s" % ( super_population, chromosome, "\n".join(previous_files) ) )
				#raise Exception("out_prefix files exists")
				#sys.exit(0) # exit gracefully - we have allready done this computation
				continue


			###################################### PLINK CALL - --make-bed and QC ######################################
			cmd_plink = None
			if gen_test_data:
				# TEST DATA dir
				cmd_plink = "plink --file {input_ped} --thin {pthin} --maf {pmaf} --geno {pgeno} --hwe {phwe} --make-bed --out {out_prefix} --noweb".format(input_ped=input_ped, pthin=pthin, pmaf=pmaf, pgeno=pgeno, phwe=phwe, out_prefix=out_prefix)
			else:
				# FULL DATA (--thin REMOVED)
				cmd_plink = "plink --file {input_ped} --maf {pmaf} --geno {pgeno} --hwe {phwe} --make-bed --out {out_prefix} --noweb".format(input_ped=input_ped, pmaf=pmaf, pgeno=pgeno, phwe=phwe, out_prefix=out_prefix)
			logger.info( "Making call '--make-bed and QC':\n%s" % cmd_plink )

			jobname = None
			if gen_test_data:
				jobname = "QCbed_test_" + super_population + "_chr_" + str(chromosome) # e.g QCbed_EUR_chr_21
			else:
				jobname = "QCbed_full_" + super_population + "_chr_" + str(chromosome) # e.g QCbed_EUR_chr_21

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
queue_name = "priority" # [bhour, bweek] priority
# priority: This queue has a per-user limit of 10 running jobs, and a run time limit of three days.
mem="10" # gb      
	### RESULTS from EUR_chr_1 (largest chromosome)
email='pascal.timshel@gmail.com' # [use an email address 'pascal.timshel@gmail.com' or 'False'/'None']
email_status_notification=True # [True or False]
email_report=False # # [True or False]

current_script_name = os.path.basename(__file__).replace('.py','')

###################################### ARGUMENTS ######################################
args = ParseArguments()

#gen_test_data = True ### SUPER IMPORTANT - controls generation of test data.
gen_test_data = False ### SUPER IMPORTANT - controls generation of test data.

###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')
log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step1_genQCbed" #OBS
if not os.path.exists(log_dir):
	logger.warning( "UPS: log dir %s does not exist. I will create it for you..." % log_dir )
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
param_chromosome = range(1,23) # produces 1, 2, .., 21, 22

#param_super_population = ["EUR", "WAFR"]
#param_chromosome = range(1,23)
#param_chromosome = [1, 21]


###################################### PARAMETERS ######################################
#@@@@@@@@@@@@@@@@@@ Important switch test dataset is created @@@@@@@@@
pthin=0.02 #To keep only a random e.g. 20% of SNPs. Parameter for --thin must be 0<x<1

######################################
pmaf=0.01 # Only include SNPs with MAF >= 0.01.
pgeno=0.1
phwe=0.000001 #10^-6 [phwe=0.001 default value]



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








