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
sys.path.append('/home/projects/tp/tools/matched_snps/src') #@@TODO: Why this line??
from queue import QueueJob,ShellUtils,ArgparseAdditionalUtils

current_script_name = os.path.basename(__file__)

############################ SETTING ZERO BUFFERING for STDOUT ######################################
# Consider this for unbuffered output. This may be useful when the function is called via run_multiple_...py
sys.stdout = os.fdopen(sys.stdout.fileno(), 'wb', 0)
#######################################################################


def makehash():
	return collections.defaultdict(makehash) 

# Funciton to map frequency to percentile bin
def get_freq_bin(f):
	f_pct = float(f)*float(100) # just to make sure that f is float..
	if f_pct > 50:
		f_pct = 100 - f_pct
		#TODO: print error code if f > 0.5	
	#bins = range(0,50,freq_bin_size) # Tune orig. [0,1,...,48,49] ==> len=50
	bins = range(0,51,freq_bin_size) # NEW. [0,1,...,49,50] ==> len=51
	bin = None # default value
	for i in range(0,len(bins)-1,1): # looping over BIN INDEX. [0,1,...,48,49] ==> len=50
		if bins[i] < f_pct <= bins[i+1]: # bins right-closed and left open intervals ===> ]a;b]
			bin = i
			break
	if bin == None:
		sys.stderr.write( "ERROR: did not find any bin to put SNP with MAF=%s and (f_pct=%s). Bug in code or SNP freq. Exiting...\n" % (f, f_pct) )
		sys.exit(1)
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
	print "called get_snps_by_freq()"
	snps_by_freq = {} 
	# @@TODO freq_bin_size is unnessesary
	for bin in range(0,len(range(0,50,freq_bin_size)),1):
		snps_by_freq[bin] = [] # TODO: use containers.defaultdict[list] instead
	print "get_snps_by_freq(): now reading infilename %s" % infilename
	infile = open(infilename,'r')
	lines = infile.readlines()[1:] # skip header in frequency file
	infile.close()
	random.seed(1) # IMPORTANT TO SET SEED to reproduce results and make sure that batches are written in the same way always!
	random.shuffle(lines)
	for line in lines:
		words = line.strip().split()
	
		# Only consider SNPs with non-zero frequency
		if float(words[4]) > 0 and float(words[4]) < 1:
			bin = get_freq_bin(float(words[4]))

			# Add to correct bin if still space
			if len(snps_by_freq[bin]) < max_snps_per_bin:
				snps_by_freq[bin].append(words[1])
	print "get_snps_by_freq(): done"
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
	print "called write_batches()"
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

			print "Bin %d | writing batch file: %s" % (bin, outfile_str)
			for rsID_matched in snps_by_freq[bin][subbins[i]:min(subbins[i]+batch_size,len(snps_by_freq[bin]))]:
				outfile.write("%s\n"%(rsID_matched))
			outfile.close()
			batches.append(batch_id)
			# break ############### TEMPORARY 06/13/2014 ############################
			############### NOTE: the outer loop should also be 'break'
	# break ############### TEMPORARY 06/13/2014 ############################
	print "write_batches(): function DONE"
	return batches

def get_plink_command(batch_id):
	#TODO: make the args local and pass them to this function
	command = "" # variable scope
	snp_list = output_dir_path + "/snplists/"+ batch_id + ".rsID"
	if args.distance_type == "kb":
		command = "plink --bfile {0}"\
						" --ld-snp-list {1}"\
						" --ld-window-kb {2}"\
						" --ld-window 99999"\
						" --out {3}/ldlists/{4}"\
						" --noweb"\
						.format(\
							genotype_prefix, \
							snp_list, \
							kb_cutoff, \
							output_dir_path, batch_id)
	if args.distance_type == "ld":
		command = "plink --bfile {0}"\
						" --ld-snp-list {1}"\
						" --ld-window-kb 1000"\
						" --ld-window-r2 {2}"\
						" --ld-window 99999"\
						" --out {3}/ldlists/{4}"\
						" --noweb"\
						.format(\
							genotype_prefix, \
							snp_list, \
							ld_cutoff, \
							output_dir_path, batch_id)
	return (command, snp_list)



