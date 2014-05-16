#!/usr/bin/env python2.7

import sys
import glob
import os
import time

#from plaunch import LaunchBsub, LaunchSubprocess, HelperUtils
from pplaunch import LaunchBsub, LaunchSubprocess
from pphelper import HelperUtils
from pplogger import Logger

import re
import subprocess
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
	files = glob.glob(path_snplist+'/*.txt')[0:10] #OBS: folder also contains "not_mapped.log"
	#files = ['/home/unix/ptimshel/git/snpsnap/samples/sample_10randSNPs_fewmatches.list']
	files.sort()
	processes = []
	for (counter, filename) in enumerate(files, start=1):
		pheno = os.path.splitext(os.path.basename(filename))[0]
		logger.info( "processing file #%d/#%d: %s" % (counter, len(files), pheno) )
		user_snps_file = filename # full path
		output_dir = path_output_sub+"/"+pheno
		HelperUtils.mkdirs(output_dir)
		#TODO: consider the potential problems with 'use' environment
		command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(program=script2call, snplist=filename, outputdir=output_dir, N=10000, freq=1, dist=5, gene_count=5)
		processes.append( LaunchBsub(cmd=command_shell, queue_name=queue_name, walltime=walltime, mem=mem, jobname=pheno, projectname='snpsnp', path_stdout=path_stdout, file_output=pheno+'.txt', no_output=False, email=email, logger=logger) ) #
	for p in processes:
		p.run()
		time.sleep(5)
	return processes

def check_jobs(processes, logger):
	logger.info("PRINTING IDs")
	list_of_pids = []
	for p in processes:
		logger.info(p.id)
		list_of_pids.append(p.id)

	logger.info( " ".join(list_of_pids) )
	#LaunchBsub.report_status(list_of_pids, logger)
	LaunchBsub.report_status_multiprocess(list_of_pids, logger)

	logger.info( "############ %s IS DONE ###############" % current_script_name)



################ Constants ############
queue_name = "hour" # [bhour, bweek] priority
#queue_name = "priority" # [bhour, bweek] priority
walltime="59" # hh:mmm, e.g. [24:00=1day | 10:00=10hrs | 120=2hrs | 1:0=1hrs
mem="1" # gb
#email='pascal.timshel@gmail.com'
email=False

script2call = "/home/unix/ptimshel/git/snpsnap/snpsnap_query.py" # Updated path
current_script_name = os.path.basename(__file__).replace('.py','')


path_snplist = "/cvar/jhlab/snpsnap/data/input_lists/gwascatalog_140201_listsBIGbim"
path_output_main = "/cvar/jhlab/snpsnap/data/query/gwascatalog"

path_output_sub = path_output_main + "/output"
HelperUtils.mkdirs(path_output_sub)
path_stdout = path_output_main + "/stdout"
HelperUtils.mkdirs(path_stdout)

## Setup-logger
#logger = Logger(__name__, path_stdout).get() # gives __name__ == main
logger = Logger(current_script_name, path_stdout).get()
#logger.setLevel(logging.WARNING)
logger.setLevel(logging.INFO)


# NOW RUN FUNCTIONS
processes = submit()
check_jobs(processes, logger)

