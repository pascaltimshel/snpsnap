#!/usr/bin/env python2.7

import sys
import glob
import os
import time

from pplaunch import LaunchBsub, LaunchSubprocess
from pphelper import HelperUtils
from pplogger import Logger

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
		logger.info( "processing file #%d/#%d: %s" % (counter, len(files), pheno) )
		user_snps_file = filename # full path
		output_dir = path_output_sub+"/"+pheno
		HelperUtils.mkdirs(output_dir)
		command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(program=script2call, snplist=filename, outputdir=output_dir, N=10000, freq=10, dist=25, gene_count=25)
		#command_seq = "--user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(snplist=filename, outputdir=output_dir, N=1000, freq=5, dist=20, gene_count=20)
		#print command_shell
		processes.append( LaunchSubprocess(cmd=command_shell, path_stdout=path_stdout, logger=logger, jobname=pheno) ) #
		#time.sleep(1)
		#p.run_Log(file_output=pheno+'.txt') # writes stdout and stdout to "file_output" file in PATH path_stdout. NO WAITING since output goes to file

	for p in processes:
		p.run_Pipe()
	return processes


################ Constants ############
script2call = "/home/unix/ptimshel/git/snpsnap/snpsnap_query.py" # Updated path
current_script_name = os.path.basename(__file__).replace('.py','')


path_snplist = "/cvar/jhlab/snpsnap/data/input_lists/gwascatalog_140201_listsBIGbim"
#path_snplist = "/home/projects/tp/childrens/snpsnap/data/gwas/gwascatalog_140201_listsBIGbim"
#path_snplist = "/home/projects/tp/childrens/snpsnap/data/gwas/gwascatalog_140201_lists"

#path_output_main = "/home/projects/tp/childrens/snpsnap/data/query/gwascatalog"
path_output_main = "/cvar/jhlab/snpsnap/data/query/gwascatalog"

path_output_sub = path_output_main + "/subprocess_output"
HelperUtils.mkdirs(path_output_sub)
path_stdout = path_output_main + "/subprocess_stdout"
HelperUtils.mkdirs(path_stdout)

## Setup-logger
#logger = Logger(__name__, path_stdout).get() # gives __name__ == main
logger = Logger(current_script_name, path_stdout).get()
#logger.setLevel(logging.WARNING)
logger.setLevel(logging.INFO)


processes = submit()

# run_Pipe() method calls
for p in processes:
	p.get_pid()


pattern = re.compile(r"Found (\d+) out of (\d+) SNPs in data base", flags=re.IGNORECASE)
#Found 25 out of 25 SNPs in data base

with open(path_output_main+'/subprocess_gwastable.tab', 'w') as f_gwastable: 
	with open(path_output_main+'/subprocess_snps_found_in_db.tab', 'w') as f_not_found: 
		for p in processes:
			lines = p.process_communicate_and_read_pipe_lines()
			for (i, line) in enumerate(lines):
				#print line
				match = pattern.search(line)
				if match:
					(found, n_input_snps) = match.groups() # return all groups
					row = "{jobname}\t{found}\t{input}".format(jobname=p.jobname, found=found, input=n_input_snps)
					logger.info(row)
					f_not_found.write(row+"\n")
				if "# rating_few_matches" in line:
					row = "{}\t{}".format(p.jobname, lines[i+1]) # next line
					logger.info(row)
					f_gwastable.write(row+"\n")


for p in processes:
	p.process_check_returncode()


###################################### LEFTOVERS ######################################

## run_log() method calls
# for p in processes:
# 	p.fhandle_check()
# 	p.get_pid()

# for p in processes:
# 	p.process_communicate()
# 	p.process_check_returncode()
# 	p.fhandle_close()
# 	p.fhandle_check()


#command_seq = "--user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(snplist=filename, outputdir=output_dir, N=1000, freq=5, dist=20, gene_count=20)
#p=subprocess.Popen([script, command_seq], stdin=subprocess.PIPE,stdout=subprocess.PIPE)



