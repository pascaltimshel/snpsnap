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
from datetime import datetime
import time
import subprocess 
sys.path.append('/home/projects/tp/tools/matched_snps/src')
from queue import QueueJob

import pdb
import argparse


#script = "/home/projects/tp/tools/matched_snps/src/parse_matched_SNPs.py" # Tunes old path
script = "/home/projects/tp/childrens/snpsnap/git/parse_matched_SNPs.py" # Updated path
current_script_name = os.path.basename(__file__)


# Submit
def submit(path):
	prefix = os.path.abspath(path+"/ldlists/freq")
	jobs = []
	for i in range(0,50,1): # 0...49. allways 50 freq bins. No problem here.
		suffix = "%s-%s"%(i,i+1) # e.g. 0-1
		outfilename = prefix + suffix + ".tab" # e.g. ...long-path.../ldlists/freq0-1.tab
		command = "%s --ldfiles_prefix %s --outfilename %s"%(script,"%s%s"%(prefix,suffix),outfilename) # e.g. --ldfiles_prefix becomes freq0-1
		if not os.path.exists(outfilename):
				jobs.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "run_parse_matched_SNPs_"+suffix, script_name=current_script_name) )
		elif sum(1 for line in open(outfilename)) == 0: # Files are emtpy
				jobs.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "run_parse_matched_SNPs_"+suffix, script_name=current_script_name) )

	for job in jobs:
		job.run()
		time.sleep(2)

# CBS queue parameters
#queue_name = "urgent" #@TODO Change queue to idle if Pascal should run it
queue_name = "cbs" #@TODO Change queue to idle if Pascal should run it
walltime="86400" # 60*60*24=1 day
#mem_per_job="1gb" #tunes default
mem_per_job="10gb"
flags = "sharedmem"

# Parse arguments  
arg_parser = argparse.ArgumentParser(description="Run parse_matched_SNPs.py")
arg_parser.add_argument("--plink_matched_snps_path", \
	help="""Path for plink_matched_snps.py results which contain 3 directories [ldlists, log, snplists],
e.g. /home/projects/tp/childrens/snpsnap/data/step2/1KG_full_queue/ld0.5/
NB. please use symlinks in the path, i.e. do not use /net/home...
NB. Also check that the path has a trailing slash (/)""", required=True)
args = arg_parser.parse_args()

path = os.path.abspath(args.plink_matched_snps_path) # Remember a trailing slash??
#^^^ E.g. "/home/projects/tp/tools/matched_snps/src/hapmap/ld0.5/"
#^^^ E.g. "/home/projects/tp/childrens/snpsnap/data/step2/1KG_test_thin0.1/ld0.5/"
log_dir_path = path + "/log" #PASCAL: PROBLEM fixed with extra slash

### Make sure that the genotype prefix is correct ###
ans = ""
print "*** SAFETY CHECK! ***"
print "You specifed --plink_matched_snps_path to be: %s" % args.plink_matched_snps_path
print "Plese confirm that this is the correct path to use by typing 'yes'"
while ans != 'yes':
 	ans = raw_input("Confirm: ")
print "Ok let's start..."


submit(path)