def run_ldfile(batch_id, snp_list, unit_test_file):
	ldfile = output_dir_path + "/ldlists/" + batch_id + ".ld"
	if not os.path.exists(ldfile): # Test if already run
		unit_test_file['NO_PREVIOUS_FILE'].append(ldfile)
		#print "%s: CREATING NEW" % ldfile ## USE THIS!!! June 2014
		#print "*** LDfile %s\nNOT exists. Appending jobs for batch ID %s to QueueJob.py... ***" % (ldfile, batch_id)
		return True # submit job is there is no existing ldfile
	else:
		batch_snplist = {}
		existing_ld_snplist = {}
		# Read existing ld file
		with open(ldfile, 'r') as f:
			# CHR_A         BP_A        SNP_A  CHR_B         BP_B        SNP_B           R2
 			# 1      1011095   rs11810785      1      1011095   rs11810785            1
 			# 1      1011095   rs11810785      1      1025301    rs9442400      0.61996
			
			# plink ALWAYS outputs a line containing with input SNP, i.e. a line with an LD buddy to itself. SEE above example. 
			# this enables us to assume len(existing_ld_snplist) == len(batch_snplist)
			lines = f.readlines()[1:] # SKIP HEADER!!
			expected_cols = 7
			for line in lines:
				cols = line.strip().split()
				# cols[2] ==> input SNP rs-number
				# cols[5] ==> LD buddy rs-number
				if len(cols) == expected_cols:
					existing_ld_snplist[cols[2]] = 1
				else:
					print "***OBS*** File %s did not contain %d columns as expected." % (ldfile, expected_cols)
					print "Please check structure of file if you see the message repeatedly"
					print 'Breaking out if loop'
					break
		# Read batch SNP list file
		with open(snp_list, 'r') as f:
			# rs28615451
			# rs184229306
			# rs115111187
			# rs12361890
			lines = f.readlines()
			for line in lines:
				rs_no = line.strip()
				batch_snplist[rs_no] = 1
		if len(existing_ld_snplist) == len(batch_snplist):
			unit_test_file['FILE_EXISTS_OK'].append(ldfile)
			#print "%s: OK" % ldfile ## USE THIS!!! June 2014
			
			#print "LDfile %s\nExists and are validated for batch ID %s. Not appending any jobs to QueueJob.py..." % (ldfile, batch_id)
			return None # Do not submit new job if files are ok!
		else:
			unit_test_file['FILE_EXISTS_BAD'].append(ldfile)
			#print "%s: BAD FILE EXISTS. MAKING NEW" % ldfile ## USE THIS!!! June 2014

			#print "LDfile %s\n*** Exists but are NOT ok! Running job for batch ID %s ***" % (ldfile, batch_id)
			return True # Re-run job.


# Function to submit jobs to queue
def submit(batch_ids):
	block_str = '========================================================================'
	#unit_test_file = {}
	unit_test_file = collections.defaultdict(list)
	# Initialyzing keys
	unit_test_file['NO_PREVIOUS_FILE']
	unit_test_file['FILE_EXISTS_OK']
	unit_test_file['FILE_EXISTS_BAD']

	jobs = []
	for batch_id in batch_ids:
		(command, snp_list) = get_plink_command(batch_id)
		run = run_ldfile(batch_id, snp_list, unit_test_file)
		if run: # run is True --> file is defect or does not exists
			jobs.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "plink_matched_SNPs_"+batch_id, script_name=current_script_name, job_name=batch_id) )
		else: # file is exists and are ok
			pass
		#break ### TEMPORARY 06/13/2014 ####
	
	################## PRINT STATS ##########################
	print '\n'.join([block_str]*3)
	print "#################### **** STATS from 'unit_test_file' **** ####################"
	for stat_key, stat_list in unit_test_file.items():
		print "{}: {}".format( stat_key, len(stat_list) )
	print block_str
	for stat_key, stat_list in unit_test_file.items():
		#print "{}: {}".format( stat_key, len(stat_list) )
		for ldfile in stat_list:
			print "{}\t{}".format( stat_key, ldfile )
		print block_str

	################## NOW SUBMIT JOBS #######################
	for job in jobs:
		time.sleep(2)
		job.run()
		#break ### TEMPORARY 06/13/2014 ####

	################## PRINT FAILS ##########################
	print '\n'.join([block_str]*3)
	print "#################### **** JOBS THAT COULD NOT BE SUBMITTED - from QueueJob **** ####################"
	print "Number of jobs that were not submitted: %s" % len(QueueJob.QJ_job_fails_list)
	for no, job_name in enumerate(QueueJob.QJ_job_fails_list, start=1):
		print "{}\t{}".format(no, job_name)
	print '\n'.join([block_str]*3)

