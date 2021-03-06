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


import shutil
import glob
import pandas as pd
import gzip

import time
import datetime
import pdb

from memory_profiler import profile

import pplogger

#@profile
def read_ld_buddy_count():
	""" This function has all parameters hardcoded - no arguments is parsed to the function. 
	NOTE: this function RENAMES the column"""

	################# production_v1 ######################
	#ld_buddy_file = "/cvar/jhlab/snpsnap/data/ld_buddy_counts/1KG_snpsnap_production_v1/test_tabs_compile/ld_buddy_count.tab_join_outer_head500" # TEST CASE - this is sorted and will not work for test case. It is sorted so all all the first indexes are 10:100115849...
	#ld_buddy_file = "/cvar/jhlab/snpsnap/data/ld_buddy_counts/1KG_snpsnap_production_v1/test_tabs_compile/ld_buddy_count.tab_join_index_head500" # TEST CASE - USE THIS. Index are aligned. It works (only rsIDs in index)

	#ld_buddy_file = "/cvar/jhlab/snpsnap/data/ld_buddy_counts/1KG_snpsnap_production_v1/complete/ld_buddy_count.tab_join_outer" # USE THIS this file is sorted (gives same result every time)
		#---> USED IN PRODUCTION_V1
	#ld_buddy_file = "/cvar/jhlab/snpsnap/data/ld_buddy_counts/1KG_snpsnap_production_v1/complete/ld_buddy_count.tab_join_index" # alternatively this could be used...
	# NB: this files have rsID as 'index'

	########## NEW FEB 2015* - production_v2 ############
	ld_buddy_file = "/cvar/jhlab/snpsnap/data/ld_buddy_counts/1KG_snpsnap_production_v2/{super_population}/ld_buddy_count.tab_join_outer".format(super_population=super_population) # USE THIS this file is sorted (gives same result every time)	
	#####################################################

	## LD BUDDY COUNT FILE
	#0=rsID
	#1=ld_buddy_count_0.1
	#2=ld_buddy_count_0.2
	#....
	#8=ld_buddy_count_0.8
	#9=ld_buddy_count_0.9
	# NUMBER OF COLUMNS = 10

	logger.info( "START: reading ld buddy file: {}".format(ld_buddy_file) )
	start_time = time.time()
	# The file must not contain any mission values (empty fields or NaN)
	df_ld_buddy = pd.read_csv( ld_buddy_file, delimiter="\t", header=0, index_col=0)
	elapsed_time = time.time() - start_time
	logger.info( "END: reading ld buddy file %s s (%s min)" % (elapsed_time, elapsed_time/60) )

	ld_buddy_cols_renameing = {"ld_buddy_count_0.1":"friends_ld01",
						"ld_buddy_count_0.2":"friends_ld02",
						"ld_buddy_count_0.3":"friends_ld03",
						"ld_buddy_count_0.4":"friends_ld04",
						"ld_buddy_count_0.5":"friends_ld05",
						"ld_buddy_count_0.6":"friends_ld06",
						"ld_buddy_count_0.7":"friends_ld07",
						"ld_buddy_count_0.8":"friends_ld08",
						"ld_buddy_count_0.9":"friends_ld09"}

	df_ld_buddy.rename(columns=ld_buddy_cols_renameing, inplace=True)

	return df_ld_buddy

#@profile
def read_combined_tab(file_combined):
	logger.info( "START: reading combined tab file..." )
	start_time = time.time()
	# The file must not contain any mission values (empty fields or NaN)
	df_combined_tab = pd.read_csv( file_combined, delimiter="\t", header=0, index_col=0)
	elapsed_time = time.time() - start_time
	logger.info( "END: reading combined tab file %s s (%s min)" % (elapsed_time, elapsed_time/60) )

	return df_combined_tab

#@profile
def drop_cols_combined_tabs(df_combined_tab):
	""" 
	This function will drop columns that have no further use. 
	NB 'snp_chr', 'snp_position' are dropped later because they are needed for forming the snpID index 
	"""
	#7=dist_nearest_gene
	#8=dist_nearest_gene_located_within
	#....
	#12=ID_nearest_gene
	#13=ID_nearest_gene_located_within
	#cols2drop = ['dist_nearest_gene', 'dist_nearest_gene_located_within', 'ID_nearest_gene', 'ID_nearest_gene_located_within']
	cols2drop = ['LD_boddies']
	df_combined_tab.drop(cols2drop, axis=1, inplace=True) # axis=1 gives colum axis

	return df_combined_tab

