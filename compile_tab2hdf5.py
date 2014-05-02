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

### Old function - ATTEMPT TO APPEND TO DATAFRAME TO SKIP Writing combined .tab file. 
# FUNCTION INCOMPLETE, but keep for now.
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


### FUNCTION THAT CONCATENATES FILES VERY FAST!
## WORKS.
## call: concatenate_tab_files(path_input, path_output, prefix_out) 
# DO NOT DELETE

# @profile
# def concatenate_tab_files(inpath, file_tab):
# 	""" Concatenates .tab files to one file"""
# 	tabfiles = glob.glob(inpath+"/*.tab")
# 	if not len(tabfiles) == 50:
# 		print "Error: did not find 50 .tab files as expected in path: %s" % inpath
# 		print "Number of tabfiles found: %s" % len(tabfiles)
# 		print "Aborting script..."
# 		sys.exit(1)
# 	# Sorting on freq bin
# 	tabfiles.sort(key=lambda x: int(x.split('/')[-1].split('freq')[-1].split('-')[0])) # this step is not needed. Unreadable code
# 	with open(file_tab, 'w') as outfile: 
# 		start_time = time.time()
# 		print "Start writing to concatenated tab file file: %s" % os.path.basename(file_tab)
# 		for counter, tabfile in enumerate(tabfiles, start=1):
# 			#print "tabfile #%s/#%s: reading %s" % (counter, len(tabfiles), os.path.basename(tabfile))
# 			print "Concatenating tabfile #%s/#%s: %s" % (counter, len(tabfiles), os.path.basename(tabfile))
# 			with open(tabfile) as infile:
# 				# Fastest way to concatenate in python. No overhead of finding newlines
# 				#http://stackoverflow.com/questions/17749484/python-script-to-concatenate-all-the-files-in-the-directory-into-one-file
# 				shutil.copyfileobj(infile, outfile) #shutil.copyfileobj(fsrc, fdst)
# 				# Alternative way to concatenate 
# 				#outfile.write(infile.read()) # writing and reading. readlines() is also ok.
# 		elapsed_time = time.time() - start_time
# 		print "Elapsed_time of writing tab file: %.3f s (%.2f min)" % (elapsed_time, elapsed_time/60)
# 		file_tab_size = os.path.getsize(file_tab)
# 		print "Size of concatenated tab file: %s bytes (%.1f MB)" % (file_tab_size, file_tab_size/(1024*1024.0))


### FUNCTION to edit and concatenate - slow, but only run once!
@profile
def write_new_tab_file(inpath, file_tab):
	""" Read .tab files and edit columns and write them to a concatenated file"""
	tabfiles = glob.glob(inpath+"/*.tab")
	if not len(tabfiles) == 50:
		print "Error: did not find 50 .tab files as expected in path: %s" % inpath
		print "Number of tabfiles found: %s" % len(tabfiles)
		print "Aborting script..."
		sys.exit(1)
	# Sorting on freq bin
	tabfiles.sort(key=lambda x: int(x.split('/')[-1].split('freq')[-1].split('-')[0])) # this step is not needed. Unreadable code
	with open(file_tab, 'w') as outfile: 
		start_time = time.time()
		print "Start writing to concatenated tab file file: %s" % os.path.basename(file_tab)
		for counter, tabfile in enumerate(tabfiles, start=1):
			#print "tabfile #%s/#%s: reading %s" % (counter, len(tabfiles), os.path.basename(tabfile))
			print "Concatenating tabfile #%s/#%s: %s" % (counter, len(tabfiles), os.path.basename(tabfile))
			with open(tabfile) as infile:
				for line in infile.readlines():
					cols = line.strip('\n').split('\t') # use strip('\n') and split('\t') a use ensure that there are always the same number of cols
													# otherwise you get error when genes_in_matched_locus is empty
					#TODO: check lenght of cols - must be 8 cols
					# Columns in input tabfiles:
					#0 matched_rsID 
					#1 freq_bin 
					#2 snp_chr
					#3 snp_position 
					#4 matched_gene_count
					#5 matched_dist_to_nearest_gene 
					#6 matched_nearest_gene 
					#7 genes_in_matched_locus
					freq_bin_new = cols[1].split('-')[0] # e.g. 4-5 --> 4
					snpID = cols[2] + ":" + cols[3] # e.g. 8:2342355
					outfile.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\n".format(\
																	snpID, \
																	cols[0], \
																	freq_bin_new, \
																	cols[4], \
																	cols[5], \
																	cols[6], \
																	cols[7] ))
					# gives cols ===> "snpID" "rsID" "freq_bin" "gene_count" "dist_nearest_gene" "ID_nearest_gene" "ID_genes_in_matched_locus"
		elapsed_time = time.time() - start_time
		print "Elapsed_time of writing tab file: %.3f s (%.2f min)" % (elapsed_time, elapsed_time/60)
		file_tab_size = os.path.getsize(file_tab)
		print "Size of concatenated tab file: %s bytes (%.1f MB)" % (file_tab_size, file_tab_size/(1024*1024.0))


