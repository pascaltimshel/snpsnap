##!/usr/bin/env python2.7

import sys
import glob
import os
import time

from queue import QueueJob,ShellUtils,ArgparseAdditionalUtils
import pdb


script = "/home/projects/tp/childrens/snpsnap/git/parse_matched_SNPs.py" # Updated path
current_script_name = os.path.basename(__file__)



# Submit
def submit():
	files = glob.glob(path_snplist+'/*.txt')
	jobs = []
	for (counter, filename) in enumerate(files, start=1):
		pheno = os.path.splitext(os.path.basename(filename))[0]
		print "processing file #%d/#%d: %s" % (counter, len(files), pheno)
		user_snps_file = filename # full path
		output_dir = path_output_main +
		N_sample_sets = "PLACE HOLDER"
		command = "{program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_cound}".format()

		run = run_parse(snplist_prefix, outfilename)
		if run:
			jobs.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, logname="wrapper_"+pheno, script_name=current_script_name) )
		# if not os.path.exists(outfilename):
		# 		jobs.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "run_parse_matched_SNPs_"+suffix, script_name=current_script_name) )
		# elif sum(1 for line in open(outfilename)) == 0: # Files are emtpy
		# 		jobs.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "run_parse_matched_SNPs_"+suffix, script_name=current_script_name) )
	for job in jobs:
		job.run()
		#time.sleep(2)

# CBS queue parameters
#queue_name = "urgent" #@TODO Change queue to idle if Pascal should run it
queue_name = "cbs" #@TODO Change queue to idle if Pascal should run it
walltime="86400" # 60*60*24=1 day
#mem_per_job="1gb" #tunes default
mem_per_job="10gb"
flags = "sharedmem"


## Constants
path_snplist = "/home/projects/tp/childrens/snpsnap/data/gwas/gwascatalog_140201_listsBIGbim"
#path_snplist = "/home/projects/tp/childrens/snpsnap/data/gwas/gwascatalog_140201_lists"

path_output_main = "/home/projects/tp/childrens/snpsnap/data/query/gwascatalog"

log_dir_path = path + "/log" #PASCAL: PROBLEM fixed with extra slash
ShellUtils.mkdirs(log_dir_path)


### Make sure that the genotype prefix is correct ###
if True:
	ans = ""
	print "*** SAFETY CHECK! ***"
	print "Plese confirm that you really want to run this job submission wrapper"
	while ans != 'yes':
	 	ans = raw_input("Confirm: ")
	print "Ok let's start..."


submit(path_snplist)








