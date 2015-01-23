#!/usr/bin/env python2.7

### On SNPsnap
#!/bin/env python
#source /opt/rh/python27/enable
	#---> gives Python 2.7.5 (where as Broad Dotkit python is Python 2.7.1)

import os
import sys
import collections
import argparse

import glob

import pandas as pd
import numpy as np
import gzip

import datetime
import time

#from queue import QueueJob,ShellUtils,ArgparseAdditionalUtils

import logging
import pplogger

#from memory_profiler import profile # USE THIS FOR MEMORY PROFILING - DOES NOT WORK ON VM SNPSNAP (MODULE NOT INSTALLED) 
#import profilehooks #  USE THIS FOR TIMING PROFILING
#import timeit
#import cProfile #or profile

import json

import subprocess # added 09/11/2014 - to be used for PLINK clumping

import pdb

########### Example calls ############
#./snpsnap_query.py --user_snps_file /Users/pascaltimshel/git/snpsnap/samples/sample_10randSNPs.list --output_dir /Users/pascaltimshel/snpsnap/data/query --distance_type ld --distance_cutoff 0.5 --N_sample_sets 10

# test data, 10 samples, match, no-sets
#./snpsnap_query.py --user_snps_file /Users/pascaltimshel/git/snpsnap/samples/sample_10randSNPs.list --output_dir /Users/pascaltimshel/snpsnap/data/query --distance_type ld --distance_cutoff 0.5 match --N_sample_sets 1000

# test data, 10 samples, annotate
#./snpsnap_query.py --user_snps_file /Users/pascaltimshel/git/snpsnap/samples/sample_10randSNPs.list --output_dir /Users/pascaltimshel/snpsnap/data/query --distance_type ld --distance_cutoff 0.5 annotate

###### BROAD - production_v1
#./snpsnap_query.py --user_snps_file /cvar/jhlab/snpsnap/snpsnap/samples/sample_10randSNPs.list --output_dir /cvar/jhlab/snpsnap/snpsnap/tmp_query --distance_type ld --distance_cutoff 0.5 match --N_sample_sets 1000 --ld_buddy_cutoff 0.5 --max_freq_deviation 5 --max_distance_deviation 20 --max_genes_count_deviation 20 --max_ld_buddy_count_deviation 20 --set_file
############################

# N_sample_sets
# ld_buddy_cutoff
# max_freq_deviation
# max_distance_deviation
# max_genes_count_deviation
# max_ld_buddy_count_deviation
# set_file

########### OBS ############
# Hardcoded paths: path_data, e.g. os.path.abspath("/Users/pascaltimshel/snpsnap/data/step3")
############################



# def locate_HDF5_data(path, prefix):
# 	#TODO: this function should be directed to a path containing ALL the HDF5 files
# 	# split on '_' and take first element. Match it against
# 	path_db = ""
# 	path_meta = ""
# 	files = glob.glob(path+"/"+prefix+"_*")
# 	if not len(files) == 2:
# 		print "Found more than two files."
# 		print "Exiting..."
# 		sys.exit(1)
# 	if "db" in files[0]: pass

#/cvar/jhlab/snpsnap/data/step3/1KG_snpsnap_production_v1/ld0.1_db.h5.

def locate_db_file(path, prefix):
	#TODO fix this. Make checks
	file_db = "{path}/{type}/{type}_db.{ext}".format(path=path, type=prefix, ext='h5')
	# META FILE DISAPLED TEMPORARY
	#file_meta = "{path}/{type}_meta.{ext}".format(path=path, type=prefix, ext='h5')
	#if not ( os.path.exists(file_db) and os.path.exists(file_meta) ): # both file must exists
	if not os.path.exists(file_db): # TODO- FIX THIS LATER
		raise Exception( "Could not find file_db file: %s" % file_db )
	#return (file_db, file_meta)
	return file_db

def locate_collection_file(path, prefix):
	#file_collection = "{path}/{type}_collection.{ext}".format(path=path, type=prefix, ext='tab.gz') # compressed file
	file_collection = "{path}/{type}/{type}_collection.{ext}".format(path=path, type=prefix, ext='tab')
	if not os.path.exists(file_collection): # TODO- FIX THIS LATER
		raise Exception( "Could not find collection file: %s" % file_collection )
	return file_collection


# Function to read userdefined list of SNPs
def read_user_snps(user_snps_file):
	"""
	Function to read user SNPs. 
	Function reports duplicats and empty lines in the input SNPlist.
	Returns a LIST of SNPs """
	#TODO error check:
	# check for match to X:YYYYYY partern: '\d{1-2}:\d+'
	# check for duplicates in list ---> most important
	#user_snps = {}
	user_snps = []
	duplicates = {}
	infile = open(user_snps_file,'r')
	lines = infile.readlines()
	infile.close()
	for line in lines:
		words = line.strip()
		if not words: # string is empty
			logger.warning( "Found empty line in user_snps_file %s" % user_snps_file )
			continue
		if not words in user_snps:
			#user_snps[words] = 1
			user_snps.append(words)
		else:
			logger.warning( "user input file contains duplicates" )
			if not words in duplicates: # first time we notice a duplicate ==> two entries seen
				duplicates[words] = 2
			else:
				duplicates[words] += 1
	if duplicates: # dict is non-empty
		logger.info( "*** List of duplicate SNPs" )
		for (k,v) in duplicates.items():
			logger.info( "%s\t%s" % (k,v) )
	logger.info( "Read %d unique user SNPs" % len(user_snps) )
	return user_snps


### OLD FUNCTION FOR 
# #@profilehooks.profile
# @memory_profiler.profile
# def lookup_user_snps(file_db, user_snps):
# 	start_time = time.time()

# 	store = pd.HDFStore(file_db, 'r')
# 	quoted_list = (', '.join("'" + item + "'" for item in user_snps.keys() ))
# 	query = "index=[%s]" % quoted_list
# 	user_snps_df = store.select('dummy', query)
# 	store.close()

# 	elapsed_time = time.time() - start_time
# 	print "DONE: lookup_user_snps %s s (%s min)" % (elapsed_time, elapsed_time/60)
# 	return user_snps_df

#@profile
def lookup_user_snps_iter(file_db, user_snps):
	""" This function will query the user_snps (type list) against the data base index 
	NOTE that the resultant concatenated data frame (user_snps_df) will have the SAME column names (and index name = 'snpID') as the HDF5 file.
	"""
	logger.info( "START: lookup_user_snps_iter" )
	start_time = time.time()
	store = pd.HDFStore(file_db, 'r')
	list_of_df = []
	#user_snps_df = pd.DataFrame() # APPEND VERSION - WORKS, but NO control of column order. Consider: pd.DataFrame(columns=colnames)
	for i, item in enumerate(user_snps, start=1):
		logger.info( "#%s/#%s | Look-up SNP: %s" % (i, len(user_snps), item) )
		df = store.select('dummy', "index=['%s']" % item) # Remember to quote the string!
		## ^^ df will be an empty DataFrame if there is no SNP with the quired index (NOTE that this is not the same as indexing in a pandas data frame: here a KeyError will be thrown if the index does not exists)
		## ^^ nothing happens when appending/concatenating empty DataFrames
		
		## If no SNP found from chr:pos, then look for rsID.
		if len(df) == 0:
			df = store.select('dummy', "rsID=['%s']" % item) # Remember to quote the string!. MAKE SURE THAT rsID is the correct column name.
			# ^this data frame has the column names (and index name = 'snpID') as the HDF5 file.

			if len(df) == 1: # make sure we only get one match
				logger.info( "#%s/#%s | Mapped rsID to chr:posID | %s --> %s" % (i, len(user_snps), item, df.index.values[0]) )
			elif len(df > 1):
				logger.critical( "Found multiple entries in db when doing look-up based on rsID '%s'" % item )
				logger.critical( "List of matching SNPs: %s" % ";".join(df.index.values) )
				logger.critical( "Will not use any of these matching. Considering SNP as SNP_not_found_in_data_base" )
				df = pd.DataFrame() # setting the data frame as empty. This still works when concatenating the dfs. type() --> pandas.core.frame.DataFrame.

		#TODO: check length of df. MUST BE EXACTLY ONE!!! ****
		#TODO: immediately write out snps/items with wrong len(df)?
		list_of_df.append(df)
		#user_snps_df = user_snps_df.append(df) # APPEND VERSION - WORKS.
	store.close()
	user_snps_df = pd.concat(list_of_df)
		# ---> pd.concat KEEPS the order of the list of df parsed. That is, SNPs in the df will be in the same order as the the user submitted them.
	
	## Making sure not to have duplicates. Duplicates could arise if the user inputs the different indentifers (chr:pos and rsID) mapping to the same SNP.
	#.duplicated() [without any arguments] check for ROWS that are duplicated.
	#.duplicated() IMPORTANT: It returns a Series denoting duplicate rows. The DEFAULT behavior is marking the FIRST observed row as NON duplicate and the FOLLOWING rows as duplicate. That is, there will still be one "copy" left of the row.
	#.duplicated() only consider column values when looking for duplicates. That is, the index value is not considered.
	if user_snps_df.duplicated().any(): # user_snps_df.duplicated().any() --> gives a bool value ('True' or 'False')
		series_duplicated_values = user_snps_df.duplicated() # user_snps_df.duplicated() --> Series object with boolean values.
		logger.warning( "Found duplicated entries in user_snps_df. Duplicates will be removed (one copy will be retained). Printing snpID and rsID for rows marked as duplicate:" )
		logger.warning( user_snps_df.ix[series_duplicated_values, ["rsID"]] )
		user_snps_df.drop(series_duplicated_values, axis=0, inplace=True)

		# ALTERNATIVE SOLUTION (not tested, but useful) - this checks for duplicated INDEX. See also tabs_compile.py [idx_bool = pd.Series(df.index).duplicated().values]
		#user_snps_df["index_tmp_col"] = user_snps_df.index #--> creating a column of the index (chr:pos ID)
		#user_snps_df.drop_duplicates(subset='index_tmp_col', inplace=True) #--> Return DataFrame with duplicate rows removed. TIP: you can get the list of duplicates ROWS by df.duplicated()
		#del user_snps_df["index_tmp_col"] #--> remove column again. Notice that the index of the df does not change.
		

	
	# NOTE: all duplicates for chr:pos have been removed in the tabs_compile.py and the list can be found in the file "ld0.X_duplicates.tab"
	# NOTE: 09/10/2014; Pascal tested the HDF5 file for duplicates of rsIDs. There are NO duplicate rsIDs!

	elapsed_time = time.time() - start_time
	logger.info( "END: lookup_user_snps_iter in %s s (%s min)" % (elapsed_time, elapsed_time/60) )
	
	return user_snps_df



