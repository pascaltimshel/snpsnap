#!/usr/bin/env python2.7
#@TODO Possibly change this

## USAGE: this script calls parse_matched_SNPs.py.
## parse_matched_SNPs.py is call with a specific freq bin to process, e.g. the bin freq0-1
## EXAMPLE call:
##
## BEWARE: the PATH of parse_matched_SNPs.py is hardcoded.


import sys
import glob
import os
import datetime
import time
import subprocess 
#sys.path.append('/home/projects/tp/tools/matched_snps/src') # Outcommented Broad 2015-02

#from queue import QueueJob,ShellUtils,ArgparseAdditionalUtils #ArgparseAdditionalUtils unused?
import pdb
import argparse

import collections


import pplaunch
import pphelper
import pplogger


############################ SETTING ZERO BUFFERING for STDOUT ######################################
# Consider this for unbuffered output. This may be useful when the function is called via run_multiple_...py
sys.stdout = os.fdopen(sys.stdout.fileno(), 'wb', 0)
batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')
#######################################################################



def run_parse(snplist_prefix, outfilename, unit_test_file):
	""" 
	One outfilename may origin from MULTIPLE batch_snplists. This is dependent on the batch_size. 
	NOTICE THE LOOP 'for snp_list in snplist_files:' 
	"""

	snplist_files = glob.glob(snplist_prefix+"*.rsID") # catching all files with CORRECT prefix
	if not os.path.exists(outfilename): # Test if already run
		status_string = "status = no previous file | {outfilename}".format(outfilename=outfilename)
		unit_test_file['NO_PREVIOUS_FILE'].append(status_string)
		#print "%s: CREATING NEW" % outfilename # OUTCOMMENTED JUNE 18 2014
		
		return True
	else:
		batch_snplist = {}
		existing_outfile = {}			
		# Read existing outfile. .tab is a 6 column file. First column is rs-number for matched_rsID
		#rs16823904      9-10    3       154081865       7       11940   ENSG00000240048 ENSG00000240068,ENSG00000174953,ENSG00000174948
		with open(outfilename, 'r') as f:
			# lines = f.readlines() # No header... # <-- BEFORE SNPsnap production v2 | *STUPID LEGACY FROM TUNE: READ WHOLE FILE INTO MEMORY!*
			#pdb.set_trace()
			#expected_cols = 10 ######################## OBS ##############################
			#expected_cols = 13 ######################## OBS - NEW JUNE 18 2014 - after adding 2 x located within (dist and ID) + 1 x LD buddies ##############################
			#expected_cols = 15 ######################## OBS - NEW JUNE 19 2014 - after adding x2 SNPsnap distance (dist and ID) ##############################
			#expected_cols = 21 ######################## OBS - NEW FEBRUARY 26 2015 - after adding 6 new columns ##############################
			expected_cols = 22 ######################## OBS - NEW FEBRUARY 27 2015 - added snp_maf ##############################
			for line in f:
				# Remove only trailing newline
				cols = line.rstrip('\n').split('\t') # tab seperated - WE MUST KNOW THIS!
				# cols[0] ==> "input SNP rs-number" (matched_rsID)
				if len(cols) == expected_cols: #hmmm, potentially bad code
					# if cols[0] in existing_outfile: pdb.set_trace()
					existing_outfile[cols[0]] = 1
				else:
					logger.critical( "***OBS*** File %s did not contain %d columns as expected." % (outfilename, expected_cols) )
					logger.critical( "Please check structure of file if you see the message repeatedly" )
					break
		#pdb.set_trace()
		for snp_list in snplist_files:
			with open(snp_list, 'r') as f:
				# rs28615451
				# rs184229306
				# rs115111187
				# rs12361890
				# lines = f.readlines()
				for line in f:
					rs_no = line.strip()
					batch_snplist[rs_no] = 1
		#pdb.set_trace()

		MAX_SNP_DEVIATION = 100 # Number of SNPs allowed to deviate | PLEASE USE THE SAME NUMBER THORUGHOUT THE PIPELINE

		LEN_batch_snplist = len(batch_snplist)
		LEN_existing_outfile = len(existing_outfile)
		DIFFERENCE = LEN_batch_snplist - LEN_existing_outfile

		if LEN_batch_snplist == LEN_existing_outfile:
			status_string = "FILE_EXISTS_OK | {outfilename}".format(outfilename=outfilename)
			unit_test_file['FILE_EXISTS_OK'].append(status_string)
			return None # Do not submit new job if files are ok!
		elif LEN_batch_snplist - MAX_SNP_DEVIATION <= LEN_existing_outfile <= LEN_batch_snplist + MAX_SNP_DEVIATION:
			logger.warning( "INSIDE run_parse() | FILE_EXISTS_DEVIATE | outfilename={outfilename}| LEN_batch_snplist={LEN_batch_snplist} | LEN_existing_outfile={LEN_existing_outfile}".format(outfilename=outfilename, LEN_batch_snplist=LEN_batch_snplist, LEN_existing_outfile=LEN_existing_outfile) )
			
			status_string = "FILE_EXISTS_DEVIATE | DIFFERENCE={DIFFERENCE} | LEN_batch_snplist={LEN_batch_snplist} | LEN_existing_outfile={LEN_existing_outfile} | {outfilename}".format(DIFFERENCE=DIFFERENCE, LEN_batch_snplist=LEN_batch_snplist, LEN_existing_outfile=LEN_existing_outfile, outfilename=outfilename)
			unit_test_file['FILE_EXISTS_DEVIATE'].append(status_string)
			return None # Do NOT submit new job if files are SEMI ok!
		else:
			logger.warning( "INSIDE run_parse() | FILE_EXISTS_DEVIATE | outfilename={outfilename}| LEN_batch_snplist={LEN_batch_snplist} | LEN_existing_outfile={LEN_existing_outfile}".format(outfilename=outfilename, LEN_batch_snplist=LEN_batch_snplist, LEN_existing_outfile=LEN_existing_outfile) )

			status_string = "*FILE_EXISTS_BAD* | DIFFERENCE={DIFFERENCE} | LEN_batch_snplist={LEN_batch_snplist} | LEN_existing_outfile={LEN_existing_outfile} | {outfilename}".format(DIFFERENCE=DIFFERENCE, LEN_batch_snplist=LEN_batch_snplist, LEN_existing_outfile=LEN_existing_outfile, outfilename=outfilename)
			unit_test_file['FILE_EXISTS_BAD'].append(status_string)
			return True # Re-run job.




