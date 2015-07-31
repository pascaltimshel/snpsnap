#!/usr/bin/env python2.7

# DATE OF CREATION: 30th July 2015

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

###################################### REMARK ######################################
# THIS SCRIPT IS NOT "POLISHED" - it is a bit of a *HACK*! 
	# --> *HARD CODED PATHS*
# Read it through before running it....
####################################################################################

def read_collection(file_collection):

	logger.info( "START: reading CSV file PRIM..." )
	start_time = time.time()
	f_tab = open(file_collection, 'r')
	df_collection = pd.read_csv(f_tab, index_col=0, header=0, delimiter="\t", compression="gzip") # index is snpID. # production_v2 - NEW March 2015.
	# NOT ACTIVE --> """ OBS: this function does *NOT* read in the collection with INDEX """
	#df_collection = pd.read_csv(f_tab, header=0, delimiter="\t", compression="gzip") # NO INDEX
	f_tab.close()
	elapsed_time = time.time() - start_time
	logger.info( "END: read CSV file PRIM into DataFrame in %s s (%s min)" % (elapsed_time, elapsed_time/60) )
	
	return df_collection


def drop_chr23_variants(df_collection):
	col_order = df_collection.columns.tolist()
	logger.info( "drop_chr23_variants() | col_order of df_collection\n[{}]".format(col_order) )

	logger.info( "Will drop chr23 from df_collection" )
	logger.info( "Number of observations in DataFrame %d" % len(df_collection) )
	### METHODS ###
	#sum(df_collection['snpID'].str[0:2] == "23") # sum --> 56907
	#sum(df_collection['snpID'].str.contains(r'^23:')) # sum --> 56907
	#sum(df_collection['snpID'].str.startswith('23:')) # sum --> 56907
	#bool_chr23 = pd.Series(df_collection.index).str.startswith('23:') # --> .str does not WORK ON INDEX
		# --> returns Series()
		# --> *DOES NOT WORK*: IndexingError: Unalignable boolean Series key provided

	### Working method ###
	df_collection['snpID_copy'] = df_collection.index # copy index to column
	bool_chr23 = df_collection['snpID_copy'].str.startswith('23:')
	## *drop column again* - otherwise it will also be in df_collection_red
	df_collection.drop('snpID_copy', axis=1, inplace=True)

	logger.info( "sum(bool_chr23) = {}".format(sum(bool_chr23)) )
	df_collection_red = df_collection[~bool_chr23] # invert a boolean: use "~" or "-"
	logger.info( "Done dropping chr23 rows. Number of observations in DataFrame now %d" % len(df_collection_red) )

	col_order = df_collection_red.columns.tolist()
	logger.info( "drop_chr23_variants() | col_order of df_collection_red\n[{}]".format(col_order) )


	return df_collection_red


def write_collection_file(df, no_compression):
	
	logger.info( "START: writing DataFrames to CSV..." )
	start_time = time.time()
	if no_compression:
		logger.info( "INFO: compressed option is OFF" )
		df.to_csv(file_collection, sep='\t', header=True, index=True, index_label='snpID')
	else:
		logger.info( "INFO: compressed option is ON" )
		# Open file handles
		f_tab = gzip.open(file_collection, 'wb')
		df.to_csv(f_tab, sep='\t', header=True, index=True, index_label='snpID')
		f_tab.close()
	elapsed_time = time.time() - start_time
	logger.info( "END: Done writing collection file: %.3f s (%.2f min)" % (elapsed_time, elapsed_time/60) )
	file_tab_size = os.path.getsize(file_collection)
	logger.info( "Size of concatenated tab file: %s bytes (%.1f MB)" % (file_tab_size, file_tab_size/(1024*1024.0)) )



### FUNCTION READS SPECIFIC COLUMNS. # CSV contains header!
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
arg_parser = argparse.ArgumentParser(description="FIX for adding chrX-altQC SNPs - July 2015")

arg_parser.add_argument("--output_dir", help="Path to write HDF5 and Collection file. DIR WILL BE CREATED IF IT DOES NOT EXISTS.", required=True)
arg_parser.add_argument("--super_population", help="IMPORTANT: This argument is used to LOCATE THE old collection file'", required=True)
arg_parser.add_argument("--distance_type", help="ld or kb. This argument is only used to construct sensable output files names", required=True)
arg_parser.add_argument("--distance_cutoff", help="r2, or kb distance.  This argument is only used to construct sensable output files names", required=True)

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

log_dir = "/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step99_tabs_recompile_add_chrX-SNPs_to_collection/{super_population}".format(super_population=super_population) #OBS VARIABLE
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


### INPUT DATA ###
### OBS: *SEMI HARD CODED PATHS*
file_collection_original = "/cvar/jhlab/snpsnap/data/step3/1KG_snpsnap_production_v2/{super_population}/{distance_type}{distance_cutoff}/{distance_type}{distance_cutoff}_collection.tab.gz".format(super_population=super_population, distance_type=distance_type, distance_cutoff=distance_cutoff)
file_collection_supplementary = "/cvar/jhlab/snpsnap/data/production_v2_chrX_standalone-altQC/step3/{super_population}/{distance_type}{distance_cutoff}/{distance_type}{distance_cutoff}_collection.tab.gz".format(super_population=super_population, distance_type=distance_type, distance_cutoff=distance_cutoff)
	

if not os.path.exists(file_collection):
	### Read collections
	df_collection_original = read_collection(file_collection_original)
	col_order_original = df_collection_original.columns.tolist() # COL ORDER | THIS COULD ALSO BE "df_collection_supplementary" since they have the same col_order.
		# ^^ We just need to make sure that we save one of the correct column orders
	df_collection_supplementary = read_collection(file_collection_supplementary)
	
	### Drop chr23
	df_collection = drop_chr23_variants(df_collection_original)
	
	### Combine data frames | append_supplementary_collection_to_original_collection
	df_collection_combined = df_collection.append(df_collection_supplementary) # OBS: the two dfs should HOPEFULLY have identical columns!
	col_order_combined = df_collection_combined.columns.tolist() # just curious...
	logger.info( "main | col_order of df_collection_combined - AFTER APPENDING\n[{}]".format(col_order_combined) )

	

	### *IMPORTANT* - reorder columns ####
	logger.info( 'Will rearrange column order of df_collection_combined now' )
	df_collection_combined = df_collection_combined.ix[:, col_order_original] # REARRANGE COLUMN ORDER - memory heavy?
	logger.info( 'Done rearranging...' )
	
	### Write collection
	write_collection_file(df_collection_combined, no_compression=args.no_compression)
else:	
	logger.warning( "Collection EXISTS: %s. Skipping writing new collection" % file_collection )

if not os.path.exists(file_hdf5_prim):
	df_prim = collection2dataframe(file_collection, no_compression=args.no_compression)
	dataframe_prim2hdf(file_hdf5_prim, df_prim)
else:
	logger.warning("HDF5 file PRIM EXISTS: %s. Skipping loading collection and skipping writing new HDF5 file" % file_hdf5_prim )



	