def process_input_snps(path_output, user_snps, user_snps_df):
	""" 
	1) Function idenfifies SNPs that where NOT found in the database. 
	2) Function EXCLUDES HLA_SNPs
	3) Function WRITES FILE input_snps_excluded.txt (either user_snps_not_in_db or user_snps_mapping_to_HLA)
	4) Function WRITES FILE input_snps_identifer_mapping.txt

	REMARKS: 
	- user_snps_df is a Data Frame containing ONLY user SNPs that exists in SNPsnap DB
	- user_snps is a LIST of the input SNPs. You need to be careful what operations you perform on the user_snps - prepare for the most crazy input. Thus use 'try except' when doing operations on them
	IMPROVEMENT:
	- the list of SNPs not found in db could be generated already in "lookup_user_snps_iter()": just check the lenght of the user_snps_df from store.select() has length 0.
	"""
	file_user_snps_excluded = path_output+"/input_snps_excluded.txt"
	file_user_snps_mapping = path_output+"/input_snps_identifer_mapping.txt"

	logger.info( "START: doing process_input_snps, that is SNPs that will be excluded" )
	start_time = time.time()

	snps_excluded = {} # dict will contain all user_snps not used further in SNPsnap (user_snps_not_in_db and snps_in_HLA)
	snps_in_HLA = [] # this list will be used to drop input SNPs from the DataFrame (user_snps_df) mapping to HLA
	n_snps_not_in_db = 0 # counter for snps not found in data base - USED IN report_news 
	for snp in user_snps: # OBS: looping over user_snps [LIST].
		#if not (user_snps_df.index == snp).any():
		if ( not (user_snps_df.index == snp).any() ) and ( not (user_snps_df.ix[:,'rsID'] == snp).any() ): # [(not A) AND (not B)] <=> [not (A OR B)]. De Morgan's laws: when changing sign outside parenthesis you must change logic inside parenthesis.
			snps_excluded[snp] = "SNP_not_found_in_data_base"
			n_snps_not_in_db += 1
	logger.warning( "{} SNPs not found in data base:\n{}".format( n_snps_not_in_db, "\n".join(snps_excluded.keys()) ) ) # OBS: more SNPs may be added to snps_excluded in the exclude_HLA_SNPs step
	logger.info( "Found %d out of the %d user input SNPs in data base" % (len(user_snps_df.index), len(user_snps)) )

	if exclude_HLA_SNPs: # global boolean variable, True or False
		for snp in user_snps_df.index: # OBS: looping over user_snps_df [DATA FRAME]
			# ^^^WE ARE NOW SURE THAT THE SNP EXISTS IN OUR DATA-BASE. This is important because we now know what operations (e.g split) we can perform on them
			# type(snp) --> <type 'str'>
			split_list = snp.split(":")
			(snp_chr, snp_position) = ( int(split_list[0]), int(split_list[1]) ) # OBS: remember to convert to int!
			# ^^ if the user input is e.g. 'Q&*)@^)@*$&Y_' or 'blabla' a ValueError will be raised if trying to convert to int
			if snp_chr == 6: # exclude SNPs in the HLA region 6:25000000-6:35000000
				if 25000000 <= snp_position <= 35000000:
					snps_excluded[snp] = "SNP_in_HLA_region"
					snps_in_HLA.append(snp) # appending to list for exclusion
		logger.warning( "{} SNPs mapping to HLA region:\n{}".format( len(snps_in_HLA), "\n".join(snps_in_HLA) ) ) # OBS: more SNPs may be added to snps_excluded in the exclude_HLA_SNPs step
		logger.warning( "Excluding the SNPs mapping to HLA region...")
		user_snps_df.drop(snps_in_HLA, axis=0, inplace=True) # inplace dropping index mapping to HLA

	if snps_excluded: # if non-empty
		logger.warning( "{} SNPs in total not found or excluded because they map to HLA region".format(len(snps_excluded)) )
		### WRITING SNPs not found to FILE ###
		#if not os.path.exists(file_user_snps_excluded): # This is needed (or better practice) to not (over)write the file when the web service calls match, annotate and clump. However, it could cause problems not overwriting if called from command line
		# ^ I put in the above line because I was UNSURE about what happens if three processes tries to open and write to the same file.
		with open(file_user_snps_excluded, 'w') as f:
			# THIS COULD LEAD TO AN ERROR IF SNP-keys are not uniqe! TODO: fix this to operator.itemgetter() approach
			for snp in sorted(snps_excluded, key=snps_excluded.get): # sort be the dict value (here snps_excluded[snp]='reason')
				f.write(snp+"\t"+snps_excluded[snp]+"\n")

	### SOME USEFUL CODE TO INSPECT THE UNIQUENESS OF USER_SNPs ###
	# print "*** Warning: Number of unique snpIDs (index) found: %d" % len(np.unique(user_snps_df.index.values))
	# bool_duplicates = pd.Series(user_snps_df.index).duplicated().values # returns true for duplicates
	# user_snps_df_duplicate = user_snps_df.ix[bool_duplicates]
	# print user_snps_df_duplicate
	# idx_duplicate = user_snps_df_duplicate.index
	# print "Pandas data frame with index of duplicate:"
	# print user_snps_df.ix[idx_duplicate]

	### WRITING OUT MAPPING FILE
	#if not os.path.exists(file_user_snps_mapping): #<-- you WANT to overwrite the file if running the tool from commandline
	user_snps_df.to_csv(file_user_snps_mapping, sep='\t', index=True, columns=['rsID'], header=True, mode='w') #index_label='snpID' NOT needed - it follows from the HDF5 file


	elapsed_time = time.time() - start_time
	logger.info( "END: process_input_snps in %s s (%s min)" % (elapsed_time, elapsed_time/60) )

	if report_obj.enabled:
		report_news = 	{	"user_snps_unique_input":len(user_snps),
							"user_snps_working_set":len(user_snps_df),
							"user_snps_excluded_in_total":len(snps_excluded),
							"user_snps_not_in_db":n_snps_not_in_db,
							"user_snps_mapping_to_HLA":len(snps_in_HLA)
							}
		report_obj.report['input'].update(report_news)

	### RETURNING DataFrame
	#Note: if exclude_HLA_SNPs is enabled, then the DataFrame (user_snps_df) will be a modified version of the one parsed to this function
	return user_snps_df 

# NOT IN USE SINCE 07/03/2014 - MAY BE OUTCOMMENTED/DELETED
# def write_user_snps_stats(path_output, user_snps_df):
# 	user_snps_stats_file = path_output+"/input_snps.tab"
# 	user_snps_df.to_csv(user_snps_stats_file, sep='\t', header=True, index=True,  mode='w')

#@profile
def read_collection(file_collection):
	"""Function that reads tab seperated gzip collection file"""

	# OBS: 07/03/2014: UNtested code added in tabs_compile.py for adding rsID as the second column (after snpID)
	# Columns in COLLECTION:
	#1=snpID
	#2=freq_bin
	#3=gene_count
	#4=dist_nearest_gene_snpsnap
	#5=dist_nearest_gene
	#6=dist_nearest_gene_located_within
	#7=loci_upstream
	#8=loci_downstream
	#9=ID_nearest_gene_snpsnap
	#10=ID_nearest_gene
	#11=ID_nearest_gene_located_within
	#12=ID_genes_in_matched_locus
	#13=friends_ld01
	#....
	#21=friends_ld00

	# NUMBER OF COLUMNS = 21 - this is validated 07/02/2014


	logger.info( "START: reading CSV file PRIM..." )
	start_time = time.time()
	#f_tab = gzip.open(file_collection, 'rb') #Before June 2014 - compressed file
	#df_collection = pd.read_csv(f_tab, index_col=0, header=0, delim_whitespace=True) # index is snpID. #Before June 2014
	f_tab = open(file_collection, 'r')
	df_collection = pd.read_csv(f_tab, index_col=0, header=0, delimiter="\t") # index is snpID. # production_v1
	f_tab.close()
	elapsed_time = time.time() - start_time
	logger.info( "END: read CSV file PRIM into DataFrame in %s s (%s min)" % (elapsed_time, elapsed_time/60) )
	return df_collection

def write_user_snps_annotation(path_output, df, df_collection):
	status_obj.update_status('annotate', 'running')

	user_snps_annotated_file = path_output+"/input_snps_annotated.txt"
	df_user_snp_found_index = df.index # index of (found) user snps
	df_user_snps_annotated = df_collection.ix[df_user_snp_found_index]
	df_user_snps_annotated.to_csv(user_snps_annotated_file, sep='\t', header=True, index=True,  mode='w') 
	status_obj.update_status('annotate', 'complete')


def few_matches_score(x, lim, scale):
	score = 'unknow'
	# scale = []
	# if scale_order == 'low_is_bad':
	# 	scale = ['very bad', 'bad', 'medium', 'good', 'very good']
	# elif scale_order == 'low_is_good':
	# 	scale = ['very good', 'good', 'medium', 'bad', 'very bad']
	# else:
	# 	score = '[error: bad scale]'
	# 	return 

	if len(scale)+1 != len(lim):
		score = '[error: lim parsed to few_matches_score does not match internal scale]'
		return score

	if lim[0]<=x<=lim[1]:
		score = scale[0]
	elif lim[1]<=x<=lim[2]:
		score = scale[1]
	elif lim[2]<=x<=lim[3]:
		score = scale[2]
	elif lim[3]<=x<=lim[4]:
		score = scale[3]
	elif lim[4]<=x<=lim[5]:
		score = scale[4]
	else:
		score = '[error: wrong limits]'
	return score