# Submit
def submit(path, stat_gene_density_path):
	#prefix = os.path.abspath(path+"/ldlists/freq")
	block_str = '============================= %s ===================================' % batch_time
	#unit_test_file = {}
	unit_test_file = collections.defaultdict(list)
	# Initialyzing keys
	unit_test_file['NO_PREVIOUS_FILE']
	unit_test_file['FILE_EXISTS_OK']
	unit_test_file['FILE_EXISTS_DEVIATE']
	unit_test_file['FILE_EXISTS_BAD']

	processes = []
	for i in range(0,50,1): # 0...49. allways 50 freq bins. No problem here.
		suffix = "%s-%s"%(i,i+1) # e.g. 0-1
		#outfilename = prefix + suffix + ".tab" # e.g. ...long-path.../ldlists/freq0-1.tab
		ldfiles_prefix = os.path.abspath(path+"/ldlists/freq") + suffix
		snplist_prefix = os.path.abspath(path+"/snplists/freq") + suffix # e.g. # e.g. ...long-path.../snplist/freq0-1, where the whole file is e.g. freq9-10-part40000-50000.rsID
		outfilename = stat_gene_density_path + "/freq" + suffix + ".tab" # e.g. .;long_path../step2/1KG_full_queue/ld0.5/stat_gene_density/freq0-1.tab
		
		run = run_parse(snplist_prefix, outfilename, unit_test_file)
		
		#command = "%s --ldfiles_prefix %s --outfilename %s"%(script,"%s%s"%(prefix,suffix),outfilename) # e.g. --ldfiles_prefix becomes freq0-1
		command = "python {script2call} --ldfiles_prefix {ldfiles_prefix} --super_population {super_population} --outfilename {outfilename}".format(script2call=script2call, ldfiles_prefix=ldfiles_prefix, super_population=super_population, outfilename=outfilename) #
				
		jobname = super_population + "_" + distance_measure + "_run_parse_matched_SNPs_" + suffix # e.g. ??

		if run:
			logger.info( "will submit job for ldfiles_prefix: %s" % ldfiles_prefix )
			processes.append( pplaunch.LaunchBsub(cmd=command, queue_name=queue_name, mem=mem, jobname=jobname, projectname='snpsnap', path_stdout=log_dir, file_output=None, no_output=False, email=email, email_status_notification=email_status_notification, email_report=email_report, logger=logger) ) #
			#processes.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "run_parse_matched_SNPs_"+suffix, script_name=current_script_name) )
		else: 
			logger.info( "will NOT submit job for ldfiles_prefix: %s" % ldfiles_prefix )

		# if not os.path.exists(outfilename):
		# 		processes.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "run_parse_matched_SNPs_"+suffix, script_name=current_script_name) )
		# elif sum(1 for line in open(outfilename)) == 0: # Files are emtpy
		# 		processes.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "run_parse_matched_SNPs_"+suffix, script_name=current_script_name) )
	
	################## Display STATS ##########################
	logger.info( '\n'.join([block_str]*3) )
	logger.info( "#################### **** STATS from 'unit_test_file' **** ####################" )
	for stat_key, stat_list in unit_test_file.items():
		logger.info( "{}: {}".format( stat_key, len(stat_list) ) )
	logger.info( block_str )
	for stat_key, stat_list in unit_test_file.items():
		#logger.info( "{}: {}".format( stat_key, len(stat_list) ) )
		for ldfile in stat_list:
			logger.info( "{}\t{}".format( stat_key, ldfile ) )
		logger.info( block_str )

	################## NOW SUBMIT JOBS #######################
	for p in processes:
		p.run()

	return processes
	# ################## PRINT FAILS ##########################
	# print '\n'.join([block_str]*3)
	# print "#################### **** JOBS THAT COULD NOT BE SUBMITTED - from QueueJob **** ####################"
	# print "Number of jobs that were not submitted: %s" % len(QueueJob.QJ_job_fails_list)
	# for no, job_name in enumerate(QueueJob.QJ_job_fails_list, start=1):
	# 	print "{}\t{}".format(no, job_name)
	# print '\n'.join([block_str]*3)


