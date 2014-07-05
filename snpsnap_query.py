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

#from memory_profiler import profile # USE THIS FOR MEMORY PROFILING - DOES NOT WORK ON VM SNPSNAP (MODULE NOT INSTALLED) 
#import profilehooks #  USE THIS FOR TIMING PROFILING
#import timeit
#import cProfile #or profile

import json

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
	""" This function will query the user_snps (type list) against the data base index """
	logger.info( "START: lookup_user_snps_iter" )
	start_time = time.time()
	store = pd.HDFStore(file_db, 'r')
	list_of_df = []
	#user_snps_df = pd.DataFrame() # APPEND VERSION - WORKS, but NO control of column order. Consider: pd.DataFrame(columns=colnames)
	for item in user_snps:
		df = store.select('dummy', "index=['%s']" % item) # Remember to quote the string!
		## ^^ df will be an empty DataFrame if there is no SNP with the quired index (NOTE that this is not the same as indexing in a pandas data frame: here a KeyError will be thrown if the index does not exists)
		## ^^ nothing happens when appending/concatenating empty DataFrames

		#TODO: check length of df. MUST BE EXACTLY ONE!!! ****
		#TODO: immediately write out snps/items with wrong len(df)?
		list_of_df.append(df)
		#user_snps_df = user_snps_df.append(df) # APPEND VERSION - WORKS.
	store.close()
	user_snps_df = pd.concat(list_of_df)
	elapsed_time = time.time() - start_time
	logger.info( "END: lookup_user_snps_iter in %s s (%s min)" % (elapsed_time, elapsed_time/60) )
	
	return user_snps_df



def exclude_snps(path_output, user_snps, df):
	user_snps_excluded = path_output+"/input_snps_excluded.tab"
	logger.info( "START: doing exclude_snps, that is SNPs that will be excluded" )
	start_time = time.time()

	snps_excluded = {}
	n_snps_not_in_db = 0 # counter for snps not found in data base - USED IN report_news 
	for snp in user_snps:
		if not (df.index == snp).any():
			snps_excluded[snp] = "SNP_not_found_in_data_base"
			n_snps_not_in_db += 1
	logger.warning( "{} SNPs not found in data base:\n{}".format( n_snps_not_in_db, "\n".join(snps_excluded.keys()) ) ) # OBS: more SNPs may be added to snps_excluded in the exclude_HLA_SNPs step
	logger.info( "Found %d out of the %d user input SNPs in data base" % (len(df.index), len(user_snps)) )

	if exclude_HLA_SNPs: # global boolean variable, True or False
		snps_in_HLA = [] # this list will be used to drop input SNPs fra the DataFrame (df) mapping to HLA
		for snp in user_snps: # OBS: we are looping twice over user_snps. I choose this to improve readability
			#NOTE: SNPs that will be excluded because they map to HLA may alreay exists in snps_excluded because they where not found in the data base.
			# OBS: you need to be careful what operations you perform on the user_snps - prepare for the most crazy input. Thus use 'try except' when doing operations on them
			# BONUS: we also do not overwrite their 'reason' for exclusion this way
			if snp not in snps_excluded: # WE ARE NOW SURE THAT THE SNP EXISTS IN OUR DATA-BASE: this is a quality mark/control
				split_list = snp.split(":")
				(snp_chr, snp_position) = ( int(split_list[0]), int(split_list[1]) ) # OBS: remember to convert to int!
				# ^^ if the user input is e.g. 'Q&*)@^)@*$&Y_' or 'blabla' a ValueError will be raised if trying to convert to int
				if snp_chr == 6: # exclude SNPs in the HLA region 6:25000000-6:35000000
					if 25000000 <= snp_position <= 35000000:
						snps_excluded[snp] = "SNP_in_HLA_region"
						snps_in_HLA.append(snp) # appending to list for exclusion
		logger.warning( "{} SNPs mapping to HLA region:\n{}".format( len(snps_in_HLA), "\n".join(snps_in_HLA) ) ) # OBS: more SNPs may be added to snps_excluded in the exclude_HLA_SNPs step
		logger.warning( "Excluding the SNPs mapping to HLA region...")
		df.drop(snps_in_HLA, axis=0, inplace=True) # inplace dropping index mapping to HLA

	if snps_excluded: # if non-empty
		logger.warning( "{} SNPs in total not found or excluded because they map to HLA region".format(len(snps_excluded)) )
		# WRITING SNPs not found to FILE
		with open(user_snps_excluded, 'w') as f:
			for snp in sorted(snps_excluded, key=snps_excluded.get): # sort be the dict value (here snps_excluded[snp]='reason')
				f.write(snp+"\t"+snps_excluded[snp]+"\n")

	# print "*** Warning: Number of unique snpIDs (index) found: %d" % len(np.unique(df.index.values))
	# bool_duplicates = pd.Series(df.index).duplicated().values # returns true for duplicates
	# df_duplicate = df.ix[bool_duplicates]
	# print df_duplicate
	# idx_duplicate = df_duplicate.index
	# print "Pandas data frame with index of duplicate:"
	# print df.ix[idx_duplicate]
	elapsed_time = time.time() - start_time
	logger.info( "END: exclude_snps in %s s (%s min)" % (elapsed_time, elapsed_time/60) )

	if report_obj.enabled:
		report_news = 	{	"unique_user_snps":len(user_snps),
							"snps_in_total_excluded":len(snps_excluded),
							"n_snps_not_in_db":n_snps_not_in_db,
							"n_snps_in_HLA":len(snps_in_HLA)
							}
		report_obj.report['input'].update(report_news)

	### RETURNING DataFrame
	#Note: if exclude_HLA_SNPs is enabled, then the DataFrame (df) will be a modified version of the one parsed to this function
	return df 

