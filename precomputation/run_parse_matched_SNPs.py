#!/usr/bin/env python2.7
#@TODO Possibly change this

## USAGE: this script calls parse_matched_SNPs.py.
## parse_matched_SNPs.py is call with a specific freq bin to process, e.g. the bin freq0-1
## EXAMPLE call:
##
## BEWARE: the PATH of parse_matched_SNPs.py is hardcoded.


import sys
import glob
import os
import datetime
import time
import subprocess 
sys.path.append('/home/projects/tp/tools/matched_snps/src')

from queue import QueueJob,ShellUtils,ArgparseAdditionalUtils #ArgparseAdditionalUtils unused?
import pdb
import argparse

import collections

#script = "/home/projects/tp/tools/matched_snps/src/parse_matched_SNPs.py" # Tunes old path
script = "/home/projects/tp/childrens/snpsnap/git/parse_matched_SNPs.py" # Updated path
current_script_name = os.path.basename(__file__)


############################ SETTING ZERO BUFFERING for STDOUT ######################################
# Consider this for unbuffered output. This may be useful when the function is called via run_multiple_...py
sys.stdout = os.fdopen(sys.stdout.fileno(), 'wb', 0)
batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')
#######################################################################



def run_parse(snplist_prefix, outfilename, unit_test_file):
	snplist_files = glob.glob(snplist_prefix+"*.rsID") # catching all files with CORRECT prefix
	if not os.path.exists(outfilename): # Test if already run
		unit_test_file['NO_PREVIOUS_FILE'].append(outfilename)
		#print "%s: CREATING NEW" % outfilename # OUTCOMMENTED JUNE 18 2014
		
		return True
	else:
		batch_snplist = {}
		existing_outfile = {}			
		# Read existing outfile. .tab is a 6 column file. First column is rs-number for matched_rsID
		#rs16823904      9-10    3       154081865       7       11940   ENSG00000240048 ENSG00000240068,ENSG00000174953,ENSG00000174948
		with open(outfilename, 'r') as f:
			lines = f.readlines() # No header...
			#pdb.set_trace()
			#expected_cols = 10 ######################## OBS ##############################
			#expected_cols = 13 ######################## OBS - NEW JUNE 18 2014 - after adding 2 x located within (dist and ID) + 1 x LD buddies ##############################
			expected_cols = 15 ######################## OBS - NEW JUNE 19 2014 - after adding x2 SNPsnap distance (dist and ID) ##############################
			for line in lines:
				# Remove only trailing newline
				cols = line.rstrip('\n').split('\t') # tab seperated - WE MUST KNOW THIS!
				# cols[0] ==> "input SNP rs-number" (matched_rsID)
				if len(cols) == expected_cols: #hmmm, potentially bad code
					# if cols[0] in existing_outfile: pdb.set_trace()
					existing_outfile[cols[0]] = 1
				else:
					print "***OBS*** File %s did not contain %d columns as expected." % (outfilename, expected_cols)
					print "Please check structure of file if you see the message repeatedly"
					break
		#pdb.set_trace()
		for snp_list in snplist_files:
			with open(snp_list, 'r') as f:
				# rs28615451
				# rs184229306
				# rs115111187
				# rs12361890
				lines = f.readlines()
				for line in lines:
					rs_no = line.strip()
					batch_snplist[rs_no] = 1
		#pdb.set_trace()
		if len(batch_snplist) == len(existing_outfile):
			unit_test_file['FILE_EXISTS_OK'].append(outfilename)
			#print "%s: OK" % outfilename # OUTCOMMENTED JUNE 18 2014

			return None # Do not submit new job if files are ok!
		else:
			unit_test_file['FILE_EXISTS_BAD'].append(outfilename)
			#print "%s: BAD FILE EXISTS. MAKING NEW" % outfilename # OUTCOMMENTED JUNE 18 2014

			return True # Re-run job.






