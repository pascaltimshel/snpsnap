#!/usr/bin/env python2.7

# Example call:
# test data
# ./compile_tabs.py --input_dir /Users/pascaltimshel/snpsnap/data/step2/1KG_test_thin0.02_duprm/ld0.5/stat_gene_density --hdf5_dir /Users/pascaltimshel/snpsnap/data/step3/test --type ld0.5
# full ld0.5
# ./compile_tabs.py --input_dir /Users/pascaltimshel/snpsnap/data/step2/1KG_full_duprm_nolim/ld0.5/stat_gene_density --hdf5_dir /Users/pascaltimshel/snpsnap/data/step3 --type ld0.5


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


def read_ld_buddy_count():
	""" This function has all parameters hardcoded - no arguments is parsed to the function. """
	ld_buddy_file = "/cvar/jhlab/snpsnap/data/ld_buddy_counts/1KG_snpsnap_production_v1/complete/ld_buddy_count.tab_join_outer" # this file is sorted
	#ld_buddy_file = "/cvar/jhlab/snpsnap/data/ld_buddy_counts/1KG_snpsnap_production_v1/complete/ld_buddy_count.tab_join_index" # alternatively this could be used...
	# NB: this files have rsID as 'index'

	## LD BUDDY COUNT FILE
	#0=rsID
	#1=ld_buddy_count_0.1
	#2=ld_buddy_count_0.2
	#....
	#8=ld_buddy_count_0.8
	#9=ld_buddy_count_0.9
	# NUMBER OF COLUMNS = 10

	logger.info( "START: reading ld buddy file..." )
	start_time = time.time()
	# The file must not contain any mission values (empty fields or NaN)
	df_ld_buddy = pd.read_csv( ld_buddy_file, delimiter="\t", header=0, index_col=0)
	elapsed_time = time.time() - start_time
	logger.info( "END: reading ld buddy file %s s (%s min)" % (elapsed_time, elapsed_time/60) )

	return df_ld_buddy


def read_combined_tab(file_tab):
	logger.info( "START: reading combined tab file..." )
	start_time = time.time()
	# The file must not contain any mission values (empty fields or NaN)
	df_combined_tab = pd.read_csv( file_tab, delimiter="\t", header=0, index_col=0)
	elapsed_time = time.time() - start_time
	logger.info( "END: reading combined tab file %s s (%s min)" % (elapsed_time, elapsed_time/60) )

	return df_combined_tab



def add_ld_buddy_df(df_ld_buddy, df_combined_tab):
	


