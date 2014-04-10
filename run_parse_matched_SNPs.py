#!/usr/bin/env python2.7

import sys
import glob
import os
from datetime import datetime
import time
import subprocess 
sys.path.append('/home/projects/tp/tools/matched_snps/src')
from queue import QueueJob

script = "/home/projects/tp/tools/matched_snps/src/parse_matched_SNPs.py"

# Submit
def submit(path):

	prefix = os.path.abspath(path+"/ldlists/freq")
	jobs = []
	for i in range(0,50-1,1):

		suffix = "%s-%s"%(i,i+1)
		outfilename = prefix + suffix + ".tab" 
		command = "%s --ldfiles_prefix %s --outfilename %s"%(script,"%s%s"%(prefix,suffix),outfilename)

		if not os.path.exists(outfilename):
				jobs.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "run_parse_matched_SNPs_"+suffix) )
		elif sum(1 for line in open(outfilename)) == 0:
				jobs.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "run_parse_matched_SNPs_"+suffix) )

	for job in jobs:
		job.run()
		time.sleep(1)

# CBS queue parameters
queue_name = "urgent"
walltime="86400" # 60*60*24=1 day
mem_per_job="1gb"
flags = "sharedmem"

path = os.path.abspath(sys.argv[1]) # E.g. "/home/projects/tp/tools/matched_snps/src/hapmap/ld0.5/"
log_dir_path = path + "/log/"
submit(path)

