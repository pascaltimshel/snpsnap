#!/usr/bin/env python2.7

import re
import os
import sys
import string
import math
import argparse
import subprocess 
from datetime import datetime
import time
import random
import collections
from sets import Set
import pdb; 
import glob

def makehash():
	return collections.defaultdict(makehash) 

class ArgparseAdditionalUtils:
    @classmethod
    def verify_file_path_exists_return_abs(cls, file_path):
        if not os.path.exists(file_path):
            msg="File path: %s is invalid"%file_path
            raise argparse.ArgumentTypeError(msg)
        else:
            return os.path.abspath(file_path)
        
    @classmethod
    def check_if_writable(cls, file_path):
        if not os.access(file_path, os.W_OK):
            msg="File path: %s is not writable"%file_path
            raise argparse.ArgumentTypeError(msg)
        else:
            return os.path.abspath(file_path)
        
class ShellUtils:
    @classmethod
    def mkdirs(cls, file_path):
        if not os.path.exists(file_path):
            os.makedirs(file_path)

    @classmethod
    def gen_timestamp(cls):
        return datetime.now().strftime("%d_%m_%y_%H_%M_%S")

class QueueJob:

    def __init__(self, cmd, logdir, queue, walltime, mem, flags):
        self.id = -1
        self.is_running = False
        self.status = ""
        self.qcmd = "xmsub -de -o %s -e %s -r y -q %s -l mem=%s,walltime=%s,flags=%s"%(logdir, logdir, queue, mem, walltime,flags) 
        self.cmd = cmd
        
    def run(self):
        print self.qcmd + " " + self.cmd
        out = subprocess.check_output(self.qcmd + " " + self.cmd,shell=True)
        self.id = out.strip()
        print self.id

        
    def check_status(self):
        out = subprocess.check_output("checkjob %s" % self.id, shell=True)
        pattern = re.compile("^State:\W(\w*)",flags=re.MULTILINE)
        match = pattern.search(out)
        if match: 
            self.status = match.group(1)
            if self.status == "Running":
                self.is_running = True
            elif self.status == "Completed":
                self.is_running = False
        else:
            print out

# Function to submit jobs to queue
def submit(snp_file):
	batch_ids = []
	tmp = snp_file.split('/')
	batch_ids.append(tmp[len(tmp)-1].split('.')[0])
	jobs = []
	for batch_id in batch_ids:
		os.system("cp " + snp_file + " " + output_dir_path + "/snplists/"+ batch_id + ".rsID")
		command = "plink --bfile %s --ld-snp-list %s --ld-window-kb %s --ld-window-r2 %s --ld-window 99999 --out %s/ldlists/%s --noweb "%(genotype_path, output_dir_path + "/snplists/"+ batch_id + ".rsID", kb_cutoff, ld_cutoff, output_dir_path, batch_id)
		
		print command
		jobs.append( QueueJob(command, tmp_dir_path, queue_name, walltime, mem_per_job , flags) )
	
	for job in jobs:
	    time.sleep(2)
	    job.run()

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

#
# Fixed variables
#
genotype_path = "/home/projects/tp/data/hapmap/phase2/hapmap_CEU_r23a"
freq_bin_size = 1

#
#Parse Arguments
#
arg_parser = argparse.ArgumentParser(description="Get regions for observed SNPs")
arg_parser.add_argument("--output_dir_path", type=ArgparseAdditionalUtils.check_if_writable, help="Directory into which the output will be produced")
arg_parser.add_argument("--distance_type", help="ld or kb")
arg_parser.add_argument("--distance_cutoff", help="r2, or kb distance")
arg_parser.add_argument("--snp_file", help="File with SNPs") 
args = arg_parser.parse_args()

#
#Create directories and logging dirs:
#
#ShellUtils.mkdirs(args.output_dir_path)
if args.distance_type == "ld":
	output_dir_path = args.output_dir_path+"/ld"+str(args.distance_cutoff)
	ld_cutoff = args.distance_cutoff
	kb_cutoff = 1000 #1 MB
if args.distance_type == "kb":
	output_dir_path = args.output_dir_path+"/kb"+str(args.distance_cutoff)
	ld_cutoff = 0
	kb_cutoff = args.distance_cutoff
ShellUtils.mkdirs(output_dir_path)
ShellUtils.mkdirs(output_dir_path + "/snplists/")
ShellUtils.mkdirs(output_dir_path + "/ldlists/")
log_dir_path = output_dir_path + "/log/"
tmp_dir_path = log_dir_path + "/tmp_" + ShellUtils.gen_timestamp()
ShellUtils.mkdirs(tmp_dir_path)

print("Running with %s option, using cutoff %s"%(args.distance_type,args.distance_cutoff))

#
# Prepare queue parameters and commands
#
queue_name = "urgent"
walltime="604800" # 60*60*24*7=7 days
mem_per_job="3gb"
flags = "sharedmem"

submit(args.snp_file)