def few_matches_report(path_output, df_snps_few_matches, N_sample_sets, N_snps):
	########## Write few_matches - ONLY IF THERE ARE FEW MATCHES ##############
	if len(df_snps_few_matches) != 0:
		user_snps_few_matches_file = path_output+"/input_snps_insufficient_matches.txt"
		df_snps_few_matches.to_csv(user_snps_few_matches_file, sep='\t', index=True, header=True, index_label='snpID', mode='w') 
	############################################
	
	insufficient_matches_pct = ( len(df_snps_few_matches)/float(N_snps) )*100

	if len(df_snps_few_matches) == 0: # NO few_matches found
		match_size_median = N_sample_sets
	else:
		match_size_median = df_snps_few_matches.ix[:,'n_matches'].median()

	match_size_median_pct = ( match_size_median/float(N_sample_sets) )*100
	
	insufficient_scale = ['very good', 'good', 'ok', 'poor', 'very poor']
	match_size_scale = ['very poor', 'poor', 'ok', 'good', 'very good']
	# convert to strings
	insufficient_scale_str = (', '.join("'" + item + "'" for item in insufficient_scale))
	match_size_scale_str = (', '.join("'" + item + "'" for item in match_size_scale))
	# About the use of this few_matches_score:
	# 1) check that the criteria for scale and lim lengths is ok
	# 2) function does ONLY support 5 scores ATM
	# 3) IMPORTANT: limits may have to be reversed for it to work. See the function code..



	### production_v1 | from GWAS catalog, N=10000.freq=5.gene_density=50.gene_dist=50.ld_buddy_count=50
	# .id					q_insuf	q_size	quantile_id
	# 10000.5.50.50.50	16.97	27.77	20%
	# 10000.5.50.50.50	22.44	38.40	40%
	# 10000.5.50.50.50	26.35	45.30	60%
	# 10000.5.50.50.50	31.03	61.19	80%
	# 10000.5.50.50.50	41.67	72.02	100%

	#insufficient_quantile = [0,1,5,10,25,100] # self selected quantiles
	#match_size_quantile = [100,75,50,30,15,0][::-1] # self selected quantiles
	insufficient_quantile = [0, 16.97, 22.44, 26.35, 31.03, 100] # production_v1 | from GWAS catalog, N=10000.freq=5.gene_density=50.gene_dist=50.ld_buddy_count=50
	match_size_quantile = [0, 27.77, 38.40, 45.30, 61.19, 100] # production_v1 | from GWAS catalog, N=10000.freq=5.gene_density=50.gene_dist=50.ld_buddy_count=50

	insufficient_rating = few_matches_score(insufficient_matches_pct, insufficient_quantile, insufficient_scale) #low_is_good
	match_size_rating = few_matches_score(match_size_median_pct, match_size_quantile, match_size_scale) #low_is_bad

	#TODO: print scale_order (pass as argument to function)
	# print_str_insufficient_rating = "Rating 'number of few matches' = '{rating:s}' ({pct:.4g}%, {count:d} few_matches out of {total:d} valid input SNPs)".format(rating=insufficient_rating, 
	# 																											pct=insufficient_matches_pct, 
	# 																											count=len(df_snps_few_matches),
	# 																											total=N_snps)
	# print_str_score_match_size = "Rating 'over sampling' = '{rating:s}' ({pct:.4g}%, median SNPs to sample from in few_matches is {median:.6g} compared to {total:d} N_sample_sets)".format(rating=match_size_rating, 
	# 																											pct=match_size_median_pct, 
	# 																											median=match_size_median,
	# 																											total=N_sample_sets)
	
	insufficient_matches=len(df_snps_few_matches)
	#tmp1 = "# Rating 'number of few matches' = '{rating:s}' with scale [{scale:s}]".format(rating=insufficient_rating, scale=(', '.join("'" + item + "'" for item in insufficient_scale)) )
	tmp1 = "# Rating 'insufficient SNP matches' = '{rating:s}' with scale [{scale:s}]".format(rating=insufficient_rating, scale=insufficient_scale_str )
	tmp2 = "# Percent 'insufficient SNP matches' = {pct:.4g}% (low is good; {count:d} 'insufficient SNP matches' out of {total:d} valid input SNPs)".format(pct=insufficient_matches_pct, count=insufficient_matches, total=N_snps)
	write_str_insufficient_rating = '\n'.join([tmp1, tmp2])

	#tmp1 = "# Rating 'over sampling' = '{rating:s}' with scale [{scale:s}]".format(rating=match_size_rating, scale=(', '.join("'" + item + "'" for item in match_size_scale)) )
	#Rating 'relative sample size'
	# 'effective set/sample size'
	# insufficient match size
	# effective matches
	# bootstrapping
	# resample
	# match size
	tmp1 = "# Rating 'match size' = '{rating:s}' for SNPs in 'insufficient SNP matches' with scale [{scale:s}]".format(rating=match_size_rating, scale=match_size_scale_str )
	tmp2 = "# Relative 'match size' = {pct:.4g}% (high is good; median number of SNPs to sample from in 'insufficient SNP matches' is {median:.6g} compared to {total:d} requested sample sets)".format(pct=match_size_median_pct, median=match_size_median, total=N_sample_sets)
	write_str_score_match_size = '\n'.join([tmp1, tmp2])

	tmp1 = "# {0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}".format("insufficient_rating", "pct_insufficient", "insufficient_matches", "N_snps", 
															"rating_size", "pct_size", "median_size", "N_sample_sets")
	#tmp1 = "# rating_few_matches\tpct_few_matches\tN_few_matches\tN_snps\trating_over_sampling\tpct_over_sampling\tmedian_sample_size\tN_sample_sets"
	tmp2 = "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}".format(insufficient_rating, insufficient_matches_pct, insufficient_matches, N_snps,
															match_size_rating, match_size_median_pct, match_size_median, N_sample_sets)
	write_str_score_table = '\n'.join([tmp1, tmp2])
	logger.info( "################# Score ###############" )
	logger.info( write_str_insufficient_rating )
	logger.info( write_str_score_match_size )
	logger.info( write_str_score_table )
	logger.info( "######################################" )

	#### UNCOMMENTED 06/12/2014 - Pascal. Reason: 
	#user_snps_few_matches_report = path_output+"/snps_report.txt" # 06/12/2014: NO LONGER NEEDED. We do not write out file
	# with open(user_snps_few_matches_report, 'w') as f:
	# 	f.write(write_str_insufficient_rating+'\n')
	# 	f.write(write_str_score_match_size+'\n')
	# 	f.write(write_str_score_table+'\n')
	
	####### Creating report dict of dicts #####
	if report_obj.enabled: 
		#insufficient_scale_str = (', '.join("'" + item + "'" for item in insufficient_scale))
		#match_size_scale_str = (', '.join("'" + item + "'" for item in match_size_scale))
		report_news = 		{	"insufficient_rating":insufficient_rating,
								"insufficient_matches_pct":insufficient_matches_pct, 
								"insufficient_matches":insufficient_matches,
								"match_size_rating":match_size_rating,
								"match_size_median_pct":match_size_median_pct,
								"match_size_median":match_size_median
							}
		report_obj.report['snpsnap_score'].update(report_news)
		
					#'insufficient_scale_str':insufficient_scale_str,
					#'match_size_scale_str':match_size_scale_str



def calculate_input_to_matched_ratio(file_db, df_input, matched_snpID_array, cols2calc):
	status_obj.update_status('bias', 'running')

	# Read SNPsnap data base
	logger.info( "START: reading HDF5 file into DataFrame..." )
	start_time = time.time()
	status_obj.update_pct('bias', float(20)) # ###### STATUSBAR #########
	store = pd.HDFStore(file_db, 'r')
	snpsnap_db_df = store.select('dummy') # read entire HDF5 into data frame
	store.close()
	elapsed_time = time.time() - start_time
	logger.info( "END: read HDF5 file into DataFrame in %s s (%s min)" % (elapsed_time, elapsed_time/60) )

	logger.info( "START: Indexing and creating df_input and df_matched" )
	start_time = time.time()
	### Subsetting columns
	status_obj.update_pct('bias', float(40)) # ###### STATUSBAR #########
	snpsnap_db_df = snpsnap_db_df.ix[:,cols2calc] # taking all rows and specific columns
	df_input = df_input.ix[:,cols2calc]

	### Contructing df_matched by indexing in snpsnap_db_df
	df_matched = snpsnap_db_df.ix[matched_snpID_array]
	status_obj.update_pct('bias', float(60)) # ###### STATUSBAR #########
	elapsed_time = time.time() - start_time
	logger.info( "END: Indexing and creating df_input and df_matched in %s s (%s min)" % (elapsed_time, elapsed_time/60) )

	### Calculating mean
	logger.info( "START: calculating mean and ratio..." )
	start_time = time.time()
	status_obj.update_pct('bias', float(80)) # ###### STATUSBAR #########
	input_mean = df_input.mean(axis=0) # <class 'pandas.core.series.Series'>
	matched_mean = df_matched.mean(axis=0) #<class 'pandas.core.series.Series'>

	### Taking ratio and multiply by 100 to get percent.
	ratio = input_mean/matched_mean*100 # see also: Series.divide(other, level=None, fill_value=None, axis=0)
	### ^^ Note: I tested the senario that matched_mean contains elements with the value zero. Not exceptions are raised, but elements get value 'inf'
	### ratio is of class <class 'pandas.core.series.Series'>
	elapsed_time = time.time() - start_time
	logger.info( "END: calculating mean and ratio in %s s (%s min)" % (elapsed_time, elapsed_time/60) )


	### Convert SERIES to a DICTINARY, like: {'dist_nearest_gene_snpsnap': 162.59887515819352, 'freq_bin': 123.39080459770115,...}
	input_mean_dict = input_mean.to_dict() # INPUT
	for key in input_mean_dict.keys():
		input_mean_dict['mean_input_'+key] = input_mean_dict.pop(key)
	matched_mean_dict = matched_mean.to_dict() # MATCHED
	for key in matched_mean_dict.keys():
		matched_mean_dict['mean_matched_'+key] = matched_mean_dict.pop(key)
	ratio_dict = ratio.to_dict() # RATIO
	for key in ratio_dict.keys():
		ratio_dict['ratio_'+key] = ratio_dict.pop(key) ### renaming keys by adding ratio_ to the beginning of the key:
	## The names in the dict will be someting like this:
	#'ratio_freq_bin'
	#'ratio_gene_count'
	#'ratio_dist_nearest_gene_snpsnap'
	#'ratio_friends_ld05' # <--- OBS this key name is variable!

	## Combining the dicts
	report_news = dict( input_mean_dict.items() + matched_mean_dict.items() + ratio_dict.items() ) # OBS: if there are any keys exitsting in more than one dict, the value of the key will be overwritten by the latest dict's value

	logger.info("####### RATIO REPORT #########")
	for key in sorted(report_news.keys()):
		logger.info( "%s : %s" % (key, report_news[key]) )
	logger.info("#############################")

	####### Creating report dict of dicts #####
	if report_obj.enabled:
		## NOTE: report_news has already been contructed!
		report_obj.report['mean_input_to_match_ratio'].update(report_news) # CONSIDER: making a new 'category' containing the ratio values

	status_obj.update_pct('bias', float(100)) # ###### STATUSBAR #########
	report_obj.write_json_report() # WRITE OUT REPORT so "report_input_to_matched_ratio_html.py" can read it.
	status_obj.update_status('bias', 'complete')