# Submit
def submit(path, stat_gene_density_path):
	#prefix = os.path.abspath(path+"/ldlists/freq")
	block_str = '============================= %s ===================================' % batch_time
	#unit_test_file = {}
	unit_test_file = collections.defaultdict(list)
	# Initialyzing keys
	unit_test_file['NO_PREVIOUS_FILE']
	unit_test_file['FILE_EXISTS_OK']
	unit_test_file['FILE_EXISTS_BAD']

	jobs = []
	for i in range(0,50,1): # 0...49. allways 50 freq bins. No problem here.
		suffix = "%s-%s"%(i,i+1) # e.g. 0-1
		#outfilename = prefix + suffix + ".tab" # e.g. ...long-path.../ldlists/freq0-1.tab
		ldfiles_prefix = os.path.abspath(path+"/ldlists/freq") + suffix
		snplist_prefix = os.path.abspath(path+"/snplists/freq") + suffix # e.g. # e.g. ...long-path.../snplist/freq0-1, where the whole file is e.g. freq9-10-part40000-50000.rsID
		outfilename = stat_gene_density_path + "/freq" + suffix + ".tab" # e.g. .;long_path../step2/1KG_full_queue/ld0.5/stat_gene_density/freq0-1.tab
		#command = "%s --ldfiles_prefix %s --outfilename %s"%(script,"%s%s"%(prefix,suffix),outfilename) # e.g. --ldfiles_prefix becomes freq0-1
		command = "%s --ldfiles_prefix %s --outfilename %s" % (script, ldfiles_prefix ,outfilename) #
		run = run_parse(snplist_prefix, outfilename, unit_test_file)
		if run:
			print "will submit job for ldfiles_prefix: %s" % ldfiles_prefix
			jobs.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "run_parse_matched_SNPs_"+suffix, script_name=current_script_name) )
		else: 
			print "will NOT submit job for ldfiles_prefix: %s" % ldfiles_prefix

		# if not os.path.exists(outfilename):
		# 		jobs.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "run_parse_matched_SNPs_"+suffix, script_name=current_script_name) )
		# elif sum(1 for line in open(outfilename)) == 0: # Files are emtpy
		# 		jobs.append( QueueJob(command, log_dir_path, queue_name, walltime, mem_per_job , flags, "run_parse_matched_SNPs_"+suffix, script_name=current_script_name) )
	
	################## PRINT STATS ##########################
	print '\n'.join([block_str]*3)
	print "#################### **** STATS from 'unit_test_file' **** ####################"
	for stat_key, stat_list in unit_test_file.items():
		print "{}: {}".format( stat_key, len(stat_list) )
	print block_str
	for stat_key, stat_list in unit_test_file.items():
		#print "{}: {}".format( stat_key, len(stat_list) )
		for ldfile in stat_list:
			print "{}\t{}".format( stat_key, ldfile )
		print block_str

	################## NOW SUBMIT JOBS #######################
	for job in jobs:
		job.run()
		time.sleep(2)

	################## PRINT FAILS ##########################
	print '\n'.join([block_str]*3)
	print "#################### **** JOBS THAT COULD NOT BE SUBMITTED - from QueueJob **** ####################"
	print "Number of jobs that were not submitted: %s" % len(QueueJob.QJ_job_fails_list)
	for no, job_name in enumerate(QueueJob.QJ_job_fails_list, start=1):
		print "{}\t{}".format(no, job_name)
	print '\n'.join([block_str]*3)

# CBS queue parameters
#queue_name = "urgent" #@TODO Change queue to idle if Pascal should run it
queue_name = "cbs" #@TODO Change queue to idle if Pascal should run it
walltime="604800" # 60*60*24*7=7 days
#walltime="86400" # 60*60*24=1 day - USED BEFORE JUNE 18 2014
#mem_per_job="1gb" #tunes default
mem_per_job="15gb"
flags = "sharedmem"

# Parse arguments  
arg_parser = argparse.ArgumentParser(description="Run parse_matched_SNPs.py")
arg_parser.add_argument("--plink_matched_snps_path", \
	help="""Path for plink_matched_snps.py results which contain 3 directories [ldlists, log, snplists],
e.g. /home/projects/tp/childrens/snpsnap/data/step2/1KG_full_queue/ld0.5/
NB. please use symlinks in the path, i.e. do not use /net/home...""", required=True)
#NB. Also check that the path has a trailing slash (/)
args = arg_parser.parse_args()

path = os.path.abspath(args.plink_matched_snps_path) # Trailing slash are removed/corrected - NICE!
#^^^ E.g. "/home/projects/tp/tools/matched_snps/src/hapmap/ld0.5/"
#^^^ E.g. "/home/projects/tp/childrens/snpsnap/data/step2/1KG_test_thin0.1/ld0.5/"
log_dir_path = path + "/log" #PASCAL: PROBLEM fixed with extra slash
stat_gene_density_path = path + "/stat_gene_density"
ShellUtils.mkdirs(stat_gene_density_path)