### FUNCTION THAT READS tab file and MANIPULATES/EDITS COLUMNS
### NOTICE THE HEADER STRING!
### FUNCTION WORKS with "old tab file format - old cols order and numbers"
# @profile
# def tab2dataframe_with_colmanipulation(file_tab):
# 	header_str = "matched_rsID freq_bin snp_chr snp_position matched_gene_count matched_dist_to_nearest_gene matched_nearest_gene genes_in_matched_locus"
# 	colnames=header_str.split()
# 	#df = pd.read_csv(file_tab, index_col=0, names=colnames, delim_whitespace=True)
# 	start_time = time.time()
# 	print "START: reading CSV file..."
# 	df = pd.read_csv(file_tab, names=colnames, delim_whitespace=True)
# 	elapsed_time = time.time() - start_time
# 	print "END: read CSV file into DataFrame in %s s (%s min)" % (elapsed_time, elapsed_time/60)
	
# 	print "START: mapping chrposID strings..."
# 	start_time = time.time()
# 	df['chrposID'] = df.snp_chr.map(str) + ":" + df.snp_position.map(str) # http://stackoverflow.com/questions/11858472/pandas-combine-string-and-int-columns
# 	elapsed_time = time.time() - start_time
# 	print "END: manipulating chrposID in %s s (%s min)" % (elapsed_time, elapsed_time/60)

# 	df.set_index('chrposID', inplace=True)
# 	df.drop(['snp_chr', 'snp_position'], axis=1, inplace=True) # Deletes unnecessary columns
	
# 	print "START: editing freq_bin strings..."
# 	start_time = time.time()
# 	df['freq_bin'] = df.freq_bin.str.split('-').str.get(0).apply(int) # Converting freq_bin into 'int' so we can sort later on
# 	elapsed_time = time.time() - start_time
# 	print "END: editing freq_bin in %s s (%s min)" % (elapsed_time, elapsed_time/60)

# 	return df


### FUNCTION to read tab file
## NEW HEADER - function work! and use
# @profile
# def tab2dataframe(file_tab):
# 	header_str = "snpID rsID freq_bin gene_count dist_nearest_gene ID_nearest_gene ID_genes_in_matched_locus"
# 	colnames=header_str.split()
# 	start_time = time.time()
# 	print "START: reading CSV file..."
# 	df = pd.read_csv(file_tab, index_col='snpID', names=colnames, delim_whitespace=True) # index is snpID
# 	elapsed_time = time.time() - start_time
# 	print "END: read CSV file into DataFrame in %s s (%s min)" % (elapsed_time, elapsed_time/60)
# 	df.drop(['ID_genes_in_matched_locus'], axis=1, inplace=True) # Deletes unnecessary columns - THIS WORKS. Keep
# 	return (df df_meta)

### FUNCTION THAT READS SPECIFIC COLUMNS
### SPLITs CVS file into two DataFrames: meta
@profile
def tab2dataframe(file_tab):
	## FULL HEADER STRING (look for updates!): "snpID rsID freq_bin gene_count dist_nearest_gene ID_nearest_gene ID_genes_in_matched_locus"
	#0 snpID 
	#1 rsID 
	#2 freq_bin
	#3 gene_count
	#4 dist_nearest_gene 
	#5 ID_nearest_gene
	#6 ID_genes_in_matched_locus 
	header_str_prim = "snpID rsID freq_bin gene_count dist_nearest_gene"
	header_str_meta = "ID_nearest_gene ID_genes_in_matched_locus"
	colnames_prim=header_str_prim.split()
	colnames_meta=header_str_meta.split()
	start_time = time.time()
	#usecols: a subset of columns to return, results in much faster parsing time and lower memory usage.
	print "START: reading CSV file PRIM..."
	df_prim = pd.read_csv(file_tab, index_col=0, names=colnames_prim, delim_whitespace=True, usecols=[0, 1, 2, 3, 4]) # index is snpID
	elapsed_time = time.time() - start_time
	print "END: read CSV file PRIM into DataFrame in %s s (%s min)" % (elapsed_time, elapsed_time/60)
	print "START: reading CSV file META..."
	df_meta = pd.read_csv(file_tab, index_col=0, names=colnames_meta, delim_whitespace=True, usecols=[5, 6]) # index is snpID
	elapsed_time = time.time() - start_time
	print "END: read CSV file META into DataFrame in %s s (%s min)" % (elapsed_time, elapsed_time/60)
	return (df_prim, df_meta)