# NOT IN USE SINCE 07/03/2014 - MAY BE OUTCOMMENTED/DELETED
# def write_user_snps_stats(path_output, df):
# 	user_snps_stats_file = path_output+"/input_snps.tab"
# 	df.to_csv(user_snps_stats_file, sep='\t', header=True, index=True,  mode='w')

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

	user_snps_annotated_file = path_output+"/input_snps_annotated.tab"
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
		user_snps_few_matches_file = path_output+"/input_snps_insufficient_matches.tab"
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
		report_obj.report['report'].update(report_news)
		
					#'insufficient_scale_str':insufficient_scale_str,
					#'match_size_scale_str':match_size_scale_str



	


#@profile
def query_similar_snps(file_db, path_output, df, N_sample_sets, ld_buddy_cutoff, exclude_input_SNPs, max_freq_deviation, max_distance_deviation, max_genes_count_deviation, max_ld_buddy_count_deviation):
	status_obj.update_status('match', 'running')
	

	np.random.seed(1) # Always set seed to be able to reproduce result. np.choice is dependent on seed()
	n_attempts = 5 # use this variable to adjust balance between speed (n_attempts low) and getting best matches (n_attempts high)
	
	df_snps_few_matches = None

	user_snps_matrix_file = path_output+"/matched_snps.tab"
	if os.path.exists(user_snps_matrix_file): # removing any existing file. REASON: we are appending to matrix_file
		os.remove(user_snps_matrix_file)
	f_matrix_out = open(user_snps_matrix_file,'a')
	f_matrix_out.write('Input_SNP\t%s\n' % "\t".join(['Set_'+str(i) for i in xrange(1,N_sample_sets+1)])) #IMPORTANT: writing out header!
	
	store = pd.HDFStore(file_db, 'r')

	idx_input_snps = range(len(df.index)) # REMEMBER: both python and pandas are zero-based
	N_snps = len(idx_input_snps)
	for i in idx_input_snps:
		query_snpID = df.index[i]
		freq = df.ix[i,'freq_bin']
		gene_count = df.ix[i,'gene_count']
		dist = df.ix[i,'dist_nearest_gene_snpsnap']
		colname_ld_buddy_count = 'friends_ld'+str(ld_buddy_cutoff).replace(".", "") # e.g. friends_ld02. "ld_buddy_cutoff" will be a FLOAT like "0.2"
		ld_buddy_count = df.ix[i,colname_ld_buddy_count] #NEW

		### Setting delta space ####
		delta_freq = np.rint(np.linspace(0,max_freq_deviation, n_attempts)).astype(int) # rounds to nearest integer and convert to int
		# OBS: delta_gene_count and delta_dist are in the range of [-1;1]
		delta_gene_count = np.linspace(0,max_genes_count_deviation, n_attempts)/float(100)
		if max_distance_deviation < 1:
			logger.error( "max_distance_deviation set to %s. Lowest possible max_distance_deviation is 1." % max_distance_deviation )
			max_distance_deviation = 1
		delta_dist = np.linspace(1,max_distance_deviation, n_attempts)/float(100) # OBS distance deviation starts at 1 %
		delta_ld_buddy_count = np.linspace(1,max_ld_buddy_count_deviation, n_attempts)/float(100) # NEW

		### Calculating low/high boundaries
		freq_low = np.repeat(freq, n_attempts) - delta_freq # ABSOLUTE DEVIATION
		freq_high = np.repeat(freq, n_attempts) + delta_freq # ABSOLUTE DEVIATION
		gene_count_low = np.repeat(gene_count, n_attempts)*(1-delta_gene_count)
		gene_count_high = np.repeat(gene_count, n_attempts)*(1+delta_gene_count)
		dist_low = np.repeat(dist, n_attempts)*(1-delta_dist)
		dist_high = np.repeat(dist, n_attempts)*(1+delta_dist)
		ld_buddy_count_low = np.repeat(ld_buddy_count, n_attempts)*(1-delta_ld_buddy_count)
		ld_buddy_count_high = np.repeat(ld_buddy_count, n_attempts)*(1+delta_ld_buddy_count)

		logger.info( "SNP #%d/%d: ID starting query in data base" % (i+1, N_snps) )
		match_ID_old = None # placeholder for a Numpy array
		match_ID = None # placeholder for a Numpy array
		for attempt in xrange(n_attempts):
			query_freq = '(freq_bin >= %s & freq_bin <= %s)' % (freq_low[attempt], freq_high[attempt])
			query_gene_count = '(gene_count >= %s & gene_count <= %s)' % (gene_count_low[attempt], gene_count_high[attempt])
			query_dist = '(dist_nearest_gene_snpsnap  >= %s & dist_nearest_gene_snpsnap  <= %s)' % (dist_low[attempt], dist_high[attempt])
			query_ld_buddy_count = '({col} >= {min} & {col} <= {max})'.format(col=colname_ld_buddy_count, min=ld_buddy_count_low[attempt], max=ld_buddy_count_high[attempt])

			query = "%s & %s & %s & %s" % (query_freq, query_gene_count, query_dist, query_ld_buddy_count)
			#match_ID = store.select('dummy', query, columns=[]).index.values # return no columns --> only index # USED BEFORE JUNE 30
			start_time = time.time()
			match_ID = store.select('dummy', query, columns=[]) # return no columns --> only index 
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
	user_snps_set_file = path_output+"/matched_snps_annotated.tab"
	matrix_file = path_output+"/matched_snps.tab" #TODO OBS: FIX THIS. the file name should be parsed to the function
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

