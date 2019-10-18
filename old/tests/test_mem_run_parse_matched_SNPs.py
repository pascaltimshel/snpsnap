#!/usr/bin/env python2.7


import sys
import glob
import os
import datetime
import time
import subprocess 

from queue import QueueJob,ShellUtils,ArgparseAdditionalUtils #ArgparseAdditionalUtils unused?
import pdb
import argparse

import collections

import gc

def run_parse(snplist_prefix, outfilename, unit_test_file):
	print "INSIDE FUNCTION:"
	max_mem_used = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
	print "resource.getrusage(resource.RUSAGE_SELF).ru_maxrss: %s" % max_mem_used
	print memory_usage()
	#gc.collect()

	snplist_files = glob.glob(snplist_prefix+"*.rsID") # catching all files with CORRECT prefix
	if not os.path.exists(outfilename): # Test if already run
		unit_test_file['NO_PREVIOUS_FILE'].append(outfilename)
		print "%s: CREATING NEW" % outfilename # OUTCOMMENTED JUNE 18 2014
		
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
			print "%s: OK" % outfilename # OUTCOMMENTED JUNE 18 2014

			return None # Do not submit new job if files are ok!
		else:
			unit_test_file['FILE_EXISTS_BAD'].append(outfilename)
			print "%s: BAD FILE EXISTS. MAKING NEW" % outfilename # OUTCOMMENTED JUNE 18 2014

			return True # Re-run job.







# Submit
def submit(path, stat_gene_density_path):
	unit_test_file = collections.defaultdict(list)
	# Initialyzing keys
	unit_test_file['NO_PREVIOUS_FILE']
	unit_test_file['FILE_EXISTS_OK']
	unit_test_file['FILE_EXISTS_BAD']

	for i in range(0,50,1): # 0...49. allways 50 freq bins. No problem here.
		suffix = "%s-%s"%(i,i+1) # e.g. 0-1
		snplist_prefix = os.path.abspath(path+"/snplists/freq") + suffix # e.g. # e.g. ...long-path.../snplist/freq0-1, where the whole file is e.g. freq9-10-part40000-50000.rsID
		outfilename = stat_gene_density_path + "/freq" + suffix + ".tab" # e.g. .;long_path../step2/1KG_full_queue/ld0.5/stat_gene_density/freq0-1.tab
		run = run_parse(snplist_prefix, outfilename, unit_test_file)

	################## PRINT STATS ##########################
	print "#################### **** STATS from 'unit_test_file' **** ####################"
	for stat_key, stat_list in unit_test_file.items():
		print "{}: {}".format( stat_key, len(stat_list) )
	for stat_key, stat_list in unit_test_file.items():
		for ldfile in stat_list:
			print "{}\t{}".format( stat_key, ldfile )

#######################
import resource
def using(point=""):
	usage=resource.getrusage(resource.RUSAGE_SELF)
	return '''%s: usertime=%s systime=%s mem=%s mb''' % (point,usage[0],usage[1], (usage[2]*resource.getpagesize())/1000000.0 )
#######################


def memory_usage():
    """Memory usage of the current process in kilobytes."""
    status = None
    result = {'peak': 0, 'rss': 0}
    try:
        # This will only work on systems with a /proc file system
        # (like Linux).
        status = open('/proc/self/status')
        for line in status:
            parts = line.split()
            key = parts[0][2:-1].lower()
            if key in result:
                result[key] = int(parts[1])
    finally:
        if status is not None:
            status.close()
    return result

# http://stackoverflow.com/questions/938733/total-memory-used-by-python-process
print "BEFORE ANYTHING"
max_mem_used = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print "resource.getrusage(resource.RUSAGE_SELF).ru_maxrss: %s" % max_mem_used
print using()
print memory_usage()

print resource.getrusage(resource.RUSAGE_SELF)

# Parse arguments  
arg_parser = argparse.ArgumentParser(description="Run parse_matched_SNPs.py")
arg_parser.add_argument("--plink_matched_snps_path", \
	help="""Path for plink_matched_snps.py results which contain 3 directories [ldlists, log, snplists],
e.g. /home/projects/tp/childrens/snpsnap/data/step2/1KG_full_queue/ld0.5/
NB. please use symlinks in the path, i.e. do not use /net/home...""", required=True)
#NB. Also check that the path has a trailing slash (/)
args = arg_parser.parse_args()

path = os.path.abspath(args.plink_matched_snps_path) # Trailing slash are removed/corrected - NICE!
stat_gene_density_path = path + "/stat_gene_density"

submit(path, stat_gene_density_path)


print "AFTER EVERYTHING"
max_mem_used = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print "resource.getrusage(resource.RUSAGE_SELF).ru_maxrss: %s" % max_mem_used

print using()
print memory_usage()