###################################### ... ######################################


def check_jobs(processes, logger):
	logger.info("PRINTING IDs")
	list_of_pids = []
	for p in processes:
		logger.info(p.id)
		list_of_pids.append(p.id)

	logger.info( " ".join(list_of_pids) )

	# if args.multiprocess:
	# 	logger.info( "Running report_status_multiprocess " )
	# 	pplaunch.LaunchBsub.report_status_multiprocess(list_of_pids, logger) # MULTIPROCESS
	# else:
	logger.info( "Running report_status" )
	pplaunch.LaunchBsub.report_status(list_of_pids, logger) # NO MULTIPROCESS


def ParseArguments():
	# Parse arguments  
	arg_parser = argparse.ArgumentParser(description="Run parse_matched_SNPs.py")
	arg_parser.add_argument("--plink_matched_snps_path", \
		help="""Path for plink_matched_snps.py results which contain 3 directories [ldlists, log, snplists],
	e.g. /home/projects/tp/childrens/snpsnap/data/step2/1KG_full_queue/ld0.5/
	NB. please use symlinks in the path, i.e. do not use /net/home...""", required=True)
	#NB. Also check that the path has a trailing slash (/)
	
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
#queue_name = "hour" # [bhour, bweek] priority
#queue_name = "priority" # [bhour, bweek] priority
if os.environ["HOST"] == "gold":
	#queue_name = "MEDPOP" 
	#queue_name = "hour" # NEW altQC
	queue_name = "priority" # NEW altQC
