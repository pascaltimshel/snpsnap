#!/usr/bin/env python2.7

# Example call:
# test data
# ./compile_tab2hdf5.py --input_dir /Users/pascaltimshel/snpsnap/data/step2/1KG_test_thin0.02_duprm/ld0.5/stat_gene_density --hdf5_dir /Users/pascaltimshel/snpsnap/data/step3/test --type ld0.5
# full ld0.5
# ./compile_tab2hdf5.py --input_dir /Users/pascaltimshel/snpsnap/data/step2/1KG_full_duprm_nolim/ld0.5/stat_gene_density --hdf5_dir /Users/pascaltimshel/snpsnap/data/step3 --type ld0.5

# Run time
# The program runs in about 8 min on Pascal's MBP (6 min for .map(str)!)

# Memory usage:
# This program uses about 4 GB of memory when using the full data set of size ~900 MB
# The data frame uses 2 GB and the split uses an additional 2 GB

#TODO
#0) Write shell script that calls this function many times
#0) map rsID to chromosomal position
#1) header_str is hardcoded. Fix run_parse_matched_snps.py to print a header for the file!?


import os
import sys
import argparse
from queue import QueueJob,ArgparseAdditionalUtils

import shutil
import glob
import pandas as pd

import time
import pdb

import psutil
from memory_profiler import profile

### Old function - ATTEMPT TO APPEND TO DATAFRAME TO SKIP Writing combined .tab file. Keep for now.
# def tab2dataframe(path):
# 	""" Read .tab files to data.frame and concatenates them to one object"""
# 	tabfiles = glob.glob(path+"/*.tab")
	
# 	df_1KG_snsps = pd.DataFrame()
# 	#TODO: fix the hardcoded header	
# 	header_str = "matched_rsID freq_bin snp_chr snp_position matched_gene_count matched_dist_to_nearest_gene matched_nearest_gene genes_in_matched_locus"
# 	colnames=header_str.split()

# 	for counter, tabfile in enumerate(tabfiles, start=1):
# 		print "tabfile #%s/#%s: reading %s" % (counter, len(tabfiles), os.path.basename(tabfile))
# 		frame = pd.read_csv(tabfile, index_col=0, names=colnames, delim_whitespace=True)
# 		#pdb.set_trace()
# 		if frame.empty:
# 			print "tabfile #%s/#%s: DataFrame is empty" % (counter, len(tabfiles))
# 		else:
# 			#pd.concat(df_1KG_snsps, frame) #FIX: the concat takes a list as argument
# 			df_1KG_snsps.append(df_1KG_snsps, frame)
# 	return df_1KG_snsps

@profile
def concatenate_tab_files(inpath, outpath, prefix_out):
	""" Read .tab files to data.frame and concatenates them to one object"""
	tabfiles = glob.glob(inpath+"/*.tab")
	if not len(tabfiles) == 50:
		print "Error: did not find 50 .tab files as expected in path: %s" % inpath
		print "Number of tabfiles found: %s" % len(tabfiles)
		print "Aborting script..."
		sys.exit(1)
	# Sorting on freq bin
	tabfiles.sort(key=lambda x: int(x.split('/')[-1].split('freq')[-1].split('-')[0])) # this step is not needed. Unreadable code
	tabfile_concatenated = outpath+"/"+prefix_out+".tab" # e.g ../1KGsnp_matrix_ld0.5.tab
	with open(tabfile_concatenated, 'w') as outfile: 
		start_time = time.time()
		print "Start writing to concatenated tab file file: %s" % os.path.basename(tabfile_concatenated)
		for counter, tabfile in enumerate(tabfiles, start=1):
			#print "tabfile #%s/#%s: reading %s" % (counter, len(tabfiles), os.path.basename(tabfile))
			print "Concatenating tabfile #%s/#%s: %s" % (counter, len(tabfiles), os.path.basename(tabfile))
			with open(tabfile) as infile:
				# Fastest way to concatenate in python. No overhead of finding newlines
				#http://stackoverflow.com/questions/17749484/python-script-to-concatenate-all-the-files-in-the-directory-into-one-file
				shutil.copyfileobj(infile, outfile) #shutil.copyfileobj(fsrc, fdst)
				# Alternative way to concatenate 
				#outfile.write(infile.read()) # writing and reading. readlines() is also ok.
		elapsed_time = time.time() - start_time
		print "Elapsed_time of writing tab file: %.3f s (%.2f min)" % (elapsed_time, elapsed_time/60)
		file_tab_size = os.path.getsize(tabfile_concatenated)
		print "Size of concatenated tab file: %s bytes (%.1f MB)" % (file_tab_size, file_tab_size/(1024*1024.0))