#@profile
def query_similar_snps(file_db, path_output, df, N_sample_sets, ld_buddy_cutoff, exclude_input_SNPs, max_freq_deviation, max_distance_deviation, max_genes_count_deviation, max_ld_buddy_count_deviation):
	## NOTE: df is "user_snps_df"

	status_obj.update_status('match', 'running')
	

	np.random.seed(1) # Always set seed to be able to reproduce result. np.choice is dependent on seed()
	n_attempts = 5 # use this variable to adjust balance between speed (n_attempts low) and getting best matches (n_attempts high)
	
	df_snps_few_matches = None

	user_snps_matrix_file = path_output+"/matched_snps.txt"
	if os.path.exists(user_snps_matrix_file): # removing any existing file. REASON: we are appending to matrix_file
		os.remove(user_snps_matrix_file)
	f_matrix_out = open(user_snps_matrix_file,'a')
	f_matrix_out.write('Input_SNP\t%s\n' % "\t".join(['Set_'+str(i) for i in xrange(1,N_sample_sets+1)])) #IMPORTANT: writing out header!
	
	store = pd.HDFStore(file_db, 'r')
	
	####################### *OBS* GLOBAL internal parameter | DID NOT IMPROVE PERFORMACE, but tested and works ################
	if data_frame_query:
		snpsnap_db_df = store.select('dummy') # read entire HDF5 into data frame
	##################################################################################


	if calculate_mean_input_to_match_ratio:
		all_matched_snpID = np.array([]) # empty array. This array will be appended to for each FINAL (after sampling with-replacement etc) set of matched SNPs


	idx_input_snps = range(len(df.index)) # REMEMBER: both python and pandas are zero-based
	N_snps = len(idx_input_snps)
	for i in idx_input_snps:
		query_snpID = df.index[i]
		q_freq_bin = df.ix[i,'freq_bin']
		q_gene_count = df.ix[i,'gene_count']
		q_dist = df.ix[i,'dist_nearest_gene_snpsnap']
		colname_ld_buddy_count = 'friends_ld'+str(ld_buddy_cutoff).replace(".", "") # e.g. friends_ld02. "ld_buddy_cutoff" will be a FLOAT like "0.2"
		q_ld_buddy_count = df.ix[i,colname_ld_buddy_count] #NEW

		### Setting delta space ####
		delta_freq = np.rint(np.linspace(0,max_freq_deviation, n_attempts)).astype(int) # rounds to nearest integer and convert to int
		# OBS: delta_gene_count and delta_dist are in the range of [-1;1]
		delta_gene_count = np.linspace(0,max_genes_count_deviation, n_attempts)/float(100)
		if max_distance_deviation < 1:
			logger.error( "max_distance_deviation set to %s. Lowest possible max_distance_deviation is 1." % max_distance_deviation )
			max_distance_deviation = 1
		delta_dist = np.linspace(1,max_distance_deviation, n_attempts)/float(100) # OBS distance deviation starts at 1 %
		delta_ld_buddy_count = np.linspace(0,max_ld_buddy_count_deviation, n_attempts)/float(100) # NEW

		### Calculating low/high boundaries
		freq_low = np.repeat(q_freq_bin, n_attempts) - delta_freq # ABSOLUTE DEVIATION
		freq_high = np.repeat(q_freq_bin, n_attempts) + delta_freq # ABSOLUTE DEVIATION
		gene_count_low = np.rint(np.repeat(q_gene_count, n_attempts)*(1-delta_gene_count))
		gene_count_high = np.rint(np.repeat(q_gene_count, n_attempts)*(1+delta_gene_count))
		dist_low = np.rint(np.repeat(q_dist, n_attempts)*(1-delta_dist))
		dist_high = np.rint(np.repeat(q_dist, n_attempts)*(1+delta_dist))
		ld_buddy_count_low = np.rint(np.repeat(q_ld_buddy_count, n_attempts)*(1-delta_ld_buddy_count))
		ld_buddy_count_high = np.rint(np.repeat(q_ld_buddy_count, n_attempts)*(1+delta_ld_buddy_count))

		logger.info( "SNP #%d/%d: ID starting query in data base" % (i+1, N_snps) )
		match_ID_old = None # placeholder for a Numpy array
		match_ID = None # placeholder for a Numpy array
		for attempt in xrange(n_attempts):
			start_time = time.time()
			if data_frame_query:
				#logger.info("query df")
				query_freq_bin = '(%s <= freq_bin <= %s)' % (freq_low[attempt], freq_high[attempt])
				query_gene_count = '(%s <= gene_count <= %s)' % (gene_count_low[attempt], gene_count_high[attempt])
				query_dist = '(%s <= dist_nearest_gene_snpsnap  <= %s)' % (dist_low[attempt], dist_high[attempt])
				query_ld_buddy_count = '({min} <= {col} <= {max})'.format(col=colname_ld_buddy_count, min=ld_buddy_count_low[attempt], max=ld_buddy_count_high[attempt])

				query = "%s & %s & %s & %s" % (query_freq_bin, query_gene_count, query_dist, query_ld_buddy_count)
				match_ID = snpsnap_db_df.query(query)
			else: # THIS IS USED
				#logger.info("query store")
				query_freq_bin = '(freq_bin >= %s & freq_bin <= %s)' % (freq_low[attempt], freq_high[attempt])
				query_gene_count = '(gene_count >= %s & gene_count <= %s)' % (gene_count_low[attempt], gene_count_high[attempt])
				query_dist = '(dist_nearest_gene_snpsnap  >= %s & dist_nearest_gene_snpsnap  <= %s)' % (dist_low[attempt], dist_high[attempt])
				query_ld_buddy_count = '({col} >= {min} & {col} <= {max})'.format(col=colname_ld_buddy_count, min=ld_buddy_count_low[attempt], max=ld_buddy_count_high[attempt])

				query = "%s & %s & %s & %s" % (query_freq_bin, query_gene_count, query_dist, query_ld_buddy_count)
				#match_ID = store.select('dummy', query, columns=[]).index.values # --> only index # USED BEFORE JUNE 30
				match_ID = store.select('dummy', query, columns=[]) # return no columns --> only index
				#match_ID = store.select('dummy', query, columns=['freq_bin', 'gene_count', 'dist_nearest_gene_snpsnap', colname_ld_buddy_count]) # return specific columns



			## Permuting/shuffling the rows
			#df.reindex(index=np.random.permutation(df.index)) # A new object is produced unless the new index is equivalent to the current one and copy=False
			elapsed_time = time.time() - start_time
			logger.info( "attempt #%d/%d| SNP %s| Selecting data from store in %s s (%s min)" % (attempt+1, n_attempts, query_snpID, elapsed_time, elapsed_time/60) )


			if len(match_ID) < N_sample_sets:
				match_ID_old = match_ID
			else: #we have enough matches
				match_ID_old = np.array([]) # empty array. This line ensures that len(match_ID_old) is always valid
				break

		logger.info( "SNP #%d/%d: ID {%s}: found %d hits" % (i+1, N_snps, query_snpID, len(match_ID)) )
		
		# ###################################### STATUSBAR ######################################
		status_obj.update_pct('match', (i+1)/float(N_snps)*100)
		# #######################################################################################

		### IMPORTANT: converting DataFrame to Index
		match_ID = match_ID.index # IMPORTANT: converting data frame to index. We use the pandas Index.intersection method. (it could also be used in a DataFrame)
		## ^^ type(match_ID) ---> <class 'pandas.core.index.Index'>

		#start_time = time.time() # START: timing how long the intersection step takes... # FOR DEBUGGING
		if exclude_input_SNPs:
			set_intersect = match_ID.intersection(df.index) # returns Index. finding intersection between indexes in matched SNPs and user SNPs
			list_of_intersecting_SNPs = set_intersect.tolist()
			if len(list_of_intersecting_SNPs) > 1: # we only want to see the logger warning if more than the SNP itself is in the intersection
				logger.warning( "Found %s SNPs in intersection between matched SNPs and input SNPs." % len(list_of_intersecting_SNPs) )
				logger.warning( "List of intersection set: [%s]" % " ".join(list_of_intersecting_SNPs) )
				logger.warning( "SNPs will be excluded" )
			#logger.warning( "Length of match_ID BEFORE dropping: %s" % len(match_ID) ) # FOR DEBUGGING
			match_ID = match_ID.drop(set_intersect) # returns nex Index with passed list of labels deleted. (no inplace argument). takes array-like argument
													# **OBS: all indexes you wish to drop must exist in match_ID. If not, the following exception will be thrown: ValueError: labels ['9:5453460'....] not contained in axis
			#logger.warning( "Length of match_ID AFTER dropping: %s" % len(match_ID) ) # FOR DEBUGGING
			#elapsed_time = time.time() - start_time # FOR DEBUGGING
			#logger.info( "Run time of exclude_input_SNPs step: %s s" % elapsed_time ) # FOR DEBUGGING


		### PERFORMACE test of 'exclude_HLA_SNPs'
		## - WITH SPLIT + IF --> 100 loops, best of 3: 3.68 ms per loop  
		## - NO SPLIT --> 100 loops, best of 3: 2.15 ms per loop
		## Ratio: 3.68/2.15 = 1.71 times SLOWER using the exclude_HLA_SNPs option
		if exclude_HLA_SNPs: # global boolean variable, True or False
			snps_to_exclude = []
			for snpID in match_ID: # type(snpID) --> <type 'str'>. OBS: this is the first time I iterate directly over the index values. THIS SHOULD BE AN FAIRLY EFFICIENT WAY OF LOOPING OVER THE INDEX
				split_list = snpID.split(":")
				(snp_chr, snp_position) = ( int(split_list[0]), int(split_list[1]) ) # OBS: remember to convert to int!
				if snp_chr == 6: # exclude SNPs in the HLA region 6:25000000-6:35000000
					if 25000000 <= snp_position <= 35000000:
						#logger.warning( "%s: found SNP to be excluded" % snpID )
						snps_to_exclude.append(snpID)
			if snps_to_exclude: # enter if block if list is non-empty
				logger.warning( "Found %s SNPs in HLA region that will be excluded" % len(snps_to_exclude) )
				logger.warning( "List of SNPs mapping to HLA region [%s]" % " ".join(snps_to_exclude) )
				#logger.warning( "Length of match_ID BEFORE dropping: %s" % len(match_ID) ) # FOR DEBUGGING
				match_ID = match_ID.drop(snps_to_exclude) # returns nex Index with passed list of labels deleted. (no inplace argument). takes array-like argument
				#logger.warning( "Length of match_ID AFTER dropping: %s" % len(match_ID) ) # FOR DEBUGGING


		### IMPORTANT: Converting Index to Numpy array
		match_ID = match_ID.values # IMPORTANT: transforming data frame into numpy array. This is needed because we used numpy functions like np.setdiff1d
		#^^ we need to convert to numpy regime to be able to sample properly (e.g. use np.random.choice). [Potential alternative solution: the random module could maybe be used in combination with pandas indexing]

		# Unfortunately, we cannot create the 'df_snps_few_matches' DataFrame before we know the columns in df
		if df_snps_few_matches is None: # if true, create DataFrame with correct ordering of columns
			pd.set_option('mode.chained_assignment',None) # OBS: avoids SettingWithCopy exception when doing: row_query['n_matches'] = len(match_ID)
			cols = np.append(df.columns.values, 'n_matches')
			df_snps_few_matches= pd.DataFrame(columns=cols) #df.columns is a Index object

		# ####### Exception if no matches - THIS MAY BE DELETED ########### 
		# 2014-07-03 10:27:11     WARNING *** Found SNP with too few matches; n_matches=0. Using sampling with replacement to get enough samples ***
		# File "/cvar/jhlab/snpsnap/snpsnap/snpsnap_query.py", line 503, in query_similar_snps
		# match_ID_final = np.random.choice(match_ID, size=N_sample_sets, replace=True, p=None)
		# ValueError: a must be non-empty
		match_ID_final = None # initializing value. TODO: initialize to a sensible value
		if len(match_ID) < N_sample_sets:
			logger.warning( "*** Found SNP with too few matches; n_matches=%s. Using sampling with replacement to get enough samples ***" % len(match_ID) )
			# if df_snps_few_matches is None: # if true, create DataFrame with correct ordering of columns
			# 	pd.set_option('mode.chained_assignment',None) # OBS: avoids SettingWithCopy exception when doing: row_query['n_matches'] = len(match_ID)
			# 	cols = np.append(df.columns.values, 'n_matches')
			# 	df_snps_few_matches= pd.DataFrame(columns=cols) #df.columns is a Index object
			row_query = df.ix[i] # this is the current user input SNP
			row_query['n_matches'] = len(match_ID)
			df_snps_few_matches = df_snps_few_matches.append(row_query) # select row (df.ix[i]) --> gives Series object

			if len(match_ID) == 0: # we have zero matches
				# Replicate INPUT SNP until we have enough samples ===> generates N_sample_sets identical values
				match_ID_final = np.random.choice([query_snpID], size=N_sample_sets, replace=True, p=None) #Same as replicating array/list: could use numpy.tile()
			else:
				# Sample snpIDs uniformly from the matches we have at hand until we have enough samples.
				match_ID_final = np.random.choice(match_ID, size=N_sample_sets, replace=True, p=None)
		else:
			match_ID_uniq_new = np.setdiff1d(match_ID, match_ID_old, assume_unique=True) #Return the sorted, unique values in ar1 that are not in ar2
			n_elements_to_fill = N_sample_sets - len(match_ID_old)
			match_ID_uniq_new_sample = np.random.choice(match_ID_uniq_new, size=n_elements_to_fill, replace=False, p=None) # sample uniformly from NEW matches
			match_ID_final = np.concatenate((match_ID_old, match_ID_uniq_new_sample))


		if calculate_mean_input_to_match_ratio: 
			all_matched_snpID = np.append(all_matched_snpID, match_ID_final) # this is a numpy array! 

		# version TOLIST() print
		# insert query_snpID as first element and CONVERT to list
		ID_list = np.insert(match_ID_final, 0, query_snpID).tolist() # np.array --> python list. NB: check that a 'flat' list is returned
		f_matrix_out.write("\t".join(ID_list)+'\n')

		# version NUMPY print. problem: extra tab is added to the end
		#np.savetxt(f_matrix_out, np.insert(match_ID_final, 0, query_snpID), fmt="%s", newline="\t") #delimiter="\n"
		#f_matrix_out.write("\n")
	f_matrix_out.close()
	store.close()
	
	#CALL REPORT FUNCTION
	few_matches_report(path_output, df_snps_few_matches, N_sample_sets, N_snps)

	#CALL calculate_input_to_matched_ratio FUNCTION
	if calculate_mean_input_to_match_ratio:
		report_obj.write_json_report() # OPS: this is important to make sure that a json report is written for "report_snpsnap_score_html" to read.
		status_obj.update_status('match', 'finalizing') ## OBS: this line is important. results.js uses this keyword to check if the bias calucalation has started
		cols2calc=['freq_bin', 'gene_count', 'dist_nearest_gene_snpsnap', colname_ld_buddy_count]
		calculate_input_to_matched_ratio(file_db=file_db, df_input=df, matched_snpID_array=all_matched_snpID, cols2calc=cols2calc) # this function will take care of writing the 

	### Calculate score and write few_matches (if any)
	#if df_snps_few_matches is not None: 
		# few_matches_report(path_output, df_snps_few_matches, N_sample_sets, N_snps)