#@profile
def join_dfs(df_ld_buddy, df_combined_tab, path_output):
	logger.info( 'Running join_dfs' )

	df_list = [df_ld_buddy, df_combined_tab]
	df_index_list = [df_ld_buddy.index, df_combined_tab.index]
	df_length_list = [len(df_ld_buddy), len(df_combined_tab)]

	logger.info( 'df_ld_buddy: len of data frame: %s' % len(df_ld_buddy) )
	logger.info( 'df_combined_tab: len of data frame: %s' % len(df_combined_tab) )


	for i in range(len(df_index_list)-1): # ---> gives [0]
		# comparing all indexes and length against the first read data frame (ld0.1)
		elem_ref = 0
		elem_next = i+1

		set_diff = df_index_list[elem_ref].diff(df_index_list[elem_next]) # NB: this computation is a bit heavy. Takes ~ 20 seconds...
		test_set_diff = 'NotDone'
		if len(set_diff) == 0:
			test_set_diff = True # test passed
		else:
			test_set_diff = False
			logger.warning( "%s vs %s | OBS! index set difference with length: %s" % (elem_ref, elem_next, len(set_diff)) )
			logger.warning( "%s vs %s | printing set difference:\n%s" % (elem_ref, elem_next, set_diff) )
		
		test_index_equality = df_index_list[elem_ref].equals(df_index_list[elem_next]) # pandas index method
		test_lenght = df_length_list[elem_ref] == df_length_list[elem_next]
		logger.warning( "test_set_diff | %s vs %s | passed = %s" % (elem_ref, elem_next, test_set_diff) )
		logger.warning( "test_index_equality | %s vs %s | passed = %s" % (elem_ref, elem_next, test_index_equality) )
		logger.warning( "test_lenght | %s vs %s | passed = %s" % (elem_ref, elem_next, test_lenght) )
		### Additional tests:
		# 1) check that for each SNP the ld_boddy_count is MONOTONIC DECREASING as you INCREASE ld

	# concatenate data frames horizontally
	start_time = time.time()
	logger.info( 'JOIN_OUTER: start concat and writing csv' )
	df_merged = pd.concat(df_list, axis=1, join='outer') # ---> row indexes will be unioned and sorted.
														# ***OBS***: index name is NOT kept using 'outer' - I found out about this the hard way
	df_merged.index.name = df_list[0].index.name # ADDED 07/04/2014 - COPYING the index name from the first df in the df_list to fix that index_label is lost using join='outer'
	# alternative approach which DOES NOT loose the index name: df_merged.to_csv(outfile_ld_buddy+"_join_outer", sep='\t', header=True, index=True, index_label=None) # index_label=None ==> use index names from df

	elapsed_time = time.time()-start_time
	logger.info( "DONE | elapsed time: %s min" % (elapsed_time/60, ) )
	logger.info( 'JOIN_OUTER: len of data frame: %s' % len(df_merged) )

	logger.info( 'Will rearrange column order of df_merged now' )
	cols_df_combined_tab = df_combined_tab.columns.tolist()
	cols_df_ld_buddy = df_ld_buddy.columns.tolist()
	col_order = cols_df_combined_tab + cols_df_ld_buddy # THE ORDER IS IMPORTANT --> combined_tab should go first for a nice format
	df_merged = df_merged.ix[:, col_order] # REARRANGE COLUMN ORDER - memory heavy?


	###################################### OUTCOMMENTED SNPsnap production v2 ######################################
	### Pascal found no reason to write these two rather large files to disk - they are not very helpful:
	# - df_merged.tab ~ 3 GB
	# - df_null.tab ~ 1.5 GB

	# if df_merged.isnull().any(axis=0).any(axis=0): # same as df_merged.isnull().any().any()
	# 	df_null = df_merged[df_merged.isnull().any(axis=1)]
	# 	logger.warning( 'JOIN_OUTER isnull(): len of data frame: %s' % len(df_null) )
	# 	#logger.warning( df_null )

	# 	file_df_null = path_output+"/df_null.tab"
	# 	logger.warning( 'Will write df_null to file: %s' % file_df_null )
	# 	df_null.to_csv(file_df_null, sep='\t', header=True, index=True, index_label='snpID')
	# else:
	# 	logger.warning( 'JOIN_OUTER: there is NO null values' )

	# ############################ WRITE OUT df_merged ###########################
	# file_df_merged = path_output+"/df_merged.tab"
	# logger.info( 'Will write df_merged to file: %s' % file_df_merged )
	# df_merged.to_csv(file_df_merged, sep='\t', header=True, index=True, index_label='snpID')
	# logger.info( 'DONE writing df_merged to file' )


	return df_merged