@profile
def dataframe_prim2hdf(file_hdf5, dataframe):
	# Open store with unique name to identify data stored in it
	#store = pd.HDFStore(file_hdf5, 'w')
	store = pd.HDFStore(file_hdf5, 'w', complevel=9, complib='blosc') # TEST OF COMPRESSION, 05/01/2014
	# writing to HDF5
	#store.put('dummy', df_1KG_snsps, format='fixed') #TODO: change 'key'=dummy to something useful
	# PerformanceWarning:  your performance may suffer as PyTables will pickle object types that it cannot
	#idx_cols = ['freq_bin', 'gene_count', 'dist_nearest_gene'] # OBS: Check this string to the string name in the tab2dataframe
	start_time = time.time()
	print "START: Writing to HDF5 file: %s" % file_hdf5
	
	# TODO: use pd.to_hdf(), 
	# store_compressed = HDFStore('store_compressed.h5', complevel=9, complib='blosc')

	# TABLE
	#store.put('dummy', dataframe, format='table', append=False, data_columns=idx_cols, chunksize=100) # default chunksize = 100000
	#store.put('dummy', dataframe, format='table', append=False, data_columns=idx_cols) 
	store.put('dummy', dataframe, format='table', append=False, data_columns=True) 
	
	# FIXED
	#store.put('dummy', dataframe, format='fixed', append=False)
	
	elapsed_time = time.time() - start_time
	print "END: Elapsed_time of writing file: %.3f s (%.2f min)" % (elapsed_time, elapsed_time/60)
	file_hdf5_size = os.path.getsize(file_hdf5)
	print "Size of HDF5 file: %s bytes (%.1f MB)" % (file_hdf5_size, file_hdf5_size/(1024*1024.0))
	# CONSIDER: df.to_hdf('test.hdf','df',mode='w',format='table',chunksize=2000000)
	store.close()

@profile
def dataframe_meta2hdf(file_hdf5, dataframe):
	#store = pd.HDFStore(file_hdf5, 'w')
	store = pd.HDFStore(file_hdf5, 'w', complevel=9, complib='blosc')
	start_time = time.time()
	print "START: Writing to HDF5 file: %s" % file_hdf5
	#store.put('dummy', dataframe, format='table', append=False, expectedrows=dataframe.shape[0], min_itemsize=100) ===> failed!
	store.put('dummy', dataframe, format='table', append=False, expectedrows=dataframe.shape[0], min_itemsize=100) 
		#chunksize=5000000 ===> failed
		#chunkshape' to (10,)
		#min_itemsize
	elapsed_time = time.time() - start_time
	print "END: Elapsed_time of writing file: %.3f s (%.2f min)" % (elapsed_time, elapsed_time/60)
	file_hdf5_size = os.path.getsize(file_hdf5)
	print "Size of HDF5 file: %s bytes (%.1f MB)" % (file_hdf5_size, file_hdf5_size/(1024*1024.0))
	store.close()



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
path_output = os.path.abspath(args.hdf5_dir)
#prefix_out = '1KGsnp_%s' % args.type
#file_hdf5 = path_output+"/"+prefix_out+'.h5'
#file_tab = path_output+"/"+prefix_out+".tab"
file_hdf5_prim = "{path}/{type}_db.{ext}".format(path=path_output, type=args.type, ext='h5')
file_hdf5_meta = "{path}/{type}_meta.{ext}".format(path=path_output, type=args.type, ext='h5')
file_tab = "{path}/{type}_collection.{ext}".format(path=path_output, type=args.type, ext='tab')
# sanity check. TODO: remove this later!
if True:	
	if not args.type in path_input:
		print "Input dir: %s" % path_input
		print "Could not find --type '%s' in input dir. Are you sure you know what you are doing?" % args.type
		ans = ""
		while ans != 'yes':
		 	ans = raw_input("Confirm: ")
			print "Ok let's start..."


##Read .tab files into one combined data frame
if not os.path.exists(file_tab):
	#concatenate_tab_files(path_input, file_tab)
	write_new_tab_file(path_input, file_tab)
else:	
	print "INFO: Tab file EXISTS: %s. Skipping writing new concatenated file" % file_tab

if not ( os.path.exists(file_hdf5_prim) or os.path.exists(file_hdf5_meta) ): # enter if block if NONE of them exists
	#df_1KG_snsps = tab2dataframe_with_colmanipulation(file_tab)
	(df_prim, df_meta) = tab2dataframe(file_tab)
	dataframe_prim2hdf(file_hdf5_prim, df_prim)
	#dataframe_meta2hdf(file_hdf5_meta, df_meta) ### OBS: WRITING META DATA DISABLED
else:
	if os.path.exists(file_hdf5_prim): print "INFO: HDF5 file PRIM EXISTS: %s. Skipping loading CVS and skipping writing new HDF5 file" % file_hdf5_prim
	if os.path.exists(file_hdf5_meta): print "INFO: HDF5 file META EXISTS: %s. Skipping loading CVS and skipping writing new HDF5 file" % file_hdf5_meta

# #TODO: make function that compresses .tab file after dataframe is created.


	

