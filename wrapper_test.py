##!/usr/bin/env python2.7

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
	files = glob.glob(path_snplist+'/*.txt')[0:2] #REMOVE LATER
	processes = []
	for (counter, filename) in enumerate(files, start=1):
		pheno = os.path.splitext(os.path.basename(filename))[0]
		print "processing file #%d/#%d: %s" % (counter, len(files), pheno)
		user_snps_file = filename # full path
		output_dir = path_output_main+"/"+pheno 
		command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(program=script2call, snplist=filename, outputdir=output_dir, N=1000, freq=5, dist=20, gene_count=20)
		#command_seq = "--user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(snplist=filename, outputdir=output_dir, N=1000, freq=5, dist=20, gene_count=20)
		print command_shell
		processes.append( LaunchSubprocess(cmd=command_shell, logdir=log_dir_path, log_root=current_script_name, file_output=pheno, tag=pheno) ) #
		time.sleep(1)
	for p in processes:
		p.run_Log()
	return processes


################ Constants ############
script2call = "/home/unix/ptimshel/git/snpsnap/snpsnap_query.py" # Updated path

current_script_name = os.path.basename(__file__).replace('.py','')


path_snplist = "/cvar/jhlab/snpsnap/data/input_lists/gwascatalog_140201_listsBIGbim"
#path_snplist = "/home/projects/tp/childrens/snpsnap/data/gwas/gwascatalog_140201_listsBIGbim"
#path_snplist = "/home/projects/tp/childrens/snpsnap/data/gwas/gwascatalog_140201_lists"

#path_output_main = "/home/projects/tp/childrens/snpsnap/data/query/gwascatalog"
path_output_main = "/cvar/jhlab/snpsnap/data/query/gwascatalog"

log_dir_path = path_output_main + "/log"
HelperUtils.mkdirs(log_dir_path)

processes = submit()

for p in processes:
	p.fhandle_check()
	p.get_pid()

for p in processes:
	p.process_communicate()
	p.process_check_returncode()
	p.fhandle_close()
	p.fhandle_check()

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











