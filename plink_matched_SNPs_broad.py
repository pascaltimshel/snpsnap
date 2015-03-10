#!/usr/bin/env python2.7

## Use this line on padawan
## #!/home/people/timshel/.local/bin/python
## Use this line else
## #!/usr/bin/env python2.7

# TODO: Check that all files have been run properly
# TODO: Do not run with 10mb on either side but only 1 mb

import re
import os
import sys
import string
import math
import argparse
from datetime import datetime
import time
import random
import collections
from sets import Set
import pdb 
import os.path

import pplaunch
import pplogger
import pphelper

#sys.path.append('/home/projects/tp/tools/matched_snps/src') #@@TODO: Why this line??
#from queue import QueueJob,ShellUtils,ArgparseAdditionalUtils


###################################### Example call ######################################

#python plink_matched_SNPs_broad.py --distance_type ld --distance_cutoff 0.5 --super_population EUR


##########################################################################################

current_script_name = os.path.basename(__file__)

############################ SETTING ZERO BUFFERING for STDOUT ######################################
# Consider this for unbuffered output. This may be useful when the function is called via run_multiple_...py
#sys.stdout = os.fdopen(sys.stdout.fileno(), 'wb', 0)
#######################################################################


def makehash():
	return collections.defaultdict(makehash) 

# Funciton to map frequency to percentile bin
def get_freq_bin(f):
	f_pct = float(f)*float(100) # just to make sure that f is float..
	if f_pct > 50:
		f_pct = 100 - f_pct
		#TODO: logger.info( error code if f > 0.5	 )
	#bins = range(0,50,freq_bin_size) # Tune orig. [0,1,...,48,49] ==> len=50
	bins = range(0,51,freq_bin_size) # NEW. [0,1,...,49,50] ==> len=51
	bin = None # default value
	for i in range(0,len(bins)-1,1): # looping over BIN INDEX. [0,1,...,48,49] ==> len=50
		if bins[i] < f_pct <= bins[i+1]: # bins right-closed and left open intervals ===> ]a;b]
			bin = i
			break
	if bin == None:
		raise Exception( "ERROR: did not find any bin to put SNP with MAF=%s and (f_pct=%s). Bug in code or SNP freq. Raising execption...\n" % (f, f_pct) )
	# REMEMBER: f_pct = 0 is NOT included in any bins since IT SHOULD NOT EXIST. (SNPs with freq = 0 does not make sense)
	# Function returns "lower boundary" of bin, i.e:
	# 0<f_pct<=1 ==> bin=0
	# 1<f_pct<=2 ==> bin=1
	# ....
	# 48<f_pct<=49 ==> bin=48
	# 49<f_pct<=50 ==> bin=49
	return bin



# Funciton to read in summary statiscs and bin SNPs into MAF percentiles
def get_snps_by_freq(infilename):
	logger.info( "called get_snps_by_freq()" )
	snps_by_freq = {} 
	# @@TODO freq_bin_size is unnessesary
	for bin in range(0,len(range(0,50,freq_bin_size)),1):
		snps_by_freq[bin] = [] # TODO: use containers.defaultdict[list] instead
	logger.info( "get_snps_by_freq(): now reading infilename %s" % infilename )
	infile = open(infilename,'r')
	lines = infile.readlines()[1:] # skip header in frequency file
	infile.close()
	random.seed(1) # IMPORTANT TO SET SEED to reproduce results and make sure that batches are written in the same way always!
	random.shuffle(lines)
	for line in lines:
		words = line.strip().split()
		### Pink1: .frq file
		# CHR          SNP   A1   A2          MAF  NCHROBS
		#   1   rs58108140    A    G       0.2052      536
		#   1  rs189107123    G    C      0.01306      536
		#   1  rs180734498    T    C       0.1343      536
		#   1  rs144762171    C    G      0.02425      536
		#   1  rs201747181    T   TC      0.01119      536
		#   1  rs151276478    C    T      0.01306      536
		### Pink2 .frq file
		# CHR                                  SNP   A1   A2          MAF  NCHROBS
		#   1                              1:11008    G    C      0.08847     1006
		#   1                              1:11012    G    C      0.08847     1006
		#   1                              1:13110    A    G      0.05666     1006
		#   1                          rs201725126    G    T       0.1869     1006
		# Only consider SNPs with non-zero frequency
		if float(words[4]) > 0 and float(words[4]) < 1:
			bin = get_freq_bin(float(words[4]))

			# Add to correct bin if still space
			if len(snps_by_freq[bin]) < max_snps_per_bin:
				snps_by_freq[bin].append(words[1])
	logger.info( "get_snps_by_freq(): done" )
	return snps_by_freq