#
# Fixed variables
#
#genotype_prefix = "/home/projects/tp/data/hapmap/phase2/hapmap_CEU_r23a" # TUNES OLD HAPMAP path/prefix
#PATH TO 1000 GENOMES DATA FILES
#REMEMBER genotype prefix is not just the DIR - it also includes the FILE PREFIXES
#genotype_prefix = "/home/projects/tp/childrens/snpsnap/data/step1/test_thin0.02/CEU_GBR_TSI_unrelated.phase1" ######## TEST RUN!!!
#genotype_prefix = "/home/projects/tp/childrens/snpsnap/data/step1/full_no_pthin/CEU_GBR_TSI_unrelated.phase1"
genotype_prefix = "/home/projects/tp/childrens/snpsnap/data/step1/full_no_pthin_rmd/CEU_GBR_TSI_unrelated.phase1_dup_excluded" # duplicates removed!
#genotype_prefix = "/home/projects/tp/childrens/snpsnap/data/step1/test_thin0.02_rmd/CEU_GBR_TSI_unrelated.phase1_dup_excluded" # TEST DATA!!! duplicates removed!
#max_snps_per_bin = 50000 # 50*50,000==2.5e6 - DEFAULT VALUE
max_snps_per_bin = float('Inf') # no limit - use all snps
batch_size = 10000 # Used to break down jobs for paralellization - DEFAULT VALUE
freq_bin_size = 1


#
#Parse Arguments
#
arg_parser = argparse.ArgumentParser(description="Get matched SNPs")
arg_parser.add_argument("--output_dir_path", \
	type=ArgparseAdditionalUtils.check_if_writable, \
	help="Directory into which the output will be produced", \
	required=True)
arg_parser.add_argument("--distance_type", help="ld or kb", required=True)
arg_parser.add_argument("--distance_cutoff", help="r2, or kb distance", required=True)
## Important argument: # e.g. #genotype_prefix = "/home/projects/tp/childrens/snpsnap/data/step1/full_no_pthin/CEU_GBR_TSI_unrelated.phase1"
#arg_parser.add_argument("--genotype_prefix", help="path and file prefix to genetype data", required=True) 
args = arg_parser.parse_args()


#
# Create directories and logging dirs:
#
#TODO: fix this structure! Not pretty!
#ShellUtils.mkdirs(args.output_dir_path)
if args.distance_type == "ld":
	output_dir_path = args.output_dir_path+"/ld"+str(args.distance_cutoff)
	ld_cutoff = args.distance_cutoff
if args.distance_type == "kb":
	output_dir_path = args.output_dir_path+"/kb"+str(args.distance_cutoff)
	kb_cutoff = args.distance_cutoff



### Make sure that the genotype prefix is correct ###
if False:
	ans = ""
	print "*** SAFETY CHECK! ***"
	print "You specifed --output_dir_path to be: %s" % output_dir_path
	print "The genotype_prefix is set to: %s" % genotype_prefix
	print "You will overwrite files in /snplists and /ldlists if the parameters in step1/ and step2/ do not match"
	print "Plese confirm that this is the correct paths to use by typing 'yes'"
	while ans != 'yes':
	 	ans = raw_input("Confirm: ")
	print "Ok let's start..."


ShellUtils.mkdirs(output_dir_path + "/snplists/") #TODO: remove trailing slash and see if it still works
ShellUtils.mkdirs(output_dir_path + "/ldlists/") #TODO: remove trailing slash and see if it still works
log_dir_path = output_dir_path + "/log" # Pascal - FIXED ERROR. : before it was /log/
ShellUtils.mkdirs(log_dir_path)

print("Running with %s option, using cutoff %s"%(args.distance_type,args.distance_cutoff))

#
#prepare queue parameters and commands
#
##TODO@@ Adjust queue parameters??
queue_name = "cbs" # default - 06/15/2014
#queue_name = "idle" 
#walltime="604800" # 60*60*24*7=7 days
walltime="86400" # 60*60*24=24 hours - 06/15/2014
#mem_per_job="15gb" #=>> PBS: job killed: mem job total 4323312 kb exceeded limit 3145728 kb
mem_per_job="8gb"
#walltime="86400" # 60*60*24=1 day
#mem_per_job="1gb"
flags = "sharedmem"




#if os.listdir(output_dir_path + "/snplists") == []: # 
#	print "Path " + output_dir_path + "/snplists" + " is empty - going to write snp batches"
snps_by_freq = get_snps_by_freq(genotype_prefix+".frq")
write_batch_size_distribution_file()

batch_ids = write_batches()
#else:
#	print "Path " + output_dir_path + "/snplists" + " is NOT empty. SKIPPING writing batches"
submit(batch_ids)