#@profile
def write_set_file(path_output, df_collection):
	#snpsnap_set_file.tab
	#snpsnap_collection.tab
	#snpsnap_set_collection.tab
	#snpsnap_sets.tab
	#snpsnap_matrix_stats.tab
	#snpsnap_table.tab
	#snpsnap_set_annotation.tab
	user_snps_set_file = path_output+"/matched_snps_annotated.txt"
	matrix_file = path_output+"/matched_snps.txt" #TODO OBS: FIX THIS. the file name should be parsed to the function
	#TODO: check 'integrity' of df_matrix before reading?
	# TWO DIFFERENT VERSIONS. None of them set the index explicitly, but rely either on header or pandas naming columns [0,1,2,...] where 0 is giving to the index
	
	# version READ HEADER: gives index {set1, set2,...}
	#df_matrix = pd.read_csv(matrix_file, index_col=0, header=0, delim_whitespace=True) # index is PARRENT snpID.
	
	# version SKIP HEADER: gives index {0, 1, 2}
	df_matrix = pd.read_csv(matrix_file, index_col=0, header=None, skiprows=1, delimiter="\t") # index is PARRENT snpID.

	if os.path.exists(user_snps_set_file):
		logger.warning( "user_snps_set_file exists. removing file before annotating..." )
		os.remove(user_snps_set_file)

	f_set = open(user_snps_set_file, 'a')
	idx_input_snps = range(len(df_matrix)) # REMEMBER: both python and pandas are zero-based
	logger.info( "START: creating set_file" )
	start_time = time.time()
	for i in idx_input_snps: # len(df_matrix) is equal to the number of user_snps found in db.
		### STATUS
		status_obj.update_pct( 'set_file', (i+1)/float(len(idx_input_snps))*100 ) # float() is needed to avoid interger division

		logger.info( "SNP #%s/#%s: creating and writing to CSV set_file" % (i+1, len(idx_input_snps)) )
		parrent_snp = df_matrix.index[i] # type --> string
		match_snps = df_matrix.ix[i] # series
		set_idx = df_matrix.columns.values 	# copying COLUMN NAMES to np.array, better than: set_idx = range(1,len(df_matrix.columns)+1)
											# gives np.array([1, 2, 3, 4,...]) because 0 is taking by 'index' when header is skipped
		df_container = pd.DataFrame(set_idx, columns=['set']) # SEMI IMPORTANT: new data frame + setting name of column
		df_container.ix[:,'input_snp'] = parrent_snp # creating new column with identical elements

		# TODO 07/03/2014: make a 'try except' block - BUT this is slow.... SEE: http://stackoverflow.com/questions/23643479/pandas-try-df-locx-vs-x-in-df-index
			#try: return df.loc[id_val] except KeyError: return constant_val
		df_match = df_collection.ix[match_snps.values] # IMPORTANT: fetching snps from collection. OBS: we rely on that all SNPs exists in the collection data frame. 
		df_match.index.name = df_collection.index.name # Copy index name, e.g. df_match.index.name = 'snpID'
		df_match.reset_index(inplace=True) # 'freeing' snpID index. Since drop=False by default, the 'snpID' becomes a column now. Index is now 0,1,2...  

		df_final = pd.concat([df_container, df_match], axis=1) # Concatenating: notice ORDER of data frames.
		df_final.set_index('set',inplace=True) # SEMI important: setting index. THEN YOU MUST PRINT index and index_label
		# Writing/appending to CSV file
		if i==0: # write out header - ONLY FIRST TIME!
			df_final.to_csv(f_set, sep='\t', index=True, header=True, index_label='set') # filehandle in appending mode is given
		else:
			df_final.to_csv(f_set, sep='\t', index=True, header=False) # filehandle in appending mode is given
	
	elapsed_time = time.time() - start_time
	logger.info( "END: creating set_file %s s (%s min)" % (elapsed_time, elapsed_time/60) )