def write_batch_size_distribution_file():
	#TODO: fix to local variables
	# added Pascal 04/21/2014
	with open(log_dir_path+"/bin_size_distribution.txt", 'w') as f:
		f.write("bin\tsize\n")
		for bin in snps_by_freq: # bin is integer, e.g 0,1,2...
			f.write("%s\t%s\n" % (bin, len(snps_by_freq[bin])) )


# Funciton to save into files to be run in plink
def write_batches():
	logger.info( "called write_batches()" )
	batches = []
	# Construct batch for each frequency bin
	bins = range(0,50,freq_bin_size)
	for bin in range(0,len(bins),1):

		subbins = range(0,len(snps_by_freq[bin]),batch_size)
		# Break into sub bins
		for i in range(0,len(subbins),1):
			batch_id = "freq" + str(bins[bin]) + "-" + str(bins[bin]+freq_bin_size) + "-part" + str(subbins[i]) + "-" + str(min(subbins[i]+batch_size,len(snps_by_freq[bin])))  
			outfile_str = output_dir_path + "/snplists/" +  batch_id + ".rsID"
			outfile = open(outfile_str,'w')

			logger.info( "Bin %d | writing batch file: %s" % (bin, outfile_str) )
			for rsID_matched in snps_by_freq[bin][subbins[i]:min(subbins[i]+batch_size,len(snps_by_freq[bin]))]:
				outfile.write("%s\n"%(rsID_matched))
			outfile.close()
			batches.append(batch_id)
			# break ############### TEMPORARY 06/13/2014 ############################
			############### NOTE: the outer loop should also be 'break'
	# break ############### TEMPORARY 06/13/2014 ############################
	logger.info( "write_batches(): function DONE" )
	return batches

def get_plink_command(batch_id):
	#TODO: make the args local and pass them to this function
	command = "" # variable scope
	snp_list = output_dir_path + "/snplists/"+ batch_id + ".rsID"
	if distance_type == "kb":
		command = "/cvar/jhlab/timshel/bin/plink1.9_linux_x86_64/plink"\
						" --bfile {0}"\
						" --r2"\
						" --ld-snp-list {1}"\
						" --ld-window-kb {2}"\
						" --ld-window 99999"\
						" --out {3}/ldlists/{4}"\
						.format(\
							genotype_prefix, \
							snp_list, \
							kb_cutoff, \
							output_dir_path, batch_id)
	if distance_type == "ld":
		command = "/cvar/jhlab/timshel/bin/plink1.9_linux_x86_64/plink"\
						" --bfile {0}"\
						" --r2"\
						" --ld-snp-list {1}"\
						" --ld-window-kb 1000"\
						" --ld-window-r2 {2}"\
						" --ld-window 99999"\
						" --out {3}/ldlists/{4}"\
						.format(\
							genotype_prefix, \
							snp_list, \
							ld_cutoff, \
							output_dir_path, batch_id)
	return (command, snp_list)



