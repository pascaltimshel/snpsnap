#!/usr/bin/env python2.7

# Example call:
# test data
# ./compile_tabs.py --input_dir /Users/pascaltimshel/snpsnap/data/step2/1KG_test_thin0.02_duprm/ld0.5/stat_gene_density --hdf5_dir /Users/pascaltimshel/snpsnap/data/step3/test --type ld0.5
# full ld0.5
# ./compile_tabs.py --input_dir /Users/pascaltimshel/snpsnap/data/step2/1KG_full_duprm_nolim/ld0.5/stat_gene_density --hdf5_dir /Users/pascaltimshel/snpsnap/data/step3 --type ld0.5

# Run time
# The program runs in about 6.5 min on Pascal's MBP on the full data set
# Reading CSV takes 4 min
#

# Memory usage - 05/06/2014 (after boundary cols included):
# This program uses about 6-10 GB of memory when using the full data set of size ~900 MB
# The data frame uses 2 GB, and the split uses an additional 2 GB

#TODO
#0) Write shell script that calls this function many times


import os
import sys
import argparse
import collections
from queue import QueueJob,ArgparseAdditionalUtils


import shutil
import glob
import pandas as pd
import gzip

import time
import pdb

import memory_profiler


### FUNCTION to read all tabs and append to data frame.
## Will use DataFrame string manipulation to make correct collection
## Will REMOVE rows with duplicates
## Write DataFrame to CVS
@memory_profiler.profile
def tab2collection(inpath, file_tab, file_dup, no_compression):
	tabfiles = glob.glob(inpath+"/*.tab")
	if not len(tabfiles) == 50:
		print "Error: did not find 50 .tab files as expected in path: %s" % inpath
		print "Number of tabfiles found: %s" % len(tabfiles)
		print "Aborting script..."
		sys.exit(1)
	# Sorting on freq bin
	tabfiles.sort(key=lambda x: int(x.split('/')[-1].split('freq')[-1].split('-')[0])) # this step is not strictly needed. Unreadable code
	

	## NEW JUNE 2014
	#1=rsID
	#2=freq_bin
	#3=chromosome number of rsID
	#4=position of rsID
	#5=gene count in matched locus
	#6=dist to nearest gene - SNPSNAP DISTANCE (NEW!)
	#7=dist to nearest gene
	#8=dist to nearest gene LOCATED WITHIN (NEW!)
	#9=boundary_upstream
	#10=boundary_downstream
	#11=nearest_gene SNPSNAP (NEW!)
	#12=nearest_gene
	#13=nearest_gene LOCATED WITHIN (may be empty) (NEW!)
	#14=ld buddies count (NEW!)
	#15=genes in matches locus, multiple ENSEMBL IDs



	header_str = "rsID freq_bin snp_chr snp_position gene_count dist_nearest_gene_snpsnap dist_nearest_gene dist_nearest_gene_located_within loci_upstream loci_downstream ID_nearest_gene_snpsnap ID_nearest_gene ID_nearest_gene_located_within LD_boddies ID_genes_in_matched_locus"
	colnames =header_str.split()


	df = pd.DataFrame(columns=colnames) # NOTICE THE NAMEING OF COLUMNS. CHECK THIS LATER!!!
	print "START: reading tab files and appending to DataFrame..."
	start_time = time.time()
	for counter, tabfile in enumerate(tabfiles, start=1):
		print "Reading tabfile #%s/#%s into DataFrame: %s" % (counter, len(tabfiles), os.path.basename(tabfile))
		df = df.append(pd.read_csv(tabfile, names=colnames, delim_whitespace=True)) # appending read CSV. consider not setting names
	elapsed_time = time.time() - start_time
	print "END: read CSV file into DataFrame in %s s (%s min)" % (elapsed_time, elapsed_time/60)

	print "START: mapping snpID strings..."
	start_time = time.time()
	df['snpID'] = df.snp_chr.map(str) + ":" + df.snp_position.map(str) # http://stackoverflow.com/questions/11858472/pandas-combine-string-and-int-columns
	elapsed_time = time.time() - start_time
	print "END: manipulating snpID in %s s (%s min)" % (elapsed_time, elapsed_time/60)

	print "Setting index on DataFrame and dropping columns"
	df.set_index('snpID', inplace=True)
	df.drop(['snp_chr', 'snp_position'], axis=1, inplace=True) # Deletes unnecessary columns


	print "START: removing duplicate snpID in df.index..."
	start_time = time.time()
	idx_bool = pd.Series(df.index).duplicated().values # returns bool for all values that are duplicated
	df_dup = df.ix[df.index[idx_bool]] # selecting rows with duplicate index
	n_duplicate_snpIDs = len(df.index[idx_bool]) # or np.sum(idx_bool)
	df.drop(df.index[idx_bool], inplace=True) # dropping duplicate values.
	elapsed_time = time.time() - start_time
	print "END: removing duplicate snpID in %s s (%s min)" % (elapsed_time, elapsed_time/60)

	print "### Results from duplicate removal ###"
	print "N duplicate row removed: %d, i.e. snpIDs with more than one entry is %s" % ( len(df_dup),  n_duplicate_snpIDs)
	print "Size of DataFrame after duplicate removal: %d" % len(df)


	print "START: writing DataFrames to CSV..."
	start_time = time.time()
	if no_compression:
		print "INFO: compressed option is OFF"
		df.to_csv(file_tab, sep='\t', header=True, index=True, index_label='snpID')
		df_dup.to_csv(file_dup, sep='\t', header=True, index=True, index_label='snpID')
	else:
		print "INFO: compressed option is ON"
		# Open file handles
		f_tab = gzip.open(file_tab, 'wb')
		f_dup = gzip.open(file_dup, 'wb')
		df.to_csv(f_tab, sep='\t', header=True, index=True, index_label='snpID')
		df_dup.to_csv(f_dup, sep='\t', header=True, index=True, index_label='snpID')
		f_tab.close()
		f_dup.close()
	elapsed_time = time.time() - start_time
	print "END: Done writing collection file: %.3f s (%.2f min)" % (elapsed_time, elapsed_time/60)
	file_tab_size = os.path.getsize(file_tab)
	print "Size of concatenated tab file: %s bytes (%.1f MB)" % (file_tab_size, file_tab_size/(1024*1024.0))


