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

## Program outline
#1) process "raw" data using plink with user criteria
	# possibly set pthin to generate test data
#2) check for dublicates in .bim file via call to python script



def ParseArguments():
	arg_parser = argparse.ArgumentParser(description="Python submission Wrapper")
	arg_parser.add_argument("--chromosome", type=int, help="chromosome number", required=True)
	arg_parser.add_argument("--population", help="population", choices=["EUR", "EAS", "WAFR"], required=True)
	arg_parser.add_argument("--gen_test_data", help="if set, then generate a test data set", action='store_true', required=True)
	
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


###################################### ARGUMENTS ######################################
args = ParseArguments()

chromosome = args.chromosome
population = args.population
gen_test_data = args.gen_test_data
###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')

log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step1_genQCbed"
if not os.path.exists(log_dir):
	os.mkdir(log_dir)
log_name = current_script_name + ".{population}_chr{chromosome}".format(population=population, chromosome=chromosome) # this will give "logger.step1_genQCbed.EUR_chr1"

logger = pplogger.Logger(name=log_name, log_dir=log_dir, log_format=1, enabled=True).get()
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################

###################################### INITIALYZE ######################################
# NOW RUN FUNCTIONS
LogArguments()
start_time_check_jobs = time.time()


###################################### PARAMETERS ######################################
#@@@@@@@@@@@@@@@@@@ Important switch test dataset is created @@@@@@@@@
pthin=0.02 #To keep only a random e.g. 20% of SNPs. Parameter for --thin must be 0<x<1

######################################
pmaf=0.01 # Only include SNPs with MAF >= 0.01.
pgeno=0.1
phwe=0.000001 #10^-6 [phwe=0.001 default value]


### Scripts ###
script_get_duplicates = "/cvar/jhlab/snpsnap/snpsnap/get_duplicates.py"

### INPUT dir params ###
input_ped="/cvar/jhlab/snpsnap/data/step1/production_v2/{population}/ALL.chr{chromosome}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes".format(population=population, chromosome=chromosome) # OBS: this is the prefix needed in PLINK

dir_out = None # correct variable scope
if gen_test_data:
	dir_out="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_test/{population}".format(population=population)
else:
	dir_out="/cvar/jhlab/snpsnap/data/step1/production_v2_QC_full/{population}".format(population=population)

### Creating outdir
if not os.path.exists(dir_out):
	os.mkdirs(dir_out) # NOTE use of mkdirs(): all intermediate-level directories needed to contain the leaf directory

### Setting out_prefix
out_prefix = dir_out + '/' + os.path.basename(input_ped) # e.g. /cvar/jhlab/snpsnap/data/step1/production_v2_QC_full/EUR/ALL.chr1.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes

### SAFETY CHECK - checking for existence of ANY FILES with out_prefix (e.g, if --make-bed has previously been called and .bed, .bim. .fam files exists)
previous_files = glob.glob(out_prefix+'.*')
if previous_files:
	logger.critical( "%s | chr%s | out_prefix: %s seem to exists already. Will exit with status code 0 (everything ok)" % (popultation, chromosome, out_prefix) )
	logger.critical( "%s | chr%s | globbing matches:\n%s" % ( popultation, chromosome, "\n".join(previous_files) ) )
	#raise Exception("out_prefix files exists")
	sys.exit(0) # exit gracefully - we have allready done this computation


###################################### PLINK CALL - --make-bed and QC ######################################
cmd_plink = None
if gen_test_data:
	# TEST DATA dir
	cmd_plink = "plink --file {input_ped} --thin {pthin} --maf {pmaf} --geno {pgeno} --hwe {phwe} --make-bed --out {out_prefix} --silent --noweb".format(input_ped=input_ped, pthin=pthin, pmaf=pmaf, pgeno=pgeno, phwe=phwe, out_prefix=out_prefix)
else:
	# FULL DATA (--thin REMOVED)
	cmd_plink = "plink --file {input_ped} --maf {pmaf} --geno {pgeno} --hwe {phwe} --make-bed --out {out_prefix} --silent --noweb".format(input_ped=input_ped, pmaf=pmaf, pgeno=pgeno, phwe=phwe, out_prefix=out_prefix)

logger.info( "Making plink call '--make-bed and QC':\n%s" % cmd_plink )


FNULL = open(os.devnull, 'w')
p_plink = subprocess.Popen(cmd_plink, stdout=FNULL, stderr=subprocess.STDOUT, shell=True) # FULL is not needed when running PLINK in silent mode
p_plink.wait()
FNULL.close()

if p_plink.returncode != 0:
	logger.critical( "PLINK call '--make-bed and QC' returned with non-zero returncode!" )
	raise Exception("see above...")
else:
	logger.info( "PLINK call '--make-bed and QC' done" )


###################################### Remove Dublicates CALL ######################################
cmd_get_duplicates = "python {script} --input {out_prefix}.bim".format(script=script_get_duplicates, out_prefix=out_prefix) # OBS: important to add .bim
logger.info( "making call to get_duplicates.py:\n%s" % cmd_get_duplicates )

FNULL = open(os.devnull, 'w')
p_get_duplicates = subprocess.Popen(cmd_get_duplicates, stdout=FNULL, stderr=subprocess.STDOUT, shell=True) # FULL is not needed
p_get_duplicates.wait()
FNULL.close()

if p_get_duplicates.returncode != 0:
	logger.critical( "get_duplicates returned with non-zero returncode!" )
	raise Exception("see above...")
else:
	logger.info( "get_duplicates done" )

#### IMPORTANT NOTE ####
# get_duplicates.py produces a file with the name <out_prefix>.duplicates.txt with the rsIDs of duplicates. 
# THIS IS FILE IS EMPTY IF NOT DUPLICATES ARE FOUND.


###################################### END ######################################
elapsed_time = time.time() - start_time_check_jobs
logger.info( "Total Runtime for check_jobs: %s s (%s min)" % (elapsed_time, elapsed_time/60) )
logger.critical( "%s: finished" % current_script_name)