def clump_snps(user_snps_df, path_output, clump_r2, clump_kb):
	path_genotype = "/cvar/jhlab/snpsnap/data/step1/full_no_pthin_rmd/CEU_GBR_TSI_unrelated.phase1_dup_excluded"
	#path_genotype = "/cvar/jhlab/snpsnap/data/step1/test_thin0.02_rmd/CEU_GBR_TSI_unrelated.phase1_dup_excluded" # TEST DATA SET!!!
	file_user_snps_clumped = path_output+"/input_snps_clumped.txt"
	file_plink_input_tmp_assoc = path_output + "/tmp.assoc"
	file_plink_output_tmp_prefix = path_output + "/plink_tmp" # this is the filename prefix (root filename). plink will add extensions itself, e.g. .log, .nosex. .clumped
	p_val = "0.00001" # --> str(0.00001) gives 1e-05 when written to file.
	#^OBS: this p_val must be LOWER than (or equal to?) plinks --clump-p1 (default=0.0001) and --clump-p2 (default=0.01). Only SNPs passing p2 significant will be written in the "SP2" column of the .clumped file

	logger.info( "Writing .assoc file: %s" % file_plink_input_tmp_assoc )
	## REMEMBER: Plink needs the 'rsID' to be able to match the SNP IDs with the ones in the genotype data. 
	#If Plink CANNOT find the ID in the genotype data it will create NAs. See below example
	# CHR    F          SNP         BP        P    TOTAL   NSIG    S05    S01   S001  S0001    SP2
	# NA   NA 10:100096148         NA      1e-05       NA     NA     NA     NA     NA     NA     NA
	
	rsID2chrpos_map_dict = {} 	# This dict will have rsID as keys [NOTE: they are ALL UNIQUE] and chrposID as values. THIS MUST BE A 1-1 MAPPING!!
								# This dict is a convenient way of mapping rsIDs back to their corresponding chrposIDs
	chrpos2rsID_map_dict = {} # this dict is created to ensure a 1-1 mapping. THIS WILL NOT BE USED FURTHER (only for asserting about the data type)
	with open(file_plink_input_tmp_assoc, 'w') as f_assoc:
		f_assoc.write("SNP\tP\n") # Writing header - must be detectable by PLINK
		for index, rsID in user_snps_df.ix[:,'rsID'].iteritems(): #iteratable object is a Series object
			#^ taking rsID column out of data frame. .iteritems() gives (index, value) tuples
			
			## Checking non-duplicates of rsIDs
			if not rsID in rsID2chrpos_map_dict.keys(): # .keys() can be removed - only added for clarity.
				rsID2chrpos_map_dict[rsID] = index # index is chrposID
			else:
				logger.critical( "While creating rsID2chrpos_map_dict: Accessed a key that is already in rsID2chrpos_map_dict. See next line for details:" )
				logger.critical( "Previous key-value pair: (key={rsID}; value={chrposID_old}). Current key-value pair: (key={rsID}; value={chrposID_now})".format(rsID=rsID, chrposID_old=rsID2chrpos_map_dict[rsID], chrposID_now=index) )
				logger.critical( "Will raise Exception now..." )
				raise Exception( "Detected that rsID and chrposID is not a 1-1 mapping" )
			## Checking non-duplicates of chrposIDs (index)
			if not index in chrpos2rsID_map_dict.keys(): # .keys() can be removed - only added for clarity.
				chrpos2rsID_map_dict[index] = rsID 
			else:
				logger.critical( "While creating chrpos2rsID_map_dict: Accessed a key that is already in chrpos2rsID_map_dict. See next line for details:" )
				logger.critical( "Previous key-value pair: (key={index}; value={rsID_old}). Current key-value pair: (key={index}; value={rsID_now})".format(index=index, rsID_old=rsID2chrpos_map_dict[rsID], rsID_now=index) )
				logger.critical( "Will raise Exception now..." )
				raise Exception( "Detected that rsID and chrposID is not a 1-1 mapping" )

			f_assoc.write(rsID + "\t" + p_val + "\n")
			### Example of file_plink_input_tmp_assoc (tmp.assoc)
			# SNP     P
			# rs6602381       0.00001
			# rs7899632       0.00001

	### Updating status ###
	status_obj.update_pct( 'clump', float(30) )

	## OBS: plink --out is the 'output root filename', e.g. 
	# Linux snpsnap 2.6.32-431.5.1.el6.x86_64 #1 SMP Fri Jan 10 14:46:43 EST 2014 x86_64 x86_64 x86_64 GNU/Linux
	#/cvar/jhlab/snpsnap/bin/plink-1.07-x86_64/plink
	#cmd_plink = "source /broad/software/scripts/useuse && use .plink-1.07 && plink --bfile {geno} --clump {assoc} --clump-r2 {clump_r2} --clump-kb {clump_kb} --out {file_plink_output_tmp_prefix} --noweb --silent".format(geno=path_genotype, assoc=file_plink_input_tmp_assoc, clump_r2=clump_r2, clump_kb=clump_kb, file_plink_output_tmp_prefix=file_plink_output_tmp_prefix)
	cmd_plink = "/cvar/jhlab/snpsnap/bin/plink-1.07-x86_64/plink --bfile {geno} --clump {assoc} --clump-r2 {clump_r2} --clump-kb {clump_kb} --out {file_plink_output_tmp_prefix} --noweb --silent".format(geno=path_genotype, assoc=file_plink_input_tmp_assoc, clump_r2=clump_r2, clump_kb=clump_kb, file_plink_output_tmp_prefix=file_plink_output_tmp_prefix)
	### REMEMBER plink likely needs to be called as:
	#source /broad/software/scripts/useuse && use .plink-1.07 && plink <plink arguments>
	logger.info( "Making plink call: %s" % cmd_plink )
	fnull = open(os.devnull, "w")
	p_plink = subprocess.Popen(cmd_plink, stdout = fnull, stderr = subprocess.STDOUT, shell=True)
	fnull.close()
	logger.info( "PID = %s | Waiting for plink to finish..." % p_plink.pid )
	p_plink.wait()
	if not p_plink.returncode == 0:
		raise Exception("PID = %s | PLINK crashed during clumping process (return code = %s). Will not continue to process potentially corupted files!" % (p_plink.pid, p_plink.returncode) )
	else:
		logger.info( "PID = %s | DONE. Return code is ok! (return code = %s)" % (p_plink.pid, p_plink.returncode) )


	### Updating status ###
	status_obj.update_pct( 'clump', float(80) )


	n_total_snps = 0 # this is to dobbelt check that PLINK does not loose any SNPs. This number should be EQUAL to the number of input snps
	n_clumped_loci = 0 # OBS each line in .clumped corresponds to a 'independent loci'
	with open(file_plink_output_tmp_prefix+".clumped", 'r') as f_plink_clumped: # note that the filename "plink.clumped" is INVARIABLE (plink assigns this name to the file)
		### Example:
		# CHR    F          SNP         BP        P    TOTAL   NSIG    S05    S01   S001  S0001    SP2
		# 10    1   rs11189555  100092279      1e-05        9      0      0      0      0      9 rs7900936(1),rs10786411(1),rs1536154(1),rs1536153(1),rs7901537(1),rs10883071(1),rs746033(1),rs4917819(1),rs10883072(1)
		# 10    1   rs10883068  100091769      1e-05        1      0      0      0      0      1 rs12761064(1)
		# 10    1   rs55950087  100091388      1e-05        0      0      0      0      0      0 NONE
		## NOTE#1: The (1) after each SNP name refers to the results file they came from (in this case, there is only a single result file specified, so all values are 1)
		## NOTE#2: The .clumped file contains a few newlines (3?) in the end of the file
		
		## NOTE#3: The .clumped file would look something like the below if the SNP identifiers in .assoc cannot be found in plinks .bim. THIS SHOULD ONLY HAPPEN IF YOU USE TEST GENOTYP DATA (or do not convert to rsID numbers)
		# CHR    F           SNP         BP        P    TOTAL   NSIG    S05    S01   S001  S0001    SP2
		#  NA   NA   rs146350976         NA      1e-05       NA     NA     NA     NA     NA     NA     NA
		#  NA   NA   rs139360817         NA      1e-05       NA     NA     NA     NA     NA     NA     NA
		f_out_clumped = open(file_user_snps_clumped, 'w')
		f_out_clumped.write("index_snp\tn_clumped\tclumped_snps\n") # writing header

		for line in f_plink_clumped.readlines()[1:]: #skipping header
			if not line.strip(): # IMPORTANT: skipping blank lines [these are present in the end of the .clumped file]
				continue
			fields = line.strip().split()
			index_snp = fields[2] # SNP
			clump_total_count = fields[5] #TOTAL
			clumped_snps = fields[11] # SP2

			## Validating .clumped file: making sure that all SNP IDs were found. This is TESTED AND WORKS
			if any(["NA" == field for field in fields]):
				status_obj.update_status('clump', 'ERROR')
				status_obj.update_pct('clump', float(0) )
				raise Exception("While processing .clumped file: found a field with 'NA' values. This means that there were an SNP identifier that PLINK could not find")

			# Counting
			n_clumped_loci += 1
			n_total_snps += int(clump_total_count)+1 # --> +1 reason: include the index SNP


			# Mapping SNP IDs: rsID --> chrposID
			index_snp_chrpos = rsID2chrpos_map_dict[index_snp] # mapping index SNP
			clumped_snps_clean_list_chrpos = None
			if clumped_snps == "NONE": # the field SP2 can be "NONE" if no SNPs where clumped into the index SNP. Then we set the field empty to be consistent with the use of empty fields for SNPsnap.
				clumped_snps_clean_list_chrpos = [""] # LIST with empty string - must be list for ";".join() to work?
			else:
				# Processing clumped_snps (comma seperated):
				clumped_snps_clean_list = [snp.replace('(1)', '') for snp in clumped_snps.split(',')] # splitting on ',' and removing trailing '(1)'.
				# OBS: snp.rstrip('(1)') does NOT work because it potentially removes trailing '1' in the rsID. That is, .rstrip() removes CHARs not SUBSTRINGs

				# Mapping:
				clumped_snps_clean_list_chrpos = [rsID2chrpos_map_dict[snp] for snp in clumped_snps_clean_list]

			## Writing file
			f_out_clumped.write(index_snp_chrpos + "\t" + clump_total_count + "\t" + ";".join(clumped_snps_clean_list_chrpos) + "\n" )

		f_out_clumped.close()

	if not n_total_snps == len(user_snps_df):
		status_obj.update_status('clump', 'ERROR')
		status_obj.update_pct('clump', float(0) )
		raise Exception( "Number of input SNPs (%s) is NOT equal to PLINKs total number of SNPs (%s) listed in the .clumped file." % (len(user_snps_df), n_total_snps) )
	else:
		logger.info("Number of input SNPs (%s) is equal to PLINKs total number of SNPs (%s) listed in the .clumped file." % (len(user_snps_df), n_total_snps) )

	## Creating "independent loci" flag
	user_snps_are_all_independent_loci = None
	if n_clumped_loci == len(user_snps_df):
		user_snps_are_all_independent_loci = True
	else:
		user_snps_are_all_independent_loci = False

	#Updating AND writing report - REMEMBER: this 'report' is the "../XXXX_report_clump.json" file.
	report_news = 	{
					"n_clumped_loci":n_clumped_loci,
					"n_input_loci":len(user_snps_df),
					"user_snps_are_all_independent_loci":user_snps_are_all_independent_loci
					}
					# NOTE: "n_input_loci" is the same is "user_snps_working_set"
	report_obj.report['clumping'].update(report_news)
	report_obj.write_json_report() #it is important to write the report as quickly as possible. [Note that the report is always written at the end of the snpsnap_query.py script]


	### CLEAN-UP - Deleting files
	# delete: file_plink_input_tmp_assoc (path_output/tmp.assoc)
	# delete: file_plink_output_tmp_prefix (path_output/plink_tmp.*)

	os.remove(path_output+"/tmp.assoc")
	plink_tmp_files = glob.glob(path_output+"/plink_tmp.*")
	for f in plink_tmp_files:
		os.remove(f)



###################################### CHECK of INPUT arguments ######################################
def check_max_distance_deviation(value):
	ivalue = int(value)
	if not ivalue >= 1: # max_distance_deviation >= 1
		 raise argparse.ArgumentTypeError("max_distance_deviation argument must be larger or equal to one. Received argument value of %s " % value)
	return ivalue

def check_N_sample_sets(value):
	ivalue = int(value)
	if not ivalue >= 1: # N_sample_sets >= 1. This is because things goes wrong (there will be no matches) if exclude self is enabled
		 raise argparse.ArgumentTypeError("N_sample_sets argument must be larger or equal to one. Received argument value of %s " % value)
	return ivalue

def check_if_path_is_writable(file_path):
	if not os.access(file_path, os.W_OK):
		msg="File path: %s is not writable" % file_path
		raise Exception(msg)
	else:
		return os.path.abspath(file_path)

def check_if_file_is_writable(file_path):
	parrent_dir = os.path.dirname(file_path)
	if not os.access(parrent_dir, os.W_OK):
		msg="Parrent directory [%s] to file [%s] is not writable" % (parrent_dir, file_path)
		raise Exception(msg)
	else:
		return os.path.abspath(file_path)



### I DID NOT FINISH THIS FUNCTION
# def get_logging_option(value):
# 	""" This function will check if the logger is disabled by accepting various 'disabling' values.
# 	If the logger is not disabled, then return the filepath that was given.
# 	If no value is parsed (i.e. the empty value ''), then use the args.output_dir as the log dir """
# 	pass