### NEW FUNCTION THAT READS SPECIFIC COLUMNS. 
# CSV contains header!
# UPDATED HEADER!
# NO SPLITTING INTO prim and meta
@memory_profiler.profile
def tab2dataframe(file_tab, no_compression):
	# TODO: read compressed file

	# Columns in COLLECTION:
	#0 snpID 
	#1 rsID 
	#2 freq_bin 
	#3 gene_count
	#4 dist_to_nearest_gene 
	#5=loci_upstream #NEW
	#6=loci_downstream #NEW
	#7 ID_nearest_gene 
	#8 ID_in_matched_locus
	print "START: reading CSV file PRIM..."
	start_time = time.time()
	if no_compression:
		print "INFO: compressed option is OFF"
		df_prim = pd.read_csv(file_tab, index_col=0, header=0, delim_whitespace=True, usecols=[0, 1, 2, 3, 4]) # index is snpID
	else:
		print "INFO: compressed option is ON"
		f_tab = gzip.open(file_tab, 'rb')
		df_prim = pd.read_csv(f_tab, index_col=0, header=0, delim_whitespace=True, usecols=[0, 1, 2, 3, 4]) # index is snpID
		f_tab.close()
	elapsed_time = time.time() - start_time
	print "END: read CSV file PRIM into DataFrame in %s s (%s min)" % (elapsed_time, elapsed_time/60)
	return df_prim


@memory_profiler.profile
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


#
#Parse Arguments
#
arg_parser = argparse.ArgumentParser(description="Read multiple .tab files from e.g. /stat_gene_density and write all tab files to combined file 1KGsnps.h5")
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
arg_parser.add_argument("--no_compression", \
	help="If set, do NOT compress collection.tba and duplicate.tab files with gzip. Default is to compress files", \
	action='store_true')
	#store_true option automatically creates a default value of False
	#store_false will default to True when the command-line argument is not present.
args = arg_parser.parse_args()

# Trailing slash are removed/corrected - NICE!
path_input = os.path.abspath(args.input_dir) 
path_output = os.path.abspath(args.hdf5_dir)
file_hdf5_prim = "{path}/{type}_db.{ext}".format(path=path_output, type=args.type, ext='h5')
file_hdf5_meta = "{path}/{type}_meta.{ext}".format(path=path_output, type=args.type, ext='h5')

if args.no_compression:
	file_tab = "{path}/{type}_collection.{ext}".format(path=path_output, type=args.type, ext='tab')
	file_dup = "{path}/{type}_duplicates.{ext}".format(path=path_output, type=args.type, ext='tab')
else:
	file_tab = "{path}/{type}_collection.{ext}".format(path=path_output, type=args.type, ext='tab.gz')
	file_dup = "{path}/{type}_duplicates.{ext}".format(path=path_output, type=args.type, ext='tab.gz')

# sanity check. TODO: remove this later!
if False:	
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
	#write_new_tab_file(path_input, file_tab)
	tab2collection(path_input, file_tab, file_dup, no_compression=args.no_compression)
else:	
	print "INFO: Tab file EXISTS: %s. Skipping writing new concatenated file" % file_tab

#if not ( os.path.exists(file_hdf5_prim) or os.path.exists(file_hdf5_meta) ): # enter if block if NONE of them exists
if not ( os.path.exists(file_hdf5_prim) ): # enter if block if NONE of them exists
	#df_1KG_snsps = tab2dataframe_with_colmanipulation(file_tab)
	#(df_prim, df_meta) = tab2dataframe_split_meta_and_prim(file_tab)
	
	df_prim = tab2dataframe(file_tab, no_compression=args.no_compression)
	dataframe_prim2hdf(file_hdf5_prim, df_prim)

	### OBS: WRITING META DATA DISABLED:
	#dataframe_meta2hdf(file_hdf5_meta, df_meta) 
else:
	if os.path.exists(file_hdf5_prim): print "INFO: HDF5 file PRIM EXISTS: %s. Skipping loading CVS and skipping writing new HDF5 file" % file_hdf5_prim
	#if os.path.exists(file_hdf5_meta): print "INFO: HDF5 file META EXISTS: %s. Skipping loading CVS and skipping writing new HDF5 file" % file_hdf5_meta

# #TODO: make function that compresses .tab file after dataframe is created.


	

