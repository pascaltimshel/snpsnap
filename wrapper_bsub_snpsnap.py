#!/usr/bin/env python2.7

import sys
import glob
import os
import time

#import subprocess
from launch_subprocess import LaunchSubprocess,HelperUtils

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
		pheno = os.path.splitext(os.path.basename(filename))[0]
		print "processing file #%d/#%d: %s" % (counter, len(files), pheno)
		user_snps_file = filename # full path
		output_dir = path_output_sub+"/"+pheno
		HelperUtils.mkdirs(output_dir)
		command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(program=script2call, snplist=filename, outputdir=output_dir, N=1000, freq=5, dist=20, gene_count=20)
		#command_seq = "--user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(snplist=filename, outputdir=output_dir, N=1000, freq=5, dist=20, gene_count=20)
		#print command_shell
		processes.append( LaunchSubprocess(cmd=command_shell, logdir=log_dir_path, log_root=current_script_name, file_output=pheno+'.txt', tag=pheno) ) #
		#time.sleep(1)
		
		# run = run_parse(snplist_prefix, outfilename)
		# if run:
		# 	jobs.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, logname="wrapper_"+pheno, script_name=current_script_name) )
		

	for p in processes:
		#p.run_Log() # writes stdout and stdout to "file_output" file
		p.run_Pipe()
	return processes


################ Constants ############
#queue_name = "urgent" #@TODO Change queue to idle if Pascal should run it
queue_name = "cbs" #@TODO Change queue to idle if Pascal should run it
walltime="86400" # 60*60*24=1 day
#mem_per_job="1gb" #tunes default
mem_per_job="10gb"
flags = "sharedmem"

script2call = "/home/unix/ptimshel/git/snpsnap/snpsnap_query.py" # Updated path

current_script_name = os.path.basename(__file__).replace('.py','')


path_snplist = "/cvar/jhlab/snpsnap/data/input_lists/gwascatalog_140201_listsBIGbim"
path_output_main = "/cvar/jhlab/snpsnap/data/query/gwascatalog"

path_output_sub = path_output_main + "/output"
HelperUtils.mkdirs(path_output_sub)
log_dir_path = path_output_main + "/log"
HelperUtils.mkdirs(log_dir_path)

processes = submit()

# run_Pipe() method calls
for p in processes:
	p.get_pid()

with open(path_output_main+'/gwastable.tab', 'w') as f: 
	for p in processes:
		lines = p.process_communicate_and_read_pipe_lines()
		for (i, line) in enumerate(lines):
			#print line
			if "# rating_few_matches" in line:
				row = "{}\t{}".format(p.tag, lines[i+1]) # next line
				print row
				f.write(row+"\n")


for p in processes:
	p.process_check_returncode()




## TODO: implement argparse
# logdir
# main output dir