def run_ldfile(batch_id, snp_list, unit_test_file):
	""" 
	One-to-One mapping: 
	One batch_snplist gives rise to one outfilename (ld file)
	"""

	outfilename = output_dir_path + "/ldlists/" + batch_id + ".ld"
	if not os.path.exists(outfilename): # Test if already run

		status_string = "status = no previous outfilename | {outfilename}".format(outfilename=outfilename)
		unit_test_file['NO_PREVIOUS_FILE'].append(status_string)
		#unit_test_file['NO_PREVIOUS_FILE'].append(outfilename)
		
		#logger.info( "%s: CREATING NEW" % outfilename ## USE THIS!!! June 2014 )
		#logger.info( "*** outfilename %s\nNOT exists. Appending jobs for batch ID %s to QueueJob.py... ***" % (outfilename, batch_id) )
		return True # submit job is there is no existing outfilename
	else:
		batch_snplist = {}
		existing_outfile = {}
		# Read existing ld file
		with open(outfilename, 'r') as f:
			# CHR_A         BP_A        SNP_A  CHR_B         BP_B        SNP_B           R2
 			# 1      1011095   rs11810785      1      1011095   rs11810785            1
 			# 1      1011095   rs11810785      1      1025301    rs9442400      0.61996
			
			# plink ALWAYS outputs a line containing with input SNP, i.e. a line with an LD buddy to itself. SEE above example. 
			# this enables us to assume len(existing_outfile) == len(batch_snplist)
			#lines = f.readlines()[1:] # SKIP HEADER!! # <-- BEFORE SNPsnap production v2 | *STUPID LEGACY FROM TUNE: READ WHOLE FILE INTO MEMORY!*
			expected_cols = 7
			next(f) # SKIP HEADER!
			for line in f:
				cols = line.strip().split()
				# cols[2] ==> input SNP rs-number
				# cols[5] ==> LD buddy rs-number
				if len(cols) == expected_cols:
					existing_outfile[cols[2]] = 1
				else:
					logger.critical( "***OBS*** File %s did not contain %d columns as expected." % (outfilename, expected_cols) )
					logger.critical( "Please check structure of file if you see the message repeatedly" )
					logger.critical( 'Breaking out if loop' )
					break
		# Read batch SNP list file
		with open(snp_list, 'r') as f:
			# rs28615451
			# rs184229306
			# rs115111187
			# rs12361890
			# lines = f.readlines()
			for line in f:
				rs_no = line.strip()
				batch_snplist[rs_no] = 1


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



# Function to submit jobs to queue
def submit(batch_ids):
	block_str = '========================================================================'
	#unit_test_file = {}
	unit_test_file = collections.defaultdict(list)
	# Initialyzing keys
	unit_test_file['NO_PREVIOUS_FILE']
	unit_test_file['FILE_EXISTS_OK']
	unit_test_file['FILE_EXISTS_DEVIATE']
	unit_test_file['FILE_EXISTS_BAD']

	processes = []
	for batch_id in batch_ids:
		#logger.info( "INSIDE LOOP IN submit(): running batch_id={}".format(batch_id) )
		
		(command, snp_list) = get_plink_command(batch_id)
		run = run_ldfile(batch_id, snp_list, unit_test_file)
		if run: # run is True --> file is defect or does not exists
			logger.info( "will ===***===SUBMIT JOB===***=== for batch_id: %s" % batch_id )
			### BROAD ####
			jobname = super_population + "_" + distance_type + "_" + distance_cutoff + "_" + batch_id # batch_id --> e.g. freq0-1-part-0-1000
			processes.append( pplaunch.LaunchBsub(cmd=command, queue_name=queue_name, mem=mem, jobname=jobname, projectname='snpsnp', path_stdout=log_dir_path, file_output=None, no_output=False, email=email, email_status_notification=email_status_notification, email_report=email_report, logger=None) ) # if "logger" evaluates to false in a boolean context, then a new logger will be created
			

			### CBS ####
			# flags parameter not currenlty used because script is run on protein-s0
			#jobs.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "plink_matched_SNPs_"+batch_id, script_name=current_script_name, job_name=batch_id) )
		else: # file is exists and are ok
			logger.info( "will NOT submit job for batch_id: %s" % batch_id )
		#break ### TEMPORARY 06/13/2014 ####
	
	################## logger.info( STATS ########################## )
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

	################## logger.info( FAILS ########################## )
	### UNCOMMENDTED FROM BROAD
	# logger.info( '\n'.join([block_str]*3) )
	# logger.info( "#################### **** JOBS THAT COULD NOT BE SUBMITTED - from QueueJob **** ####################" )
	# logger.info( "Number of jobs that were not submitted: %s" % len(QueueJob.QJ_job_fails_list) )
	# for no, job_name in enumerate(QueueJob.QJ_job_fails_list, start=1):
	# 	logger.info( "{}\t{}".format(no, job_name) )
	# logger.info( '\n'.join([block_str]*3) )



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