def ParseArguments():
	""" Handles program parameters and returns an argument class containing all parameters """
	#REMEMBER: argparse uses 'default=None' by default. Thus the NameSpace will have None values for optional arguments not specified
	#TODO: check input variable types!
	# check for integers ans strings
	# check for distance and distance cutoff value: ONLY CERTAIN VALUES ALLOWED
	arg_parser = argparse.ArgumentParser(description="Program to get background distribution matching user input SNPs on the following parameters {MAF, distance to nearest gene, gene density}")
	subparsers = arg_parser.add_subparsers(dest='subcommand',
									   title='subcommands in this script',
									   description='valid subcommands. set subcommand after main program required arguments',
									   help='You can get additional help by writing <program-name> <subcommand> --help')

	## Subparsers
	arg_parser_annotate = subparsers.add_parser('annotate')
	#arg_parser_annotate.set_defaults(func=run_annotate)
	arg_parser_match = subparsers.add_parser('match')
	#arg_parser_annotate.set_defaults(func=run_match)
	
	arg_parser_clump = subparsers.add_parser('clump') # NEW, 09-09-2014

	arg_parser.add_argument("--user_snps_file", help="Path to file with user-defined SNPs", required=True) # TODO: make the program read from STDIN via '-'
	arg_parser.add_argument("--output_dir", type=check_if_path_is_writable, help="Directory in which output files, i.e. random SNPs will be written", required=True)
	#arg_parser.add_argument("--output_dir", type=ArgparseAdditionalUtils.check_if_writable, help="Directory in which output files, i.e. random SNPs will be written", required=True)
	arg_parser.add_argument("--distance_type", help="ld or kb", required=True, choices=['ld', 'kb'])
	
	### Distance cutoff - including choices - gives problem with the need for converting distance_cutoff to str (that is, str(distance_cutoff) is needed at some point) 
	# cutoff_chices = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]+[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000] # or range(100,1100,100)
	# arg_parser.add_argument("--distance_cutoff", help="r2, or kb distance", type=float, required=True, choices=cutoff_chices)
	### Distance cutoff - no choices specified
	arg_parser.add_argument("--distance_cutoff", help="r2, or kb distance (e.g. 0.5 for ld distance_type or 1000 for kb distance_type", required=True)

	# NEW: options
	arg_parser.add_argument("--exclude_HLA_SNPs", help="Bool (switch, takes no value after argument); if set then all matched SNPs mapping to the region 6:25000000-6:35000000 (6:25mb-6:35mb) will be excluded. Input SNPs mapping to this region will be excluded and written to the 'input_snps_excluded' file. (NOTE: enabling this option reduces the speed of SNPsnap). Default is false", action='store_true')
	arg_parser.add_argument("--web", help="If set, the program will run in web mode. VALUE should be the a FILE-PATH+FILE-BASENAME to output (temporary) files - usually this will be the session_id. The web mode activates: 1) ENABLE a status_obj and writing it to json file ([FILE-BASENAME]_status.json); 2) ENABLE a status_obj and writing it to a json report file ([FILE-BASENAME]_report.json);")
	arg_parser.add_argument("--NoLogger", help="Bool (switch, takes no value after argument); if set then logging is DISAPLED. Logfile will be placed in output_dir UNLESS log_dir is given", action='store_true')
	#arg_parser.add_argument("--log_dir", type=check_if_writable, help="DIR to write logfile. Default is to use the args.output_dir. NOTE that if NoLogger is given then log_dir have no function")
	arg_parser.add_argument("--log_file", type=check_if_file_is_writable, help="Full path and filename of the logfile. Default is to use the args.output_dir as DIR and current_script_name as FILENAME. NOTE that if NoLogger is given then log_file have no function")
	## NOT FINISH LOGGING OPTION, 07/07/2014
	#arg_parser.add_argument("--log", type=get_logging_option, help="If set, the program will enable a logger that prints statements to STDOUT and to a file. VALUE should be a full filepath (path and filename) to the log file. DEFAULT if set then logging is DISAPLED. Logfile will be placed in output_dir.")

	#POTENTIAL "OVERALL" arguments:
	# -population

	### MATCH arguments
	arg_parser_match.add_argument("--N_sample_sets", type=check_N_sample_sets, help="Number of matched SNPs to retrieve", required=True) # 1000 - "Permutations?" TODO: change name to --n_random_snp_sets or --N
	arg_parser_match.add_argument("--ld_buddy_cutoff", type=float, help="Choose which ld to use for the ld_buddy_count property, e.g 0.1, 0.2, .., 0.9", required=True, choices=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
	arg_parser_match.add_argument("--exclude_input_SNPs", help="Bool (switch, takes no value after argument); if set then all valid input SNPs are excluded from the matched SNPs. Default is false", action='store_true')
	#TODO: add argument that describes if ABSOLUTE or PERCENTAGE deviation should be used?
	arg_parser_match.add_argument("--max_freq_deviation", type=int, help="Maximal PERCENTAGE POINT deviation of SNP MAF bin [MAF +/- deviation]", required=True) # default=5
	arg_parser_match.add_argument("--max_distance_deviation", type=int, help="Maximal PERCENTAGE deviation of distance to nearest gene [distance +/- %%deviation])", required=True) # default=5
	#TODO: CHECK THAT max_distance_deviation > 1 %
	arg_parser_match.add_argument("--max_genes_count_deviation", type=check_max_distance_deviation, help="Maximal PERCENTAGE deviation of genes in locus [gene_density +/- %%deviation]", required=True) # default=5
	arg_parser_match.add_argument("--max_ld_buddy_count_deviation", type=int, help="Maximal PERCENTAGE deviation of genes in locus [ld_buddy_count +/- %%deviation]", required=True) # default=5
	arg_parser_match.add_argument("--set_file", help="Bool (switch, takes no value after argument); if set then write out set files to rand_set..gz. Default is false", action='store_true')


	### clump arguments
	arg_parser_clump.add_argument("--clump_r2", type=float, help="LD threshold for clumping", default=0.5)
	arg_parser_clump.add_argument("--clump_kb", type=float, help="Physical distance threshold for clumping", default=250)
	#--> genotype data path will be hard coded

	
	args = arg_parser.parse_args()

	return args




def setup_logger(args):
	""" Function to setup logger """
	logger = None
	snpsnap_log_name = None 
	snpsnap_log_dir = None
	current_script_name = os.path.basename(__file__).replace('.py','')

	if args.log_file: # some value has been parsed (and has passed the check_if_writable() check )
		snpsnap_log_dir = os.path.dirname(args.log_file)
		snpsnap_log_name = "{file_name_parsed}_{subcommand}".format(file_name_parsed=os.path.basename(args.log_file), subcommand=args.subcommand) # OBS: logger name will be something like 'logger.SESSIONID_match.log'
	else: # no args.log_file has been parsed, so we use the args.output_dir
		snpsnap_log_dir = args.output_dir
		snpsnap_log_name = "{script}_{subcommand}".format(script=current_script_name, subcommand=args.subcommand) # OBS: logger name will be something like 'logger.snpsnap_query_match.log'

	if args.NoLogger:
		logger = pplogger.Logger(name='dummy', log_dir='dummy', log_format=1, enabled=False).get()
	else:
		logger = pplogger.Logger(name=snpsnap_log_name, log_dir=snpsnap_log_dir, log_format=1, enabled=True).get() # gives logname --> snapsnap_query.py
		logger.setLevel(logging.DEBUG)
		## This works. Exceptions are written to the log AND printed to sys.stderr
		## An alternative solution is to make one big "try except" block in main:
		def handleException(excType, excValue, traceback, logger=logger):
			logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
		sys.excepthook = handleException
	return logger


def LogArguments(args):
	# PRINT RUNNING DESCRIPTION 
	now = datetime.datetime.now()
	logger.critical( '# ' + ' '.join(sys.argv) )
	logger.critical( '# ' + now.strftime("%a %b %d %Y %H:%M") )
	logger.critical( '# CWD: ' + os.getcwd() )
	logger.critical( '# COMMAND LINE PARAMETERS SET TO:' )
	for arg in dir(args):
		if arg[:1]!='_':
			logger.critical( '# \t' + "{:<30}".format(arg) + "{:<30}".format(getattr(args, arg)) )


def run_match(path_data, path_output, prefix, user_snps_file, N_sample_sets, ld_buddy_cutoff, exclude_input_SNPs, max_freq_deviation, max_distance_deviation, max_genes_count_deviation, max_ld_buddy_count_deviation, set_file):
	logger.info( "running match" )
	file_db = locate_db_file(path_data, prefix) # Locate DB files. TODO: make function more robust
	file_collection = locate_collection_file(path_data, prefix) # Locate DB files. TODO: make function more robust
	user_snps = read_user_snps(user_snps_file) # Read input SNPs. Return list
	user_snps_df = lookup_user_snps_iter(file_db, user_snps) # Query DB, return DF
	user_snps_df = process_input_snps(path_output, user_snps, user_snps_df) # Report number of matches to DB and drop SNPs mapping to HLA region
	
	# OUTCOMMENTED 07/03/2014
	#write_user_snps_stats(path_output, user_snps_df) # write stats file (no meta annotation)
	
	query_similar_snps(file_db, path_output, user_snps_df, N_sample_sets, ld_buddy_cutoff, exclude_input_SNPs, max_freq_deviation, max_distance_deviation, max_genes_count_deviation, max_ld_buddy_count_deviation)

	### STATUS
	report_obj.write_json_report() # this one may not be needed. Consider deleting. Think it through
	status_obj.update_status('match', 'complete')

	## TODO: use Threading for the read_collection() call
	if set_file: # if argument is true, then run set files
		status_obj.update_status('set_file', 'running')
		status_obj.update_pct('set_file', float(20) )
		df_collection = read_collection(file_collection)
		write_set_file(path_output, df_collection)
		status_obj.update_status('set_file', 'complete')

def run_annotate(path_data, path_output, prefix, user_snps_file):
	logger.info( "running annotate" )
	file_db = locate_db_file(path_data, prefix) # Locate DB files. TODO: make function more robust
	file_collection = locate_collection_file(path_data, prefix) # Locate DB files. TODO: make function more robust
	user_snps = read_user_snps(user_snps_file) # Read input SNPs. Return list
	user_snps_df = lookup_user_snps_iter(file_db, user_snps) # Query DB, return DF
	user_snps_df = process_input_snps(path_output, user_snps, user_snps_df) # Report number of matches to DB and drop SNPs mapping to HLA region
	
	status_obj.update_status('annotate', 'running')
	status_obj.update_pct('annotate', float(20) )
	df_collection = read_collection(file_collection)
	write_user_snps_annotation(path_output, user_snps_df, df_collection)
	status_obj.update_pct('annotate', float(100) )
	status_obj.update_status('annotate', 'complete')

def run_clump(path_data, path_output, prefix, user_snps_file, clump_r2, clump_kb):
	logger.info( "running clump" )
	file_db = locate_db_file(path_data, prefix) # Locate DB files. TODO: make function more robust
	file_collection = locate_collection_file(path_data, prefix) # Locate DB files. TODO: make function more robust
	user_snps = read_user_snps(user_snps_file) # Read input SNPs. Return list
	user_snps_df = lookup_user_snps_iter(file_db, user_snps) # Query DB, return DF
	user_snps_df = process_input_snps(path_output, user_snps, user_snps_df) # Report number of matches to DB and drop SNPs mapping to HLA region
	
	status_obj.update_status('clump', 'running')
	status_obj.update_pct('clump', float(20) )
	clump_snps(user_snps_df, path_output, clump_r2, clump_kb)

	status_obj.update_status('clump', 'complete')
	status_obj.update_pct('clump', float(100) )


class Progress():
	def __init__(self, filebasename, args, enabled): #'tmp_data.json'
		#*OBS*; filebasename will have the value like: '/cvar/jhlab/snpsnap/web_tmp/2ede5955021a10cb0e1a13882be520eb'.
		self.enabled = enabled
		if not self.enabled: return # OBS: important!
		self.fname = "{name_parsed}_{file_type}_{subcommand}.{ext}".format(name_parsed=filebasename, file_type='status', subcommand=args.subcommand, ext='json')
		# e.g. /e43f990bbb981b008b9d84b22c2770f8_status_match.json
		#self.fh = open(fname, 'w')

		### OUTCOMMENTED 09/11/2014 - this code is just silly... May be deleted!
		# if args.subcommand == "match":
		# 	self.fname = "{name_parsed}_{subcommand}.{ext}".format(name_parsed=filebasename, subcommand='status_match', ext='json')
		# 	# e.g. /e43f990bbb981b008b9d84b22c2770f8_status_match.json
		# 	#self.fh = open(fname, 'w')
		# elif args.subcommand == "annotate":
		# 	self.fname = "{name_parsed}_{subcommand}.{ext}".format(name_parsed=filebasename, subcommand='status_annotate', ext='json')
		# 	# e.g. /e43f990bbb981b008b9d84b22c2770f8_status_annotate.json
		# 	#self.fh = open(fname, 'w')
		# elif args.subcommand == "clump":
		# 	self.fname = "{name_parsed}_{subcommand}.{ext}".format(name_parsed=filebasename, subcommand='status_clump', ext='json')
		# 	# e.g. /e43f990bbb981b008b9d84b22c2770f8_status_clump.json
		# else:
		# 	emsg = "Could not find matching subcommand. You may have changed the name of the subcommands"
		# 	logger.critical( emsg )
		# 	raise Exception( emsg )
		
		self.match = {'pct_complete':0, 'status':'waiting'} # will be updated under args.subcommand == "match"
		self.bias = {'pct_complete':0, 'status':'waiting'} # will be updated under args.subcommand == "match"
		self.set_file = {'pct_complete':0, 'status':'waiting'} # will be updated under args.subcommand == "match"
		self.annotate = {'pct_complete':0, 'status':'waiting'} # will be updated under args.subcommand == "annotate"
		self.clump = {'pct_complete':0, 'status':'waiting'} # will be updated under args.subcommand == "clump"
		
		self.status_now = {'match':self.match, 'bias':self.bias, 'set_file':self.set_file, 'annotate':self.annotate, 'clump':self.clump}
		self.status_list = [self.status_now] # NOT NESSESARY. This war only implemented to have a full list of the status bar


	def update_pct(self, selector, pct):
		if not self.enabled: return
		self.status_now[selector]['pct_complete'] = pct
		self.status_list.append(self.status_now) # not needed
		self._write_status()

	def update_status(self, selector, status_txt):
		# Statements that should be used are: 
		# "not_running" (default)
		# (initializing?)
		# running
		# complete
		if not self.enabled: return
		self.status_now[selector]['status'] = status_txt
		self.status_list.append(self.status_now) # not needed
		self._write_status()

	## Private function
	def _write_status(self):
		with open(self.fname, 'w') as f:
			json.dump(self.status_now, f)
			#json.dump(self.status_now, f, indent=3)
			#json.dump(self.status, f)

	def finish(self):
		""" Closing file handle """
		sefl.fh.close()


class Report():
	def __init__(self, filebasename, args, enabled): #'tmp_data.json'
		self.enabled = enabled
		#*OBS*; filebasename will have the value like: '/cvar/jhlab/snpsnap/web_tmp/2ede5955021a10cb0e1a13882be520eb'.
		#self.fname = "{name_parsed}_{subcommand}.{ext}".format(name_parsed=filebasename, subcommand='report', ext='json') ### OUTCOMMENTED 09/11/2014. May be deleted!
		self.fname = "{name_parsed}_{file_type}_{subcommand}.{ext}".format(name_parsed=filebasename, file_type='report', subcommand=args.subcommand, ext='json')
		logger.info( "report: %s" % enabled )
		logger.info( "report file name: %s" % self.fname )
		self.report = collections.defaultdict(dict) # two-level dict
		# VALID CATEGORIES: 
		#loci_definition, -->COULD move to bootface
		#match_criteria, -->COULD move to bootface
		#options, --> COULD move to bootface

		#snpsnap_score, --> KEEP HERE
		#misc, (runtime) --> KEEP HERE
		#input, (user_snps_excluded_in_total, user_snps_not_in_db and more) --> KEEP HERE
		#mean_input_to_match_ratio --> KEEP HERE


	def write_json_report(self):
		if not self.enabled: return
		with open(self.fname, 'w') as f:
			json.dump(self.report, f, indent=3)


def main():	
	args = ParseArguments()
	global logger
	logger = setup_logger(args)
	LogArguments(args)


	### Progress class
	global status_obj
	global report_obj
	filebasename = args.web # Example of the value of args.web (if set) - path incl. session_id: '/cvar/jhlab/snpsnap/web_tmp/2ede5955021a10cb0e1a13882be520eb'
	# thus filebasename is a PATH incl a FILEBASENAME. [CONSIDER SPLITTING IT INTO DIR AND BASEFILE]

	################## SWITCH for status and report files ##################
	if args.web:
		status_obj = Progress(filebasename, args, enabled=True)
		report_obj = Report(filebasename, args, enabled=True)
	else:
		status_obj = Progress('dummy', args, enabled=False)
		report_obj = Report('dummy', args, enabled=False) 
	
	### OUTCOMMENTED 09/11/2014 - KEEP code for now! There are some good comments!
	# if args.web and args.subcommand == "match":
	# 	status_obj = Progress(filebasename, args, enabled=True)
	# 	report_obj = Report(filebasename, args, enabled=True)
	# elif args.web and args.subcommand == "annotate":
	# 	status_obj = Progress(filebasename, args, enabled=True)
	# 	report_obj = Report('dummy', args, enabled=False) # do not enable report if command is annotate. 
	# 	# Enabling "report_obj" for "annotation" will LIKELY overwrite the report file generated by 'match'. The 'annotate' report does not contain all 'fields', e.g. there is will be no self.report_obj['report']['insufficient_rating'] in launchApp function generate_report_for_email()
	# 	# To be precise: it will overwrite when the 'annotate' process is slower than the 'match' process; remember: launchApp.py runs the 'match' and 'annotate' in parallel.
	# 	# REMEMBER: with the current WEB implementation, the 'annotate' command will never be run without the 'match' command.
	# elif args.web and args.subcommand == "clump":
	# 	status_obj = Progress(filebasename, args, enabled=True)
	# 	report_obj = Report('dummy', args, enabled=False) # do not enable report if command is annotate.
	# 	#OBS: See the text/remarks about keeping 
	# else:
	# 	#status_obj = None
	# 	status_obj = Progress('dummy', args, enabled=False)
	# 	report_obj = Report('dummy', args, enabled=False) 


	## TODO: remember to close the status_obj filehandle --> status.obj.finish()

	### CONSTANTS ###
	#path_data = os.path.abspath("/Users/pascaltimshel/snpsnap/data/step3") ## OSX - HARD CODED PATH!!
	#path_data = os.path.abspath("/cvar/jhlab/snpsnap/data/step3/ld0.5") ## BROAD - HARD CODED PATH - BEFORE June 2014 (before production_v1)!!
	path_data = os.path.abspath("/cvar/jhlab/snpsnap/data/step3/1KG_snpsnap_production_v1_uncompressed_incl_rsID") ## BROAD - version: production_v1
	#path_data = os.path.abspath("/cvar/jhlab/snpsnap/data/step3/1KG_snpsnap_production_v1_single_ld") ## SINGLE LD BROAD - version: production_v1
	prefix = args.distance_type + args.distance_cutoff
	path_output = os.path.abspath(args.output_dir)

	user_snps_file = args.user_snps_file

	######################################################
	################## GLOBAL ARGUMENTS ##################
	global exclude_HLA_SNPs
	exclude_HLA_SNPs = args.exclude_HLA_SNPs # exclude_HLA_SNPs with either be True or False since 'store_true' is used


	##########################################################################
	################# GLOBAL *INTERNAL* ARGUMENTS - NOT COMMAND LINE #########
	global data_frame_query
	global calculate_mean_input_to_match_ratio
	calculate_mean_input_to_match_ratio = True
	data_frame_query = False # if set, then read in the whole HDF5 file into a DataFrame. DID NOT IMPROVE SPEED
	#########################################################################
	#########################################################################


	start_time = time.time()
	## Run appropriate subfunction
	if args.subcommand == "match":
		max_freq_deviation = args.max_freq_deviation
		max_distance_deviation = args.max_distance_deviation
		max_genes_count_deviation = args.max_genes_count_deviation
		max_ld_buddy_count_deviation = args.max_ld_buddy_count_deviation
		N_sample_sets = args.N_sample_sets
		ld_buddy_cutoff = args.ld_buddy_cutoff # NEW
		exclude_input_SNPs = args.exclude_input_SNPs # NEW
		set_file = args.set_file
		run_match(path_data, path_output, prefix, user_snps_file, N_sample_sets, ld_buddy_cutoff, exclude_input_SNPs, max_freq_deviation, max_distance_deviation, max_genes_count_deviation, max_ld_buddy_count_deviation, set_file)
	elif args.subcommand == "annotate":
		run_annotate(path_data, path_output, prefix, user_snps_file)
		## Remember: if annotate is called we should not create a report.
		## This is due to the fact that annotate is never called "stand-alone" from the web serive
	elif args.subcommand == "clump":
		clump_r2 = args.clump_r2
		clump_kb = args.clump_kb
		run_clump(path_data, path_output, prefix, user_snps_file, clump_r2, clump_kb)
		## Remember: if clump is called we should not create a report. REASON: see explanation for annotate
	else:
		logger.error( "Error in command line arguments - raising exception" )
		raise Exception( "ERROR: command line arguments not passed correctly. Fix source code!" )
	
	elapsed_time = time.time() - start_time
	logger.info( "TOTAL RUNTIME: %s s (%s min)" % (elapsed_time, elapsed_time/60) )
	#if report_obj.enabled:
	run_time_formatted_seconds = "{:.2f}".format(elapsed_time)
	#total_runtime_in_seconds_for_snp_matching_and_bias_calculation
	run_time_string = "total_runtime_in_seconds_{subcommand}".format(subcommand=args.subcommand)
	report_news = {run_time_string:run_time_formatted_seconds} 
	report_obj.report['misc_%s' % args.subcommand].update(report_news)
	########### WRITING REPORT #########
	logger.info( "Writing json report to %s" % report_obj.fname )
	report_obj.write_json_report() # this MUST be the very last step! [But also ok to do before]
	####################################


if __name__ == '__main__':
	main()


