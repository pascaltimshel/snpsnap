#!/usr/bin/env python2.7

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
sys.path.append('/home/projects2/tp/tools/matched_snps/src') #@@TODO: Why this line??
from queue import QueueJob,ShellUtils,ArgparseAdditionalUtils

def makehash():
	return collections.defaultdict(makehash) 

# Funciton to map frequency to percentile bin
def get_freq_bin(f):
	if f > 0.5:
		f = 1 - f	
	f_int = math.floor(f*float(100))
	bin = 0
	bins = range(0,50,freq_bin_size)
	for i in range(1,len(bins),1):
		if f_int >= bins[i-1] and f_int <= bins[i]:
			break
		else:
			bin += 1	
	return bin

# Funciton to read in summary statiscs and bin SNPs into MAF percentiles
def get_snps_by_freq(infilename):
	snps_by_freq = {} 
	# @@TODO freq_bin_size is unnessesary
	for bin in range(0,len(range(0,50,freq_bin_size)),1):
		snps_by_freq[bin] = []
	infile = open(infilename,'r')
	lines = infile.readlines()[1:]
	random.seed()
	random.shuffle(lines)
	for line in lines:
		words = line.strip().split()
	
		# Only consider SNPs with non-zero frequency
		if float(words[4]) > 0 and float(words[4]) < 1:
			bin = get_freq_bin(float(words[4]))

			# Add to correct bin if still space
			if len(snps_by_freq[bin]) < max_snps_per_bin:
				snps_by_freq[bin].append(words[1])
		infile.close()
	return snps_by_freq

# Funciton to save into files to be run in plink
def write_batches():
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

			for rsID_matched in snps_by_freq[bin][subbins[i]:min(subbins[i]+batch_size,len(snps_by_freq[bin]))]:
				outfile.write("%s\n"%(rsID_matched))
			outfile.close()
			batches.append(batch_id)
	return batches
	
# Function to submit jobs to queue
def submit(batch_ids):
	jobs = []
	for batch_id in batch_ids:
	
		# Test if already run
		if not os.path.exists(output_dir_path + "/ldlists/" + batch_id + ".ld"):
			command = "" # variable scope
			if args.distance_type == "kb":
				command = "plink --bfile {0}"\
								" --ld-snp-list {1}"\
								" --ld-window-kb {2}"\
								" --ld-window 99999"\
								" --out {3}/ldlists/{4}"\
								" --noweb"\
								.format(\
									genotype_prefix, \
									output_dir_path + "/snplists/"+ batch_id + ".rsID", \
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
									output_dir_path + "/snplists/"+ batch_id + ".rsID", \
									ld_cutoff, \
									output_dir_path, batch_id)
			test_run_NoSubmission = 1 # SWITCH to only print the command
			if test_run_NoSubmission:
				print command
				raise Exception('test run set to true. Exiting')
			jobs.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "plink_matched_SNPs_"+batch_id) )
	for job in jobs:
	    time.sleep(2)
	    job.run()


#pdb.set_trace()

#
# Fixed variables
#
#genotype_prefix = "/home/projects/tp/data/hapmap/phase2/hapmap_CEU_r23a" # TUNES OLD HAPMAP path/prefix
#@@TODO: INSERT PATH TO 1000 GENOMES DATA FILES
genotype_prefix = "/net/home/home/projects9/tp/childrens/snpsnap/src/results/test_thin0.001/CEU_GBR_TSI_unrelated.phase1"
#genotype_prefix = "/net/home/home/projects9/tp/childrens/snpsnap/src/results/test_thin0.05/CEU_GBR_TSI_unrelated.phase1"
max_snps_per_bin = 50000 # 50*50,000==2.5e6
batch_size = 10000 # Used to break down jobs for paralellization
freq_bin_size = 1


#
#Parse Arguments
#
arg_parser = argparse.ArgumentParser(description="Get matched SNPs")
arg_parser.add_argument("--output_dir_path", type=ArgparseAdditionalUtils.check_if_writable, help="Directory into which the output will be produced")
arg_parser.add_argument("--distance_type", help="ld or kb")
arg_parser.add_argument("--distance_cutoff", help="r2, or kb distance")
args = arg_parser.parse_args()

#
# Create directories and logging dirs:
#
#ShellUtils.mkdirs(args.output_dir_path)
if args.distance_type == "ld":
	output_dir_path = args.output_dir_path+"/ld"+str(args.distance_cutoff)
	ld_cutoff = args.distance_cutoff
if args.distance_type == "kb":
	output_dir_path = args.output_dir_path+"/kb"+str(args.distance_cutoff)
	kb_cutoff = args.distance_cutoff


ShellUtils.mkdirs(output_dir_path + "/snplists/")
ShellUtils.mkdirs(output_dir_path + "/ldlists/")
log_dir_path = output_dir_path + "/log/"
ShellUtils.mkdirs(log_dir_path)

print("Running with %s option, using cutoff %s"%(args.distance_type,args.distance_cutoff))

#
#prepare queue parameters and commands
#
##TODO@@ Adjust queue parameters??
queue_name = "cbs"
walltime="604800" # 60*60*24*7=7 days
mem_per_job="3gb"
flags = "sharedmem"

snps_by_freq = get_snps_by_freq(genotype_prefix+".frq")
batch_ids = write_batches()
submit(batch_ids)

