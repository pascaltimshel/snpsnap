##!/usr/bin/env python2.7

import sys
import glob
import os
import time

import subprocess

import pdb


def mkdirs(file_path):
	if not os.path.exists(file_path):
	    os.makedirs(file_path)





#Popen.pid The process ID of the child process.


# Submit
def submit():
	files = glob.glob(path_snplist+'/*.txt')[0:2] #REMOVE LATER
	jobs = []
	for (counter, filename) in enumerate(files, start=1):
		pheno = os.path.splitext(os.path.basename(filename))[0]
		print "processing file #%d/#%d: %s" % (counter, len(files), pheno)
		user_snps_file = filename # full path
		output_dir = path_output_main+"/"+pheno 
		command = "{program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(program=script, snplist=filename, outputdir=output_dir, N=1000, freq=5, dist=20, gene_count=20)
		print command
		p=subprocess.Popen(command, stdin=subprocess.PIPE,stdout=subprocess.PIPE)
		jobs.append(p)
	return jobs


def display_pids(jobs):
	print "Displaying %d jobs" % len(jobs)
	for p in jobs:
		print p.pid

def listen_to_jobs(jobs):
	pass
	#exit_codes = [p.wait() for p in p1, p2] #p.communicate() #now wait
	#for p in jobs:
		#(stdout, stderr) = p.communicate()

################ Constants ############
script = "/home/unix/ptimshel/git/snpsnap/snpsnap_query.py" # Updated path
current_script_name = os.path.basename(__file__)


path_snplist = "/cvar/jhlab/snpsnap/data/input_lists/gwascatalog_140201_listsBIGbim"
#path_snplist = "/home/projects/tp/childrens/snpsnap/data/gwas/gwascatalog_140201_listsBIGbim"
#path_snplist = "/home/projects/tp/childrens/snpsnap/data/gwas/gwascatalog_140201_lists"

#path_output_main = "/home/projects/tp/childrens/snpsnap/data/query/gwascatalog"
path_output_main = "/cvar/jhlab/snpsnap/data/query/gwascatalog"

log_dir_path = path_output_main + "/log"
mkdirs(log_dir_path)

## TODO: implement argparse
# logdir
# main output dir


# if True:
# 	ans = ""
# 	print "*** SAFETY CHECK! ***"
# 	print "Plese confirm that you really want to run this job submission wrapper"
# 	while ans != 'yes':
# 	 	ans = raw_input("Confirm: ")
# 	print "Ok let's start..."


submit()