### FUNCTION to read all tabs and append to data frame.
## Will use DataFrame string manipulation to make correct collection
## Will REMOVE rows with duplicates
## Write DataFrame to CVS
#@profile
def df2collection(df, file_collection, file_dup, no_compression):
	""" df is the merged df """
	## COLUMNS IN DATA FRAME - version JUNE 2014, production_v1
	#1=snpID ---> 
	#1=rsID  
		# ---> BEFORE: NOTE=this is index in the unmodified Data Frame | ACTION:index will be changed inplace (with set_index), thus effectively removing the rsID index | WHERE=df2collection()
		# ---> UNtested. Added 03/07/2014: the rsID will be a column. The new Output collection file will then have 22 columns
	#2=freq_bin
	#3=snp_chr ** ----> ACTION=WILL BE REMOVED | WHERE=df2collection()
	#4=snp_position ** ----> ACTION=WILL BE REMOVED | WHERE=df2collection()
	#5=gene_count
	#6=dist_nearest_gene_snpsnap
	#7=dist_nearest_gene
	#8=dist_nearest_gene_located_within
	#9=loci_upstream
	#10=loci_downstream
	#11=ID_nearest_gene_snpsnap
	#12=ID_nearest_gene
	#13=ID_nearest_gene_located_within
	#x=LD_boddies ** ----> ACTION=REMOVED | WHERE=drop_cols_combined_tabs()
	#14=ID_genes_in_matched_locus

	#15=ld_buddy_count_0.1 ** ----> ACTION=RENAMED | WHERE=read_ld_buddy_count()
	#....
	#23=ld_buddy_count_0.9 ** ----> ACTION=RENAMED | WHERE=read_ld_buddy_count()

	# INPUT=Data Frame (note LD_buddies already removed)
		# - NUMBER OF COLUMNS (including index) = 23
	# OUTPUT=Collection tab file
		# - NUMBER OF COLUMNS (including index) = 21
		# - columns removed here: 2 (snp_chr and snp_position)
		# - test it with: 
			#- perl -ane '$c = split("\t"); print "$c\n"; last' ld0.5_collection.tab
			# gives 21

	## CONSIDER: using df.reset_index() (the inverse operation to set_index)
		# 1) df.reset_index(inplace=True)  # <-- This transfers the index values into the DataFrame's columns and sets a simple integer index.
		# 2) df.set_index('snpID', inplace=True) # <--- or consider using append=True to make two indexes
		# 3) reorder column order to place 'rsID' as the 1. column (since 'snpID' is now the index)

	logger.info( "START: mapping snpID strings..." )
	start_time = time.time()
	df['snpID'] = df.snp_chr.map(str) + ":" + df.snp_position.map(str) # http://stackoverflow.com/questions/11858472/pandas-combine-string-and-int-columns
	elapsed_time = time.time() - start_time
	logger.info( "END: manipulating snpID in %s s (%s min)" % (elapsed_time, elapsed_time/60) )

	logger.info( "Setting index on DataFrame..." )
	df.reset_index(inplace=True) # WORKS - Added 03/07/2014, but only run in SNPsnap v2. This will 'free' the rsID index and use it as a column. The column will be placed as the FIRST COLUMN (tested)
	### ^^^ OBS: please check that the index is in fact something useful like rsID because it will be added as a column to the data frame (because drop=False by default)
	df.set_index('snpID', inplace=True) # by default 'drop=True' ---> deletes columns to be used as the new index. That is, deletes the 'snpID' column
	
	################## DELETE unnecessary columns ##################
	### AFTER RUNNING SNPsnap v2 Pipeline: OUTCOMMENT THE BELOW df.drop() CODE.
	# --> IT IS USEFUL TO HAVE a COLUMN OF snp_chr and snp_position
	logger.info( "Dropping columns 'snp_chr', 'snp_position'" )
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
		df.to_csv(file_collection, sep='\t', header=True, index=True, index_label='snpID')
		df_dup.to_csv(file_dup, sep='\t', header=True, index=True, index_label='snpID')
	else:
		logger.info( "INFO: compressed option is ON" )
		# Open file handles
		f_tab = gzip.open(file_collection, 'wb')
		f_dup = gzip.open(file_dup, 'wb')
		df.to_csv(f_tab, sep='\t', header=True, index=True, index_label='snpID')
		df_dup.to_csv(f_dup, sep='\t', header=True, index=True, index_label='snpID')
		f_tab.close()
		f_dup.close()
	elapsed_time = time.time() - start_time
	logger.info( "END: Done writing collection file: %.3f s (%.2f min)" % (elapsed_time, elapsed_time/60) )
	file_tab_size = os.path.getsize(file_collection)
	logger.info( "Size of concatenated tab file: %s bytes (%.1f MB)" % (file_tab_size, file_tab_size/(1024*1024.0)) )


