#!/usr/bin/env python2.7

import sys
import glob
import os
import time

#import subprocess
from plaunch import LaunchSubprocess,HelperUtils

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





# # Submit
# def submit():
# 	files = glob.glob(path_snplist+'/*.txt')[0:5] #REMOVE LATER
# 	jobs = []
# 	filehandles = []
# 	for (counter, filename) in enumerate(files, start=1):
# 		pheno = os.path.splitext(os.path.basename(filename))[0]
# 		print "processing file #%d/#%d: %s" % (counter, len(files), pheno)
# 		user_snps_file = filename # full path
# 		output_dir = path_output_main+"/"+pheno 
# 		command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(program=script, snplist=filename, outputdir=output_dir, N=1000, freq=5, dist=20, gene_count=20)
# 		#command_seq = "--user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(snplist=filename, outputdir=output_dir, N=1000, freq=5, dist=20, gene_count=20)
# 		print command_shell
# 		f_log = open(current_script_name+'_'+pheno+'.log', 'w')
# 		filehandles.append( f_log )
# 		p=subprocess.Popen(command_shell, stdout=f_log, stderr=subprocess.STDOUT, shell=True)
# 		#p.communicate()
# 		print "done with pheno %s" % pheno
# 		#time.sleep(2)


# 		#p=subprocess.Popen(command_shell, stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
# 		#p=subprocess.Popen([script, command_seq], stdin=subprocess.PIPE,stdout=subprocess.PIPE)
# 		jobs.append(p)
# 		#stdout = p.stdout.read()
# 		#stderr = p.stderr.read()
# 		#print "1HERE IS STDOUT: " + str(stdout)
# 		#print "2HERE IS STDERR: " + str(stderr)
# 	#return jobs
# 	return (jobs, filehandles)



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
		command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(program=script2call, snplist=filename, outputdir=output_dir, N=1000, freq=5, dist=20, gene_count=20)
		#command_seq = "--user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(snplist=filename, outputdir=output_dir, N=1000, freq=5, dist=20, gene_count=20)
		#print command_shell
		processes.append( LaunchSubprocess(cmd=command_shell, logdir=log_dir_path, log_root=current_script_name, file_output=pheno+'.txt', tag=pheno) ) #
		#time.sleep(1)
	for p in processes:
		#p.run_Log() # writes stdout and stdout to "file_output" file
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

path_output_sub = path_output_main + "/output_subprocess"
HelperUtils.mkdirs(path_output_sub)
log_dir_path = path_output_main + "/log_subprocess"
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



## run_log() method calls
# for p in processes:
# 	p.fhandle_check()
# 	p.get_pid()

# for p in processes:
# 	p.process_communicate()
# 	p.process_check_returncode()
# 	p.fhandle_close()
# 	p.fhandle_check()




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


# #jobs = submit()
# (jobs, filehandles) = submit()
# check_fhandles(filehandles)
# display_pids(jobs)
# #process_wait(jobs)
# process_communicate(jobs)
# check_fhandles(filehandles)
# check_returncodes(jobs)

# close_fhandles(filehandles)
# check_fhandles(filehandles)




# SNP #24/25: ID {12:112007756}: found 336 hits
# *** Found SNP with too few matches; n_matches=336. Using sampling with replacement to get enough samples ***
# SNP #25/25: ID {3:41912651}: found 3473 hits
# ################# Score ###############
# # Rating 'number of few matches' = 'ok' with scale ['very good', 'good', 'ok', 'poor', 'very poor']
# # Percent 'few matches' = 8% (2 'few matches' out of 25 valid input SNPs)
# # Rating 'over sampling' = 'ok' with scale ['very poor', 'poor', 'ok', 'good', 'very good']
# # Relative sample size = 34.25% (high is good; median SNPs to sample from in 'few matches' is 342.5 compared to 1000 N_sample_sets)
# # rating_few_matches    pct_few_matches N_few_matches   N_input_snps    rating_over_sampling    pct_over_sampling       median_sample_size      N_sample_sets
# ok      8.0     2       25      ok      34.25   342.5   1000
# ######################################
# TOTAL RUNTIME: 85.5982089043 s (1.42663681507 min)
# wrapper_test.launch_subprocess: INFO     [PID:21239|Tag:Age-related_macular_degeneration]       returncode-code OK: 0
# wrapper_test.launch_subprocess: INFO     [PID:21240|Tag:Diastolic_blood_pressure]       returncode-code OK: 0
# ptimshel@node1380:~/git/snpsnap>