#
# Fixed variables
#
#genotype_prefix = "/home/projects/tp/data/hapmap/phase2/hapmap_CEU_r23a" # TUNES OLD HAPMAP path/prefix
#PATH TO 1000 GENOMES DATA FILES
#REMEMBER genotype prefix is not just the DIR - it also includes the FILE PREFIXES
#genotype_prefix = "/home/projects/tp/childrens/snpsnap/data/step1/test_thin0.02/CEU_GBR_TSI_unrelated.phase1" ######## TEST RUN!!!
#genotype_prefix = "/home/projects/tp/childrens/snpsnap/data/step1/full_no_pthin/CEU_GBR_TSI_unrelated.phase1"
#genotype_prefix = "/home/projects/tp/childrens/snpsnap/data/step1/full_no_pthin_rmd/CEU_GBR_TSI_unrelated.phase1_dup_excluded" # duplicates removed!
#genotype_prefix = "/home/projects/tp/childrens/snpsnap/data/step1/test_thin0.02_rmd/CEU_GBR_TSI_unrelated.phase1_dup_excluded" # TEST DATA!!! duplicates removed!
#max_snps_per_bin = 50000 # 50*50,000==2.5e6 - DEFAULT VALUE

max_snps_per_bin = float('Inf') # no limit - use all snps
#batch_size = 10000 # ---> USED AT CBS Used to break down jobs for paralellization - DEFAULT VALUE
batch_size = 10000000000 # the maximal freq bin is about 1.2e6=1200000
freq_bin_size = 1


#
#Parse Arguments
#
arg_parser = argparse.ArgumentParser(description="Get matched SNPs")
#arg_parser.add_argument("--output_dir_path", help="Directory into which the output will be produced", required=True)
arg_parser.add_argument("--multiprocess", help="Swtich; [default is false] if set use report_status_multiprocess. Requires interactive multiprocess session", action='store_true')

arg_parser.add_argument("--distance_type", help="ld or kb", required=True)
arg_parser.add_argument("--distance_cutoff", help="r2, or kb distance", required=True)
arg_parser.add_argument("--super_population", help="[EUR,EAS,WARF]", required=True)
## Important argument: # e.g. #genotype_prefix = "/home/projects/tp/childrens/snpsnap/data/step1/full_no_pthin/CEU_GBR_TSI_unrelated.phase1"
#arg_parser.add_argument("--genotype_prefix", help="path and file prefix to genetype data", required=True) 
args = arg_parser.parse_args()

distance_type = args.distance_type
distance_cutoff = args.distance_cutoff


### NEW BROAD PATH - dependent on super_population
super_population = args.super_population
genotype_prefix = "/cvar/jhlab/snpsnap/data/step1/production_v2_QC_full_merged_duplicate_rm/{super_population}/ALL.{chromosome}.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes".format(super_population=super_population, chromosome="chr_merged")

###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')
log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step2_plink_matched_SNPs_broad/{super_population}".format(super_population=super_population) #OBS
if not os.path.exists(log_dir):
	os.makedirs(log_dir)
log_name = current_script_name + "_{super_population}_{distance_type}_{distance_cutoff}".format(super_population=super_population, distance_type=distance_type, distance_cutoff=distance_cutoff) #OBS

logger = pplogger.Logger(name=log_name, log_dir=log_dir, log_format=1, enabled=True).get()
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################