### NEW FUNCTION THAT READS SPECIFIC COLUMNS. 
# CSV contains header!
# UPDATED HEADER!
# NO SPLITTING INTO prim and meta
#@profile
def collection2dataframe(file_collection, no_compression):
	#col_string = "snpID freq_bin gene_count dist_nearest_gene_snpsnap friends_ld01 friends_ld02 friends_ld03 friends_ld04 friends_ld05 friends_ld06 friends_ld07 friends_ld08 friends_ld09"
	col_string = "snpID rsID freq_bin gene_count dist_nearest_gene_snpsnap friends_ld01 friends_ld02 friends_ld03 friends_ld04 friends_ld05 friends_ld06 friends_ld07 friends_ld08 friends_ld09" #UNtested. Added 03/07/2014. 
	cols2read = col_string.split()
	logger.info( "Will read the following columns from the collection: %s" % col_string )

	logger.info( "START: reading CSV file PRIM..." )
	start_time = time.time()	
	if no_compression:
		logger.info( "INFO: compressed option is OFF" )
		df_prim = pd.read_csv(file_collection, index_col=0, header=0, delimiter="\t", usecols=cols2read) # index is snpID
	else:
		logger.info( "INFO: compressed option is ON" )
		f_tab = gzip.open(file_collection, 'rb')
		df_prim = pd.read_csv(f_tab, index_col=0, header=0, delimiter="\t", usecols=cols2read) # index is snpID
		f_tab.close()
	elapsed_time = time.time() - start_time
	logger.info( "END: read CSV file PRIM into DataFrame in %s s (%s min)" % (elapsed_time, elapsed_time/60) )
	return df_prim


#@profile
def dataframe_prim2hdf(file_hdf5, dataframe):
	#store = pd.HDFStore(file_hdf5, 'w', complevel=9, complib='blosc') # 
	store = pd.HDFStore(file_hdf5, 'w') # NO COMPRESSION
	start_time = time.time()
	logger.info( "START: Writing to HDF5 file: %s" % file_hdf5 )
	
	store.put('dummy', dataframe, format='table', append=False, data_columns=True) 
	
	elapsed_time = time.time() - start_time
	logger.info( "END: Elapsed_time of writing file: %.3f s (%.2f min)" % (elapsed_time, elapsed_time/60) )
	file_hdf5_size = os.path.getsize(file_hdf5)
	logger.info( "Size of HDF5 file: %s bytes (%.1f MB)" % (file_hdf5_size, file_hdf5_size/(1024*1024.0)) )
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


arg_parser.add_argument("--output_dir", help="Path to write HDF5 and Collection file. DIR WILL BE CREATED IF IT DOES NOT EXISTS.", required=True)
## USED BEFORE JUNE 2014
# arg_parser.add_argument("--dist_type", \
# 	help="Type of distance used, e.g. ld0.5 or kb100", \
# 	required=True)

