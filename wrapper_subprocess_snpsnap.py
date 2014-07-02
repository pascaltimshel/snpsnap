#!/usr/bin/env python2.7

import sys
import glob
import os
import time

import pplaunch #import LaunchBsub, LaunchSubprocess
import pphelper #import HelperUtils
import pplogger #import Logger

import re
import logging


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
		pphelper.HelperUtils.mkdirs(output_dir)

		command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --ld_buddy_cutoff {ld_buddy_cutoff} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count} --max_ld_buddy_count_deviation {ld_buddy_count} --exclude_input_SNPs".format(program=script2call, snplist=filename, outputdir=output_dir, N=N_sample_sets, ld_buddy_cutoff=ld_buddy_cutoff, freq=freq, dist=dist, gene_count=gene_count, ld_buddy_count=ld_buddy_count)
		processes.append( pplaunch.LaunchSubprocess(cmd=command_shell, path_stdout=path_stdout, logger=logger, jobname=pheno) ) #
		
		#time.sleep(1)
		#p.run_Log(file_output=pheno+'.txt') # writes stdout and stdout to "file_output" file in PATH path_stdout. NO WAITING since output goes to file

	for p in processes:
		p.run_Pipe() # NOTE THAT: the path_stdout is unused when using p.run_Pipe()
	return processes


################ Constants ############
script2call = "/cvar/jhlab/snpsnap/snpsnap/snpsnap_query.py"


path_snplist = "/cvar/jhlab/snpsnap/data/input_lists/gwascatalog_140201_listsBIGbim"
path_output_main = "/cvar/jhlab/snpsnap/data/query/gwascatalog_production_v1/subprocess"

path_output_sub = path_output_main + "/subprocess_output"
pphelper.HelperUtils.mkdirs(path_output_sub)
path_stdout = path_output_main + "/subprocess_stdout" # path_stdout is unused when using p.run_Pipe()
pphelper.HelperUtils.mkdirs(path_stdout)


###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')
log_dir = path_output_main #OBS VARIABLE
logger = pplogger.Logger(name=current_script_name, log_dir=log_dir, log_format=1, enabled=True).get()
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################



## NEXT: run 10000.5.20.20
## arguments
N_sample_sets=10000
ld_buddy_cutoff=0.5
freq=5
dist=50
gene_count=50
ld_buddy_count=50

processes = submit()

# run_Pipe() method calls
for p in processes:
	p.get_pid()


pattern = re.compile(r"Found (\d+) out of (\d+) SNPs in data base", flags=re.IGNORECASE)
#Found 25 out of 25 SNPs in data base
gwas_filename = path_output_main+'/subprocess_gwastable.{N}.{freq}.{dist}.{gene_count}.{ld_buddy_count}.tab'.format(N=N_sample_sets, freq=freq, dist=dist, gene_count=gene_count, ld_buddy_count=ld_buddy_count)
with open(gwas_filename, 'w') as f_gwastable: 
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
				#if "# rating_insufficient" in line:
				if "# insufficient_rating" in line:
					row = "{}\t{}".format(p.jobname, lines[i+1]) # next line
					logger.info(row)
					f_gwastable.write(row+"\n")


logger.info("########## CHECKING RETURN CODES ##############")
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



