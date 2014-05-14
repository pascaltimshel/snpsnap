#!/usr/bin/env python2.7

import sys
import glob
import os
import time

#import subprocess
from plaunch import LaunchBsub, LaunchSubprocess, HelperUtils

import re
import logging
#current_script_name = os.path.basename(__file__).replace('.py','')
#logging.getLogger('').addHandler(logging.NullHandler())
#logger = logging.getLogger() # This includes the submodule (launch_subprocess) logger too
#logger.setLevel(logging.ERROR)
#logger.disabled = True

#handler = logging.StreamHandler()
#handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: BLABLABLASSD %(message)s'))
#logger.addHandler(handler)


import pdb



# Submit
def submit():
	files = glob.glob(path_snplist+'/*.txt') #[0:2], OBS: folder also contains "not_mapped.log"
	#files = ['/home/unix/ptimshel/git/snpsnap/samples/sample_10randSNPs_fewmatches.list']
	files.sort()
	processes = []
	for (counter, filename) in enumerate(files, start=1):
		filename = re.sub(r'[()]', '', filename) #### OBS: changing file names!
		pheno = os.path.splitext(os.path.basename(filename))[0]
		print "processing file #%d/#%d: %s" % (counter, len(files), pheno)
		user_snps_file = filename # full path
		output_dir = path_output_sub+"/"+pheno
		HelperUtils.mkdirs(output_dir)
		#TODO: consider the potential problems with 'use' environment
		command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(program=script2call, snplist=filename, outputdir=output_dir, N=1000, freq=5, dist=20, gene_count=20)
		processes.append( LaunchBsub(cmd=command_shell, queue_name=queue_name, walltime=walltime, mem=mem, jobname=pheno, projectname='snpsnp', logdir=log_dir_path, log_root=current_script_name, file_output=pheno+'.txt', no_output=False, email=email) ) #
		#cmd, queue_name, walltime, mem, jobname='NoJobName', logdir=os.getcwd(), log_root='unknown_root_name', file_output= __name__+'.tmp.out', no_output=False, email=False
	for p in processes:
		sys.exit(0)
		p.run()
	return processes


################ Constants ############
#queue_name = "hour" # [bhour, bweek] priority
queue_name = "priority" # [bhour, bweek] priority
walltime="1" # hours
mem="1"
email='pascal.timshel@gmail.com'

script2call = "/home/unix/ptimshel/git/snpsnap/snpsnap_query.py" # Updated path

current_script_name = os.path.basename(__file__).replace('.py','')


path_snplist = "/cvar/jhlab/snpsnap/data/input_lists/gwascatalog_140201_listsBIGbim"
path_output_main = "/cvar/jhlab/snpsnap/data/query/gwascatalog"

path_output_sub = path_output_main + "/output"
HelperUtils.mkdirs(path_output_sub)
log_dir_path = path_output_main + "/log"
HelperUtils.mkdirs(log_dir_path)

processes = submit()

print "PRINTING IDs"
for p in processes:
	print p.id


## TODO: implement argparse
# logdir
# main output dir