def ParseArguments():
	""" Handles program parameters and returns an argument class containing 
	all parameters """
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

	arg_parser.add_argument("--user_snps_file", help="Path to file with user-defined SNPs", required=True) # TODO: make the program read from STDIN via '-'
	arg_parser.add_argument("--output_dir", help="Directory in which output files, i.e. random SNPs will be written", required=True)
	#arg_parser.add_argument("--output_dir", type=ArgparseAdditionalUtils.check_if_writable, help="Directory in which output files, i.e. random SNPs will be written", required=True)
	arg_parser.add_argument("--distance_type", help="ld or kb", required=True, choices=['ld', 'kb'])
	
	### Distance cutoff - including choices - gives problem with the need for converting distance_cutoff to str (that is, str(distance_cutoff) is needed at some point) 
	# cutoff_chices = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]+[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000] # or range(100,1100,100)
	# arg_parser.add_argument("--distance_cutoff", help="r2, or kb distance", type=float, required=True, choices=cutoff_chices)
	### Distance cutoff - no choices specified
	arg_parser.add_argument("--distance_cutoff", help="r2, or kb distance (e.g. 0.5 for ld distance_type or 1000 for kb distance_type", required=True)

	# NEW: options
	arg_parser.add_argument("--exclude_HLA_SNPs", help="Bool (switch, takes no value after argument); if set then all matched SNPs mapping to the region 6:25000000-6:35000000 (6:25mb-6:35mb) will be excluded. Input SNPs mapping to this region will be excluded and written to the 'input_snps_excluded' file. (NOTE: enabling this option reduces the speed of SNPsnap). Default is false", action='store_true')
	arg_parser.add_argument("--web", help="If set, the program will run in web mode. VALUE should be the a filepath to output (temporary) file - usually this will be the session_id. The web mode activates: 1) creating a status_obj and writing it to json file; 2) ENABLE writing a json report file;")
	arg_parser.add_argument("--NoLogger", help="Bool (switch, takes no value after argument); if set then logging is DISAPLED. Logfile will be placed in outputdir.", action='store_true')


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

	args = arg_parser.parse_args()

	return args