output_dir_path = "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/{super_population}".format(super_population=super_population) # NO trailing slash (/)!
if not os.path.exists(output_dir_path):
	os.makedirs(output_dir_path)

#
# Create directories and logging dirs:
#
#TODO: fix this structure! Not pretty!
#ShellUtils.mkdirs(args.output_dir_path)
if distance_type == "ld":
	output_dir_path = output_dir_path+"/ld"+str(distance_cutoff)
	ld_cutoff = distance_cutoff
if distance_type == "kb":
	output_dir_path = output_dir_path+"/kb"+str(distance_cutoff)
	kb_cutoff = distance_cutoff



### Make sure that the genotype prefix is correct ###
# *** SAFETY CHECK! ***"
# You specifed --output_dir_path to be: %s" % output_dir_path
# The genotype_prefix is set to: %s" % genotype_prefix
# You will overwrite files in /snplists and /ldlists if the parameters in step1/ and step2/ do not match"
# Plese confirm that this is the correct paths to use by typing 'yes'"

#########################################################################

path_snplists = output_dir_path + "/snplists/"
path_ldlists = output_dir_path + "/ldlists/"
log_dir_path = output_dir_path + "/log" # Pascal - FIXED ERROR. : before it was /log/
for path in [path_snplists, path_ldlists, log_dir_path]:
	if not os.path.exists(path):
		os.makedirs(path)

# ShellUtils.mkdirs(output_dir_path + "/snplists/") #TODO: remove trailing slash and see if it still works
# ShellUtils.mkdirs(output_dir_path + "/ldlists/") #TODO: remove trailing slash and see if it still works
# log_dir_path = output_dir_path + "/log" # Pascal - FIXED ERROR. : before it was /log/
# ShellUtils.mkdirs(log_dir_path)

logger.info(("Running with %s option, using cutoff %s"%(distance_type,distance_cutoff)) )


###################################### Global params ######################################
queue_name = "week" # [bhour, bweek] priority
#queue_name = "hour" # [bhour, bweek] priority
#queue_name = "priority" # [bhour, bweek] priority
#queue_name = "MEDPOP" # OBS: ONLY RUN THIS ON RHEL6 System!
# priority: This queue has a per-user limit of 10 running jobs, and a run time limit of three days.
#mem="30" # 20 GB worked for EUR+EAS!
mem="120" # ?? GB worked for WAFR!
email='pascal.timshel@gmail.com' # [use an email address 'pascal.timshel@gmail.com' or 'False'/'None']
email_status_notification=False # [True or False]
email_report=False # # [True or False]

current_script_name = os.path.basename(__file__).replace('.py','')



#if os.listdir(output_dir_path + "/snplists") == []: # 
#	logger.info( "Path " + output_dir_path + "/snplists" + " is empty - going to write snp batches" )
snps_by_freq = get_snps_by_freq(genotype_prefix+".frq")
write_batch_size_distribution_file()


################## Wrie batches ##################
start_time_write_batches = time.time()
batch_ids = write_batches()
elapsed_time_write_batches = time.time() - start_time_write_batches
logger.info( "Total Runtime for WRITING BATCHES: %s s (%s min)" % (elapsed_time_write_batches, elapsed_time_write_batches/60) )

#else:
#	logger.info( "Path " + output_dir_path + "/snplists" + " is NOT empty. SKIPPING writing batches" )
logger.info( "Will call submit()" )
processes = submit(batch_ids)

start_time_check_jobs = time.time()
# OBS: CONSIDER NOT WAITING FOR JOBS. WAITING for jobs takes a lot of time from the validation ("run_multiple_plink_matched_SNPs_broad.py")
#check_jobs(processes, logger) # TODO: parse multiprocess argument?
elapsed_time = time.time() - start_time_check_jobs
logger.info( "Total Runtime for check_jobs: %s s (%s min)" % (elapsed_time, elapsed_time/60) )
logger.critical( "%s: finished" % current_script_name)