arg_parser.add_argument("--super_population", help="IMPORTANT: This argument is used to LOCATE THE ld_buddy_file in the function 'read_ld_buddy_count()'", required=True)
arg_parser.add_argument("--distance_type", help="ld or kb. This argument is only used to construct sensable output files names", required=True)
arg_parser.add_argument("--distance_cutoff", help="r2, or kb distance.  This argument is only used to construct sensable output files names", required=True)
## SNPsnap production v1
#arg_parser.add_argument("--log_dir", help="Optional argument. If a dir (or any value) is given, the program will write out a log file to the given dir. The log filename will be {current_script_name}_{distance_type}{distance_cutoff}, e.g. tabs_compile_ld0.5", default=None) # Notice that argparse by uses 'default=None' by default

arg_parser.add_argument("--no_compression", \
	help="If set, do NOT compress collection.tba and duplicate.tab files with gzip. Default is to compress files", \
	action='store_true')
	#store_true option automatically creates a default value of False
	#store_false will default to True when the command-line argument is not present.
args = arg_parser.parse_args()

###################################### FIRST PARAMS - used for logger ######################################
super_population = args.super_population

distance_type = args.distance_type
distance_cutoff = args.distance_cutoff




###################################### CONSTANTS ######################################
start_time_script = time.time()
batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')


###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')

log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step6_tabs_compile/{super_population}".format(super_population=super_population) #OBS VARIABLE
if not os.path.exists(log_dir):
	os.makedirs(log_dir)
log_name = "{current_script_name}_{distance_type}{distance_cutoff}_{batch_time}".format(current_script_name=current_script_name, distance_type=distance_type, distance_cutoff=distance_cutoff, batch_time=batch_time)

logger = pplogger.Logger(name=log_name, log_dir=log_dir, log_format=1, enabled=True).get()
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################


if args.no_compression:
	logger.info("Runinng compression: NO")
else:
	logger.info("Runinng compression: YES")

file_combined = args.combined_tabfile

# Trailing slash are removed/corrected - NICE!
path_output = os.path.abspath(args.output_dir)
if not os.path.exists(path_output):
	logger.warning( "path_output does not exists. Will create it: {}".format(path_output) )
	os.makedirs(path_output)

file_hdf5_prim = "{path}/{type}{cutoff}_db.{ext}".format(path=path_output, type=distance_type, cutoff=distance_cutoff, ext='h5')

if args.no_compression:
	file_collection = "{path}/{type}{cutoff}_collection.{ext}".format(path=path_output, type=distance_type, cutoff=distance_cutoff, ext='tab')
	file_dup = "{path}/{type}{cutoff}_duplicates.{ext}".format(path=path_output, type=distance_type, cutoff=distance_cutoff, ext='tab')
else:
	file_collection = "{path}/{type}{cutoff}_collection.{ext}".format(path=path_output, type=distance_type, cutoff=distance_cutoff, ext='tab.gz')
	file_dup = "{path}/{type}{cutoff}_duplicates.{ext}".format(path=path_output, type=distance_type, cutoff=distance_cutoff, ext='tab.gz')



##Read .tab files into one combined data frame
if not os.path.exists(file_collection):
	df_ld_buddy = read_ld_buddy_count()
	df_combined_tab = read_combined_tab(file_combined)
	df_combined_tab = drop_cols_combined_tabs(df_combined_tab)
	df_merged = join_dfs(df_ld_buddy, df_combined_tab, path_output) # path_output is used to write out df_null and df_merged
	# parsing on df_merged
	df2collection(df_merged, file_collection, file_dup, no_compression=args.no_compression) # this function manipulates the merged df and write it to a file
else:	
	logger.warning( "Collection EXISTS: %s. Skipping writing new collection" % file_collection )

if not os.path.exists(file_hdf5_prim):
	df_prim = collection2dataframe(file_collection, no_compression=args.no_compression)
	dataframe_prim2hdf(file_hdf5_prim, df_prim)
else:
	logger.warning("HDF5 file PRIM EXISTS: %s. Skipping loading collection and skipping writing new HDF5 file" % file_hdf5_prim )



	