def setup_logger(args):
	""" Function to setup logger """
	import logging
	import sys
	import pplogger

	logger = None
	if args.NoLogger:
		logger = pplogger.Logger(name=current_script_name, log_dir=args.output_dir, log_format=1, enabled=False).get()
	else:
		current_script_name = os.path.basename(__file__).replace('.py','')
		logger = pplogger.Logger(name=current_script_name, log_dir=args.output_dir, log_format=1, enabled=True).get() # gives logname --> snapsnap_query.py
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
	user_snps_df = exclude_snps(path_output, user_snps, user_snps_df) # Report number of matches to DB and drop SNPs mapping to HLA region
	
	# OUTCOMMENTED 07/03/2014
	#write_user_snps_stats(path_output, user_snps_df) # write stats file (no meta annotation)
	
	query_similar_snps(file_db, path_output, user_snps_df, N_sample_sets, ld_buddy_cutoff, exclude_input_SNPs, max_freq_deviation, max_distance_deviation, max_genes_count_deviation, max_ld_buddy_count_deviation)

	### STATUS
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
	user_snps_df = exclude_snps(path_output, user_snps, user_snps_df) # Report number of matches to DB and drop SNPs mapping to HLA region
	
	status_obj.update_status('annotate', 'running')
	status_obj.update_pct('annotate', float(20) )
	df_collection = read_collection(file_collection)
	write_user_snps_annotation(path_output, user_snps_df, df_collection)
	status_obj.update_pct('annotate', float(100) )
	status_obj.update_status('annotate', 'complete')