elif os.environ["HOST"] == "copper":
	queue_name = "week"
else: # default queue
	queue_name = "week"

#queue_name = "MEDPOP" # *<--ONLY ON RHEL6-->* <-- DO NOT USE THIS QUEUE. One population generates *1900 JOBS*
# priority: This queue has a per-user limit of 10 running jobs, and a run time limit of three days.
mem="20" # gb      
	### RESULTS from EUR_chr_1 (largest chromosome)
email='pascal.timshel@gmail.com' # [use an email address 'pascal.timshel@gmail.com' or 'False'/'None']
email_status_notification=False # [True or False]
email_report=False # # [True or False]

current_script_name = os.path.basename(__file__).replace('.py','')

###################################### ARGUMENTS ######################################
args = ParseArguments()

###################################### .... ######################################
################## script2call ##################
script2call = "/cvar/jhlab/snpsnap/snpsnap/parse_matched_SNPs_broad.py"



path = os.path.abspath(args.plink_matched_snps_path) # Trailing slash are removed/corrected - NICE!
#^^^ E.g. "/home/projects/tp/tools/matched_snps/src/hapmap/ld0.5/"
#^^^ E.g. "/home/projects/tp/childrens/snpsnap/data/step2/1KG_test_thin0.1/ld0.5/"
log_dir_path = path + "/log" #PASCAL: PROBLEM fixed with extra slash
stat_gene_density_path = path + "/stat_gene_density"
if not os.path.exists(stat_gene_density_path):
	os.makedirs(stat_gene_density_path)

################## OBS: *HAAACK* Getting "UNIQUE ID" from "--plink_matched_snps_path" ##################
## Example
#os.path.basename(os.path.dirname("/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/ld0.5"))
# -->'ld0.5'
distance_measure = os.path.basename(os.path.abspath(path)) # e.g. ld0.5
super_population = os.path.basename(os.path.dirname(os.path.abspath(path))) # e.g. EUR


# The "pipeline_identifier" should contain information to form a UNIQUE identifier. This IDENTIFIER IS ONLY CONVENIENT FOR LOGGING/DEBUGGING purposes.
	# Relevant information needed --> super_population, distance_type and 



###################################### SETUP logging ######################################
#log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step2_run_parse_matched_SNPs_broad/{super_population}".format(super_population=super_population) #OBS
log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2_chrX_standalone-altQC/step2_run_parse_matched_SNPs_broad/{super_population}".format(super_population=super_population) #OBS
if not os.path.exists(log_dir):
	os.makedirs(log_dir)
log_name = current_script_name + "_{super_population}_{distance_measure}".format(super_population=super_population, distance_measure=distance_measure) #OBS

logger = pplogger.Logger(name=log_name, log_dir=log_dir, log_format=1, enabled=True).get()
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################





###################################### RUN FUNCTIONS ######################################
# NOW RUN FUNCTIONS
LogArguments()

### Submit jobs
processes = submit(path, stat_gene_density_path)

start_time_check_jobs = time.time()
# OBS: DO NOT WAIT FOR JOBS
#check_jobs(processes, logger) # TODO: parse multiprocess argument?
elapsed_time = time.time() - start_time_check_jobs
logger.info( "Total Runtime for check_jobs: %s s (%s min)" % (elapsed_time, elapsed_time/60) )
logger.critical( "%s: finished" % current_script_name)