### FUNCTION to read all tabs and append to data frame.
## Will use DataFrame string manipulation to make correct collection
## Will REMOVE rows with duplicates
## Write DataFrame to CVS
@memory_profiler.profile
def tab2collection(file_tab, file_dup, no_compression):

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


	logger.info( "START: reading tab file..." )
	start_time = time.time()
	df = pd.read_csv( outpath_combined_tab, delimiter="\t", header=0, index_col=0)
	elapsed_time = time.time() - start_time
	logger.info( "END: read CSV file into DataFrame in %s s (%s min)" % (elapsed_time, elapsed_time/60) )

	logger.info( "START: mapping snpID strings..." )
	start_time = time.time()
	df['snpID'] = df.snp_chr.map(str) + ":" + df.snp_position.map(str) # http://stackoverflow.com/questions/11858472/pandas-combine-string-and-int-columns
	elapsed_time = time.time() - start_time
	logger.info( "END: manipulating snpID in %s s (%s min)" % (elapsed_time, elapsed_time/60) )

	logger.info( "Setting index on DataFrame and dropping columns" )
	df.set_index('snpID', inplace=True)
	df.drop(['snp_chr', 'snp_position'], axis=1, inplace=True) # Deletes unnecessary columns


	logger.info( "START: removing duplicate snpID in df.index..." )
	start_time = time.time()
	idx_bool = pd.Series(df.index).duplicated().values # returns bool for all values that are duplicated
	df_dup = df.ix[df.index[idx_bool]] # selecting rows with duplicate index
	n_duplicate_snpIDs = len(df.index[idx_bool]) # or np.sum(idx_bool)
	df.drop(df.index[idx_bool], inplace=True) # dropping duplicate values.
	elapsed_time = time.time() - start_time
	logger.info( "END: removing duplicate snpID in %s s (%s min)" % (elapsed_time, elapsed_time/60) )

	logger.info( "### Results from duplicate removal ###" )
	logger.info( "N duplicate row removed: %d, i.e. snpIDs with more than one entry is %s" % ( len(df_dup),  n_duplicate_snpIDs) )
	logger.info( "Size of DataFrame after duplicate removal: %d" % len(df) )


	logger.info( "START: writing DataFrames to CSV..." )
	start_time = time.time()
	if no_compression:
		logger.info( "INFO: compressed option is OFF" )
		df.to_csv(file_tab, sep='\t', header=True, index=True, index_label='snpID')
		df_dup.to_csv(file_dup, sep='\t', header=True, index=True, index_label='snpID')
	else:
		logger.info( "INFO: compressed option is ON" )
		# Open file handles
		f_tab = gzip.open(file_tab, 'wb')
		f_dup = gzip.open(file_dup, 'wb')
		df.to_csv(f_tab, sep='\t', header=True, index=True, index_label='snpID')
		df_dup.to_csv(f_dup, sep='\t', header=True, index=True, index_label='snpID')
		f_tab.close()
		f_dup.close()
	elapsed_time = time.time() - start_time
	logger.info( "END: Done writing collection file: %.3f s (%.2f min)" % (elapsed_time, elapsed_time/60) )
	file_tab_size = os.path.getsize(file_tab)
	logger.info( "Size of concatenated tab file: %s bytes (%.1f MB)" % (file_tab_size, file_tab_size/(1024*1024.0)) )


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
	logger.info( "START: reading CSV file PRIM..." )
	start_time = time.time()
	if no_compression:
		logger.info( "INFO: compressed option is OFF" )
		df_prim = pd.read_csv(file_tab, index_col=0, header=0, delim_whitespace=True, usecols=[0, 1, 2, 3, 4]) # index is snpID
	else:
		logger.info( "INFO: compressed option is ON" )
		f_tab = gzip.open(file_tab, 'rb')
		df_prim = pd.read_csv(f_tab, index_col=0, header=0, delim_whitespace=True, usecols=[0, 1, 2, 3, 4]) # index is snpID
		f_tab.close()
	elapsed_time = time.time() - start_time
	logger.info( "END: read CSV file PRIM into DataFrame in %s s (%s min)" % (elapsed_time, elapsed_time/60) )
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
	logger.info( "START: Writing to HDF5 file: %s" % file_hdf5 )
	
	# TODO: use pd.to_hdf(), 
	# store_compressed = HDFStore('store_compressed.h5', complevel=9, complib='blosc')

	# TABLE
	#store.put('dummy', dataframe, format='table', append=False, data_columns=idx_cols, chunksize=100) # default chunksize = 100000
	#store.put('dummy', dataframe, format='table', append=False, data_columns=idx_cols) 
	store.put('dummy', dataframe, format='table', append=False, data_columns=True) 
	
	# FIXED
	#store.put('dummy', dataframe, format='fixed', append=False)
	
	elapsed_time = time.time() - start_time
	logger.info( "END: Elapsed_time of writing file: %.3f s (%.2f min)" % (elapsed_time, elapsed_time/60) )
	file_hdf5_size = os.path.getsize(file_hdf5)
	logger.info( "Size of HDF5 file: %s bytes (%.1f MB)" % (file_hdf5_size, file_hdf5_size/(1024*1024.0)) )
	# CONSIDER: df.to_hdf('test.hdf','df',mode='w',format='table',chunksize=2000000)
	store.close()


