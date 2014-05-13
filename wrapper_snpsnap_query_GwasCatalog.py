##!/usr/bin/env python2.7

import sys
import glob
import os
import time

import subprocess

import pdb


def mkdirs(file_path):
	if not os.path.exists(file_path):
	    os.makedirs(file_path)





#Popen.pid The process ID of the child process.


# Submit
def submit():
	files = glob.glob(path_snplist+'/*.txt')[0:5] #REMOVE LATER
	jobs = []
	filehandles = []
	for (counter, filename) in enumerate(files, start=1):
		pheno = os.path.splitext(os.path.basename(filename))[0]
		print "processing file #%d/#%d: %s" % (counter, len(files), pheno)
		user_snps_file = filename # full path
		output_dir = path_output_main+"/"+pheno 
		command_shell = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(program=script, snplist=filename, outputdir=output_dir, N=1000, freq=5, dist=20, gene_count=20)
		#command_seq = "--user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type ld --distance_cutoff 0.5 match --N_sample_sets {N} --max_freq_deviation {freq} --max_distance_deviation {dist} --max_genes_count_deviation {gene_count}".format(snplist=filename, outputdir=output_dir, N=1000, freq=5, dist=20, gene_count=20)
		print command_shell
		f_out = open(current_script_name+'_'+pheno+'.out', 'w')
		f_err = open(current_script_name+'_'+pheno+'.err', 'w')
		filehandles.append( (f_out, f_err) )
		#f_log = open(current_script_name+'.log', 'w')
		p=subprocess.Popen(command_shell, stdout=f_out,stderr=f_err, shell=True)
		#p.communicate()
		print "done with pheno %s" % pheno
		#time.sleep(2)


		#p=subprocess.Popen(command_shell, stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
		#p=subprocess.Popen([script, command_seq], stdin=subprocess.PIPE,stdout=subprocess.PIPE)
		jobs.append(p)
		#stdout = p.stdout.read()
		#stderr = p.stderr.read()
		#print "1HERE IS STDOUT: " + str(stdout)
		#print "2HERE IS STDERR: " + str(stderr)
	#return jobs
	return (jobs, filehandles)

def check_fhandles(filehandles):
	for f in filehandles:
		print "f_out closed: %s" % f[0].closed
		print "f_err closed: %s" % f[1].closed


def display_pids(jobs):
	print "Displaying %d jobs" % len(jobs)
	for p in jobs:
		print p.pid

def process_wait(jobs):
	print "waiting for all jobs"
	for (n, p) in enumerate(jobs, start=1):
		print "#%d/#%d: waiting for PID %s" % ( n, len(jobs), p.pid )
		p.wait()

def process_communicate(jobs):
	print "communicating with all jobs"
	for (n, p) in enumerate(jobs, start=1):
		print "#%d/#%d: communicating with PID %s" % ( n, len(jobs), p.pid )
		(stdout, stderr) = p.communicate()
		print "HERE IS STDOUT: " + str(stdout)
		print "HERE IS STDERR: " + str(stderr)

def listen_to_jobs(jobs):
	#pass
	#exit_codes = [p.wait() for p in p1, p2] #p.communicate() #now wait
	for p in jobs:
		print "Listen to PID %s" % p.pid
		#pdb.set_trace()
		(stdout, stderr) = p.communicate()
		print "HERE IS STDOUT: " + str(stdout)
		print "HERE IS STDERR: " + str(stderr)


################ Constants ############
script = "/home/unix/ptimshel/git/snpsnap/snpsnap_query.py" # Updated path
current_script_name = os.path.basename(__file__)


path_snplist = "/cvar/jhlab/snpsnap/data/input_lists/gwascatalog_140201_listsBIGbim"
#path_snplist = "/home/projects/tp/childrens/snpsnap/data/gwas/gwascatalog_140201_listsBIGbim"
#path_snplist = "/home/projects/tp/childrens/snpsnap/data/gwas/gwascatalog_140201_lists"

#path_output_main = "/home/projects/tp/childrens/snpsnap/data/query/gwascatalog"
path_output_main = "/cvar/jhlab/snpsnap/data/query/gwascatalog"

log_dir_path = path_output_main + "/log"
mkdirs(log_dir_path)

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


#jobs = submit()
(jobs, filehandles) = submit()
check_fhandles(filehandles)
display_pids(jobs)
#process_wait(jobs)
process_communicate(jobs)
check_fhandles(filehandles)
#listen_to_jobs(jobs)