@profile
def tab2dataframe(outpath, prefix_out):
	tabfile = outpath+"/"+prefix_out+".tab"
	header_str = "matched_rsID freq_bin snp_chr snp_position matched_gene_count matched_dist_to_nearest_gene matched_nearest_gene genes_in_matched_locus"
	colnames=header_str.split()
	#df = pd.read_csv(tabfile, index_col=0, names=colnames, delim_whitespace=True)
	start_time = time.time()
	print "START: reading CSV file..."
	df = pd.read_csv(tabfile, names=colnames, delim_whitespace=True)
	elapsed_time = time.time() - start_time
	print "END: read CSV file into DataFrame in %s s (%s min)" % (elapsed_time, elapsed_time/60)
	
	print "START: mapping chrposID strings..."
	start_time = time.time()
	df['chrposID'] = df.snp_chr.map(str) + ":" + df.snp_position.map(str) # http://stackoverflow.com/questions/11858472/pandas-combine-string-and-int-columns
	elapsed_time = time.time() - start_time
	print "END: manipulating chrposID in %s s (%s min)" % (elapsed_time, elapsed_time/60)

	df.set_index('chrposID', inplace=True)
	df.drop(['snp_chr', 'snp_position'], axis=1, inplace=True) # Deletes unnecessary columns
	
	print "START: editing freq_bin strings..."
	start_time = time.time()
	df['freq_bin'] = df.freq_bin.str.split('-').str.get(0).apply(int) # Converting freq_bin into 'int' so we can sort later on
	elapsed_time = time.time() - start_time
	print "END: editing freq_bin in %s s (%s min)" % (elapsed_time, elapsed_time/60)

	return df


#
#Parse Arguments
#
arg_parser = argparse.ArgumentParser(description="Read multiple .tab files from e.g. /stat_gene_density and write all tab files to combined file 1KGsnps.h5")
# arg_parser.add_argument("--input_dir", \
# 	help="""Input directory: MUST be a 'master dir' containing the directories 
# [ldlists, log, snplists, stat_gene_density].
# e.g. /home/projects/tp/childrens/snpsnap/data/step2/1KG_full_queue/ld0.5/ 
# NB. please use symlinks in the path, i.e. do not use /net/home...""", \
# 	required=True)
arg_parser.add_argument("--input_dir", \
	help="""Input directory CONTAINING tab files].
e.g. /home/projects/tp/childrens/snpsnap/data/step2/1KG_full_queue/ld0.5/stat_gene_density
NB. please use symlinks in the path, i.e. do not use /net/home...""", \
	required=True)
arg_parser.add_argument("--hdf5_dir", \
	type=ArgparseAdditionalUtils.check_if_writable, \
	help="Path to write HDF5 file. Dir must exist.", \
	required=True)
arg_parser.add_argument("--type", \
	help="Type of distance used, e.g. ld0.5 or kb100", \
	required=True)
args = arg_parser.parse_args()

# Trailing slash are removed/corrected - NICE!
path_input = os.path.abspath(args.input_dir) 
path_hdf5 = os.path.abspath(args.hdf5_dir)
prefix_out = '1KGsnp_matrix_%s' % args.type
file_hdf5 = path_hdf5+"/"+prefix_out+'.h5'

# sanity check. TODO: remove this later!
if True:	
	if not args.type in path_input:
		print "Input dir: %s" % path_input
		print "Could not find --type '%s' in input dir. Are you sure you know what you are doing?" % args.type
		ans = ""
		while ans != 'yes':
		 	ans = raw_input("Confirm: ")
			print "Ok let's start..."

#Only proceed if file does not exists
if os.path.exists(file_hdf5):
	print "Error: file %s allready exists. Remove file before continuing. Exiting..." % file_hdf5
	sys.exit(1)


##Read .tab files into one combined data frame
concatenate_tab_files(path_input, path_hdf5, prefix_out)
df_1KG_snsps = tab2dataframe(path_hdf5, prefix_out)
# #TODO: make function that compresses .tab file after dataframe is created.

# Open store with unique name to identify data stored in it
store = pd.HDFStore(file_hdf5, 'w')
# writing to HDF5
#store.put('dummy', df_1KG_snsps, format='fixed') #TODO: change 'key'=dummy to something useful
# PerformanceWarning:  your performance may suffer as PyTables will pickle object types that it cannot
idx_cols = ['freq_bin', 'matched_gene_count', 'matched_dist_to_nearest_gene']
start_time = time.time()
print "START: Writing to HDF5 file: %s" % file_hdf5
store.put('dummy', df_1KG_snsps, format='table', append=False, data_columns=idx_cols) # No warning when using 'table' format
elapsed_time = time.time() - start_time
print "END: Elapsed_time of writing file: %.3f s (%.2f min)" % (elapsed_time, elapsed_time/60)
file_hdf5_size = os.path.getsize(file_hdf5)
print "Size of HDF5 file: %s bytes (%.1f MB)" % (file_hdf5_size, file_hdf5_size/(1024*1024.0))
# CONSIDER: df.to_hdf('test.hdf','df',mode='w',format='table',chunksize=2000000)
store.close()
	