#
#Parse Arguments
#
arg_parser = argparse.ArgumentParser(description="Read multiple .tab files from e.g. /stat_gene_density and write all tab files to combined file 1KGsnps.h5")
## USED BEFORE JUNE 2014
# arg_parser.add_argument("--input_dir", \
# 	help="""Input directory CONTAINING tab files].
# e.g. /home/projects/tp/childrens/snpsnap/data/step2/1KG_full_queue/ld0.5/stat_gene_density
# NB. please use symlinks in the path, i.e. do not use /net/home...""", \
# 	required=True)

arg_parser.add_argument("--combined_tabfile", help="""e.g. /data/step3/1KG_snpsnap_production_v1/ld0.5/combined.tab""", required=True)


arg_parser.add_argument("--hdf5_dir", \
	type=ArgparseAdditionalUtils.check_if_writable, \
	help="Path to write HDF5 file. Dir must exist.", \
	required=True)
## USED BEFORE JUNE 2014
# arg_parser.add_argument("--dist_type", \
# 	help="Type of distance used, e.g. ld0.5 or kb100", \
# 	required=True)
arg_parser.add_argument("--distance_type", help="ld or kb", required=True)
arg_parser.add_argument("--distance_cutoff", help="r2, or kb distance", required=True)
arg_parser.add_argument("--log_dir", help="Optional argument. If a dir (or any value) is given, the program will write out a log file to the given dir. The log filename will be {current_script_name}_{distance_type}{distance_cutoff}, e.g. tabs_compile_ld0.5", default=None) # Notice that argparse by uses 'default=None' by default

arg_parser.add_argument("--no_compression", \
	help="If set, do NOT compress collection.tba and duplicate.tab files with gzip. Default is to compress files", \
	action='store_true')
	#store_true option automatically creates a default value of False
	#store_false will default to True when the command-line argument is not present.
args = arg_parser.parse_args()


###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')
logger = None # global space
if args.log_dir:
	log_dir=args.log_dir
	logger = pplogger.Logger(name=current_script_name, log_dir=log_dir, log_format=1, enabled=True).get()
	def handleException(excType, excValue, traceback, logger=logger):
		logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
	#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
	sys.excepthook = handleException
	logger.info( "INSTANTIATION NOTE: placeholder" )
else:
	logger = pplogger.Logger(name=current_script_name, enabled=False).get()
###########################################################################################

###################################### CONSTANTS ######################################
start_time_script = time.time()
batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')

distance_type = args.distance_type
distance_cutoff = args.distance_cutoff
if args.no_compression:
	logger.info("Runinng compression: NO")
else:
	logger.info("Runinng compression: YES")

# Trailing slash are removed/corrected - NICE!
path_input = os.path.abspath(args.input_dir) 
path_output = os.path.abspath(args.hdf5_dir)
file_hdf5_prim = "{path}/{type}{cutoff}_db.{ext}".format(path=path_output, type=distance_type, cutoff=distance_cutoff, ext='h5')

if args.no_compression:
	file_tab = "{path}/{type}{cutoff}_collection.{ext}".format(path=path_output, type=distance_type, cutoff=distance_cutoff, ext='tab')
	file_dup = "{path}/{type}{cutoff}_duplicates.{ext}".format(path=path_output, type=distance_type, cutoff=distance_cutoff, ext='tab')
else:
	file_tab = "{path}/{type}{cutoff}_collection.{ext}".format(path=path_output, type=distance_type, cutoff=distance_cutoff, ext='tab.gz')
	file_dup = "{path}/{type}{cutoff}_duplicates.{ext}".format(path=path_output, type=distance_type, cutoff=distance_cutoff, ext='tab.gz')



##Read .tab files into one combined data frame
if not os.path.exists(file_tab):
	tab2collection(file_tab, file_dup, no_compression=args.no_compression)
else:	
	logger.warning( "Tab file EXISTS: %s. Skipping writing new concatenated file" % file_tab )

if not os.path.exists(file_hdf5_prim):
	df_prim = tab2dataframe(file_tab, no_compression=args.no_compression)
	dataframe_prim2hdf(file_hdf5_prim, df_prim)
else:
	logger.warning("HDF5 file PRIM EXISTS: %s. Skipping loading CVS and skipping writing new HDF5 file" % file_hdf5_prim )



	