class Progress():
	def __init__(self, sid, args, enabled): #'tmp_data.json'
		self.enabled = enabled
		if not self.enabled: return

		if args.subcommand == "match":
			self.fname = "{name_parsed}_{subcommand}.{ext}".format(name_parsed=sid, subcommand='status_match', ext='json')
			# e.g. /e43f990bbb981b008b9d84b22c2770f8_status_match.json
			#self.fh = open(fname, 'w')
		elif args.subcommand == "annotate":
			self.fname = "{name_parsed}_{subcommand}.{ext}".format(name_parsed=sid, subcommand='status_annotate', ext='json')
			# e.g. /e43f990bbb981b008b9d84b22c2770f8_status_annotate.json
			#self.fh = open(fname, 'w')
		else:
			emsg = "Could not find matching subcommand. You may have changed the name of the subcommands"
			logger.critical( emsg )
			raise Exception( emsg )
		
		self.match = {'pct_complete':0, 'status':'not_running'}
		self.set_file = {'pct_complete':0, 'status':'not_running'}
		self.annotate = {'pct_complete':0, 'status':'not_running'}
		
		self.status_now = {'match':self.match, 'set_file':self.set_file, 'annotate':self.annotate}
		self.status_list = [self.status_now] # NOT NESSESARY


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
	def __init__(self, sid, args, enabled): #'tmp_data.json'
		self.enabled = enabled
		self.fname = "{name_parsed}_{subcommand}.{ext}".format(name_parsed=sid, subcommand='report', ext='json')
		self.report = collections.defaultdict(dict) # two-level dict
		#self.report = {} 
		# VALID CATEGORIES: 
		#loci_definition, 
		#match_criteria, 
		#options, 
		#report, 
		#mics, 
		#input


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
	# Example of the value of web (if set) - path incl. session_id: '/cvar/jhlab/snpsnap/web_tmp/2ede5955021a10cb0e1a13882be520eb'
	if args.web and args.subcommand == "match":
		sid = args.web
		status_obj = Progress(sid, args, enabled=True)
		report_obj = Report(sid, args, enabled=True)
	elif args.web and args.subcommand == "annotate":
		sid = args.web
		status_obj = Progress(sid, args, enabled=True)
		report_obj = Report('dummy', args, enabled=False) # do not enable report if command is annotate. 
		# This will likely overwrite the report file generated by 'match'. The 'annotate' report does not contain all 'fields', e.g. there is will be no self.report_obj['report']['insufficient_rating'] in launchApp function generate_report_for_email()
		# To be precise: it will overwrite when the 'annotate' process is slower than the 'match' process; remember: launchApp.py runs the 'match' and 'annotate' in parallel.
		# REMEMBER: with the current implementation, the 'annotate' command will never be run without the 'match' command.
	else:
		#status_obj = None
		status_obj = Progress('dummy', args, enabled=False)
		report_obj = Report('dummy', args, enabled=False) 


	## TODO: remember to close the status_obj filehandle --> status.obj.finish()

	### CONSTANTS ###
	#path_data = os.path.abspath("/Users/pascaltimshel/snpsnap/data/step3") ## OSX - HARD CODED PATH!!
	#path_data = os.path.abspath("/cvar/jhlab/snpsnap/data/step3/ld0.5") ## BROAD - HARD CODED PATH - BEFORE June 2014 (before production_v1)!!
	
	path_data = os.path.abspath("/cvar/jhlab/snpsnap/data/step3/1KG_snpsnap_production_v1_bhour") ## BROAD - version: production_v1
	#path_data = os.path.abspath("/cvar/jhlab/snpsnap/data/step3/1KG_snpsnap_production_v1_single_ld") ## SINGLE LD BROAD - version: production_v1
	prefix = args.distance_type + args.distance_cutoff
	path_output = os.path.abspath(args.output_dir)

	user_snps_file = args.user_snps_file

	################## GLOBAL ARGUMENTS ##################
	global exclude_HLA_SNPs
	exclude_HLA_SNPs = args.exclude_HLA_SNPs # exclude_HLA_SNPs with either be True or False since 'store_true' is used
	#####################################################
	report_news =	{'exclude_HLA_SNPs':args.exclude_HLA_SNPs} # could also use just exclude_HLA_SNPs
	report_obj.report['options'].update(report_news)

	### OBS: loci_definition could possibly be moved into the 'if args.subcommand == "match":' block - they are only used by "match"
	report_news =	{'distance_type':args.distance_type,
					'distance_cutoff':args.distance_cutoff
					}
	report_obj.report['loci_definition'].update(report_news)


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
		if report_obj.enabled:
			report_news =	{'max_freq_deviation':max_freq_deviation,
							'max_distance_deviation':max_distance_deviation,
							'max_genes_count_deviation':max_genes_count_deviation,
							'max_ld_buddy_count_deviation':max_ld_buddy_count_deviation # NEW
							}
			report_obj.report['match_criteria'].update(report_news)
			
			report_news =	{'required_matched_SNPs':N_sample_sets, #*** OBS: different name!
							'ld_buddy_cutoff':ld_buddy_cutoff,
							'exclude_input_SNPs':exclude_input_SNPs,
							'annotate_matched_SNPs':set_file
							}
			report_obj.report['options'].update(report_news)
							
	elif args.subcommand == "annotate":
		run_annotate(path_data, path_output, prefix, user_snps_file)
		## Remember: if annotate is called we should not create a report.
		## This is due to the fact that annotate is never called "stand-alone" from the web serive
	else:
		logger.error( "Error in command line arguments - raising exception" )
		raise Exception( "ERROR: command line arguments not passed correctly. Fix source code!" )
	elapsed_time = time.time() - start_time
	logger.info( "TOTAL RUNTIME: %s s (%s min)" % (elapsed_time, elapsed_time/60) )

	if report_obj.enabled:
		run_time_min = "{:.2f}".format(elapsed_time)
		report_news = {"total_runtime_in_seconds":run_time_min}
		report_obj.report['misc'].update(report_news)
		########### WRITING REPORT #########
		report_obj.write_json_report()
		####################################


if __name__ == '__main__':
	main()