### Make sure that the genotype prefix is correct ###
if False:
	ans = ""
	print "*** SAFETY CHECK! ***"
	print "You specifed --plink_matched_snps_path to be: %s" % args.plink_matched_snps_path
	#print "NB Please check that the path has a trailing slash (/) - It may not work without - FIX THIS!"
	print "Plese confirm that this is the correct path to use by typing 'yes'"
	while ans != 'yes':
	 	ans = raw_input("Confirm: ")
	print "Ok let's start..."


submit(path, stat_gene_density_path)










#########################################

# def run_parse(ldfiles_prefix, outfilename):
# 	ldfiles = glob.glob(ldfiles_prefix+"*.ld") # catching all .ld files with CORRECT prefix
# 	if not os.path.exists(outfilename): # Test if already run
# 		print "%s: CREATING NEW" % outfilename
# 		#print "*** Filename %s does NOT exists ***.\nAppending job for LDfile %s to QueueJob.py..." % (outfilename, ldfile)
# 		return True # submit job is there is no existing ldfile
# 	else:
# 		ld_snplist = {}
# 		existing_outfile = {}
# 		# Read all .ld files matching prefix
# 		#print "Found {} ld file for prefix {}".format(len(ldfiles), ldfiles_prefix)
# 		#print "Reading files..."		
# 		for ldfile in ldfiles:
# 			with open(ldfile, 'r') as f:
# 				# CHR_A         BP_A        SNP_A  CHR_B         BP_B        SNP_B           R2
# 	 			# 1      1011095   rs11810785      1      1011095   rs11810785            1
# 	 			# 1      1011095   rs11810785      1      1025301    rs9442400      0.61996
				
# 				# plink ALWAYS outputs a line containing with input SNP, i.e. a line with an LD buddy to itself. SEE above example. 
# 				# this enables us to assume len(existing_ld_snplist) == len(batch_snplist)
# 				lines = f.readlines()[1:] # SKIP HEADER!!
# 				expected_cols = 7 ######################## OBS ##############################
# 				for line in lines:
# 					cols = line.strip().split()
# 					# cols[2] ==> input SNP rs-number
# 					# cols[5] ==> LD buddy rs-number
# 					if len(cols) == expected_cols:
# 						ld_snplist[cols[2]] = 1
# 					else:
# 						print "***OBS*** File %s did not contain %d columns as expected." % (ldfile, expected_cols)
# 						print "Please check structure of file if you see the message repeatedly"
# 						break
			
# 		# Read existing outfile. .tab is a 6 column file. First column is rs-number for matched_rsID
# 		#rs16823904      9-10    3       154081865       7       11940   ENSG00000240048 ENSG00000240068,ENSG00000174953,ENSG00000174948
# 		with open(outfilename, 'r') as f:
# 			lines = f.readlines() # No header...
# 			#pdb.set_trace()
# 			expected_cols = 8 ######################## OBS ##############################
# 			for line in lines:
# 				# Remove only trailing newline
# 				cols = line.rstrip('\n').split('\t') # tab seperated - WE MUST KNOW THIS!
# 				# cols[0] ==> "input SNP rs-number" (matched_rsID)
# 				if len(cols) == expected_cols: #hmmm, potentially bad code
# 					existing_outfile[cols[0]] = 1
# 				else:
# 					print "***OBS*** File %s did not contain %d columns as expected." % (outfilename, expected_cols)
# 					print "Please check structure of file if you see the message repeatedly"
# 					break

# 		if len(ld_snplist) == len(existing_outfile):
# 			#print "Filename %s exists and are validated for ldfile %s.\nNot appending any jobs to QueueJob.py..." % (outfilename, ldfile)
# 			print "%s: OK" % outfilename
# 			return None # Do not submit new job if files are ok!
# 		else:
# 			#print "Filename %s\n*** Exists but are NOT OK !***\nAppending job for LDfile %s to QueueJob.py... ***" % (outfilename, ldfile)
# 			print "%s: BAD FILE EXISTS. MAKING NEW" % outfilename
# 			return True # Re-run job.










