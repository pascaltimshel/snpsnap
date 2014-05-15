#!/usr/bin/env python2.7

import os
import sys
import collections
import argparse
from queue import QueueJob,ArgparseAdditionalUtils

import glob

import pandas as pd
import numpy as np
import gzip

import datetime
import time
#import timeit
#import cProfile #or profile
import memory_profiler
#import profilehooks

import pdb

## Example calls:
#./snpsnap_query.py --user_snps_file /Users/pascaltimshel/git/snpsnap/samples/sample_10randSNPs.list --output_dir /Users/pascaltimshel/snpsnap/data/query --distance_type ld --distance_cutoff 0.5 --N_sample_sets 10

# test data, 10 samples, match, no-sets
#./snpsnap_query.py --user_snps_file /Users/pascaltimshel/git/snpsnap/samples/sample_10randSNPs.list --output_dir /Users/pascaltimshel/snpsnap/data/query --distance_type ld --distance_cutoff 0.5 match --N_sample_sets 1000

# test data, 10 samples, annotate
#./snpsnap_query.py --user_snps_file /Users/pascaltimshel/git/snpsnap/samples/sample_10randSNPs.list --output_dir /Users/pascaltimshel/snpsnap/data/query --distance_type ld --distance_cutoff 0.5 annotate

########### OBS ############
# Hardcoded paths: path_data, e.g. os.path.abspath("/Users/pascaltimshel/snpsnap/data/step3")

############################

## TODO:
# setup login module



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

def locate_db_file(path, prefix):
	#TODO fix this. Make checks
	file_db = "{path}/{type}_db.{ext}".format(path=path, type=prefix, ext='h5')
	# META FILE DISAPLED TEMPORARY
	#file_meta = "{path}/{type}_meta.{ext}".format(path=path, type=prefix, ext='h5')
	#if not ( os.path.exists(file_db) and os.path.exists(file_meta) ): # both file must exists
	if not os.path.exists(file_db): # TODO- FIX THIS LATER
		print "Could not find collection file: %s." % file_db
		print "Exiting..." 
		sys.exit(1)
	#return (file_db, file_meta)
	return file_db

def locate_collection_file(path, prefix):
	file_collection = "{path}/{type}_collection.{ext}".format(path=path, type=prefix, ext='tab.gz')
	if not os.path.exists(file_collection): # TODO- FIX THIS LATER
		print "Could not find collection file: %s." % file_collection
		print "Exiting..." 
		sys.exit(1)
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
			print "Found empty line in user_snps_file %s" % user_snps_file
			continue
		if not words in user_snps:
			#user_snps[words] = 1
			user_snps.append(words)
		else:
			print "*** Warning: user input file contains duplicates"
			if not words in duplicates: # first time we notice a duplicate ==> two entries seen
				duplicates[words] = 2
			else:
				duplicates[words] += 1
	if duplicates: # dict is non-empty
		print "*** List of duplicate SNPs"
		for (k,v) in duplicates.items():
			print "%s\t%s" % (k,v)
	print "Read %d unique user SNPs" % len(user_snps)
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

def lookup_user_snps_iter(file_db, user_snps):
	print "START: lookup_user_snps_iter"
	start_time = time.time()
	store = pd.HDFStore(file_db, 'r')
	list_of_df = []
	#user_snps_df = pd.DataFrame() # APPEND VERSION - WORKS, but NO control of column order. Consider: pd.DataFrame(columns=colnames)
	for item in user_snps:
	#for item in user_snps.keys():
		df = store.select('dummy', "index=['%s']" % item) # Remember to quote the string!
		#TODO: check length of df. MUST BE EXACTLY ONE!!! ****
		#TODO: immediately write out snps/items with wrong len(df)?
		list_of_df.append(df)
		#user_snps_df = user_snps_df.append(df) # APPEND VERSION - WORKS.
	store.close()
	user_snps_df = pd.concat(list_of_df)
	elapsed_time = time.time() - start_time
	print "END: lookup_user_snps_iter in %s s (%s min)" % (elapsed_time, elapsed_time/60)
	
	return user_snps_df


def write_snps_not_in_db(path_output, user_snps, df):
	user_snps_not_found = path_output+"/snps_not_found.tab"

	print "START: doing write_snps_not_in_db"
	start_time = time.time()
	snps_not_in_db = []
	for snp in user_snps:
	#for snp in user_snps.keys():
		if not (df.index == snp).any():
			snps_not_in_db.append(snp)
	if snps_not_in_db: # if non-empty
		print "*** Warning: %d SNPs not found in data base:" % len(snps_not_in_db)
		print "\n".join(snps_not_in_db)

		# WRITING SNPs not found to FILE
		with open(user_snps_not_found, 'w') as f:
			for snp in snps_not_in_db:
				f.write(snp+"\n")
	print "Found %d out of %d SNPs in data base" % (len(df.index), len(user_snps))
	# print "*** Warning: Number of unique snpIDs (index) found: %d" % len(np.unique(df.index.values))
	# bool_duplicates = pd.Series(df.index).duplicated().values # returns true for duplicates
	# df_duplicate = df.ix[bool_duplicates]
	# print df_duplicate
	# idx_duplicate = df_duplicate.index
	# print "Pandas data frame with index of duplicate:"
	# print df.ix[idx_duplicate]
	elapsed_time = time.time() - start_time
	print "END: write_snps_not_in_db in %s s (%s min)" % (elapsed_time, elapsed_time/60)

def write_user_snps_stats(path_output, df):
	user_snps_stats_file = path_output+"/snps_stats.tab"
	df.to_csv(user_snps_stats_file, sep='\t', header=True, index=True,  mode='w')

#@memory_profiler.profile
def read_collection(file_collection):
	"""Function that reads tab seperated gzip collection file"""
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
	f_tab = gzip.open(file_collection, 'rb')
	df_collection = pd.read_csv(f_tab, index_col=0, header=0, delim_whitespace=True) # index is snpID
	f_tab.close()
	elapsed_time = time.time() - start_time
	print "END: read CSV file PRIM into DataFrame in %s s (%s min)" % (elapsed_time, elapsed_time/60)
	return df_collection

def write_user_snps_annotation(path_output, df, df_collection):
	user_snps_annotated_file = path_output+"/snps_annotated.tab"
	df_user_snp_found_index = df.index # index of (found) user snps
	df_user_snps_annotated = df_collection.ix[df_user_snp_found_index]
	df_user_snps_annotated.to_csv(user_snps_annotated_file, sep='\t', header=True, index=True,  mode='w')

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
	user_snps_few_matches_file = path_output+"/snps_few_matches.tab"
	user_snps_few_matches_report = path_output+"/snps_report.txt"
	#score_N = ''
	#score_median = ''

	pct_N_few_matches = ( len(df_snps_few_matches)/float(N_snps) )*100

	if len(df_snps_few_matches) == 0: # NO few_matches found
		median_n_matches = N_snps
	else:
		median_n_matches = df_snps_few_matches.ix[:,'n_matches'].median()

	pct_median_few_matches = ( median_n_matches/float(N_sample_sets) )*100
	
	scale_N = ['very good', 'good', 'ok', 'poor', 'very poor']
	scale_median = ['very poor', 'poor', 'ok', 'good', 'very good']
	# About the use of this few_matches_score:
	# 1) check that the criteria for scale and lim lengths is ok
	# 2) function does ONLY support 5 scores ATM
	# 3) IMPORTANT: limits may have to be reversed for it to work. See the function code..
	score_N = few_matches_score(pct_N_few_matches, [0,1,5,10,25,100], scale_N) #low_is_good
	score_median = few_matches_score(pct_median_few_matches, [100,75,50,30,15,0][::-1], scale_median) #low_is_bad

	#TODO: print scale_order (pass as argument to function)
	# print_str_score_N = "Rating 'number of few matches' = '{rating:s}' ({pct:.4g}%, {count:d} few_matches out of {total:d} valid input SNPs)".format(rating=score_N, 
	# 																											pct=pct_N_few_matches, 
	# 																											count=len(df_snps_few_matches),
	# 																											total=N_snps)
	# print_str_score_median = "Rating 'over sampling' = '{rating:s}' ({pct:.4g}%, median SNPs to sample from in few_matches is {median:.6g} compared to {total:d} N_sample_sets)".format(rating=score_median, 
	# 																											pct=pct_median_few_matches, 
	# 																											median=median_n_matches,
	# 																											total=N_sample_sets)
	

	tmp1 = "# Rating 'number of few matches' = '{rating:s}' with scale [{scale:s}]".format(rating=score_N, scale=(', '.join("'" + item + "'" for item in scale_N)) )
	tmp2 = "# Percent 'few matches' = {pct:.4g}% (low is good; {count:d} 'few matches' out of {total:d} valid input SNPs)".format(pct=pct_N_few_matches, count=len(df_snps_few_matches), total=N_snps)
	write_str_score_N = '\n'.join([tmp1, tmp2])

	tmp1 = "# Rating 'over sampling' = '{rating:s}' with scale [{scale:s}]".format(rating=score_median, scale=(', '.join("'" + item + "'" for item in scale_median)) )
	tmp2 = "# Relative sample size = {pct:.4g}% (high is good; median SNPs to sample from in 'few matches' is {median:.6g} compared to {total:d} N_sample_sets)".format(pct=pct_median_few_matches, median=median_n_matches, total=N_sample_sets)
	write_str_score_median = '\n'.join([tmp1, tmp2])

	tmp1 = "# {0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}".format("rating_few_matches", "pct_few_matches", "N_few_matches", "N_input_snps", 
															"rating_over_sampling", "pct_over_sampling", "median_sample_size", "N_sample_sets")
	#tmp1 = "# rating_few_matches\tpct_few_matches\tN_few_matches\tN_input_snps\trating_over_sampling\tpct_over_sampling\tmedian_sample_size\tN_sample_sets"
	tmp2 = "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}".format(score_N, pct_N_few_matches, len(df_snps_few_matches), N_snps,
															score_median, pct_median_few_matches, median_n_matches, N_sample_sets)
	write_str_score_table = '\n'.join([tmp1, tmp2])
	print "################# Score ###############"
	print write_str_score_N
	print write_str_score_median
	print write_str_score_table
	print "######################################"

	with open(user_snps_few_matches_report, 'w') as f:
		f.write(write_str_score_N+'\n')
		f.write(write_str_score_median+'\n')
		f.write(write_str_score_table+'\n')


	# Write few_matches
	df_snps_few_matches.to_csv(user_snps_few_matches_file, sep='\t', index=True, header=True, index_label='snpID', mode='w') 

	



def query_similar_snps(file_db, path_output, df, N_sample_sets, max_freq_deviation, max_distance_deviation, max_genes_count_deviation):
	np.random.seed(1) # Always set seed to be able to reproduce result. np.choice is dependent on seed()
	n_attempts = 5 # use this variable to adjust balance between speed (n_attempts low) and getting best matches (n_attempts high)
	
	df_snps_few_matches = None

	user_snps_matrix_file = path_output+"/snps_matrix.tab"
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
		dist = df.ix[i,'dist_nearest_gene']

		### Setting delta space ####
		delta_freq = np.rint(np.linspace(0,max_freq_deviation, n_attempts)).astype(int) # rounds to nearest integer and convert to int
		# OBS: delta_gene_count and delta_dist are in the range of [-1;1]
		delta_gene_count = np.linspace(0,max_genes_count_deviation, n_attempts)/float(100)
		if max_distance_deviation < 1:
		    print "Warning: max_distance_deviation set to %s. Lowest possible max_distance_deviation is 1." % max_distance_deviation
		    max_distance_deviation = 1
		delta_dist = np.linspace(1,max_distance_deviation, n_attempts)/float(100) # OBS distance deviation starts at 1 %

		### Calculating low/high boundaries
		freq_low = np.repeat(freq, n_attempts) - delta_freq # ABSOLUTE DEVIATION
		freq_high = np.repeat(freq, n_attempts) + delta_freq # ABSOLUTE DEVIATION
		gene_count_low = np.repeat(gene_count, n_attempts)*(1-delta_gene_count)
		gene_count_high = np.repeat(gene_count, n_attempts)*(1+delta_gene_count)
		dist_low = np.repeat(dist, n_attempts)*(1-delta_dist)
		dist_high = np.repeat(dist, n_attempts)*(1+delta_dist)


		match_ID_old = None # placeholder for a Numpy array
		match_ID = None # placeholder for a Numpy array
		for attempt in xrange(n_attempts):
		    query_freq = '(freq_bin >= %s & freq_bin <= %s)' % (freq_low[attempt], freq_high[attempt])
		    query_gene_count = '(gene_count >= %s & gene_count <= %s)' % (gene_count_low[attempt], gene_count_high[attempt])
		    query_dist = '(dist_nearest_gene  >= %s & dist_nearest_gene  <= %s)' % (dist_low[attempt], dist_high[attempt])
		    
		    query = "%s & %s & %s" % (query_freq, query_gene_count, query_dist)
		    match_ID = store.select('dummy', query, columns=[]).index.values # return no columns --> only index
		    
		    
		    if len(match_ID) < N_sample_sets:
		        match_ID_old = match_ID
		    else: #we have enough matches
		    	match_ID_old = np.array([]) # empty array. This line ensures that len(match_ID_old) is always valid
		        break

		print "SNP #%d/%d: ID {%s}: found %d hits" % (i+1, N_snps, query_snpID, len(match_ID))
		
		# Unfortunately, we cannot create the 'df_snps_few_matches' DataFrame before we know the columns in df
		if df_snps_few_matches is None: # if true, create DataFrame with correct ordering of columns
			pd.set_option('mode.chained_assignment',None) # OBS: avoids SettingWithCopy exception when doing: row_query['n_matches'] = len(match_ID)
			cols = np.append(df.columns.values, 'n_matches')
			df_snps_few_matches= pd.DataFrame(columns=cols) #df.columns is a Index object

		if len(match_ID) < N_sample_sets:
			print "*** Found SNP with too few matches; n_matches=%s. Using sampling with replacement to get enough samples ***" % len(match_ID)
			# if df_snps_few_matches is None: # if true, create DataFrame with correct ordering of columns
			# 	pd.set_option('mode.chained_assignment',None) # OBS: avoids SettingWithCopy exception when doing: row_query['n_matches'] = len(match_ID)
			# 	cols = np.append(df.columns.values, 'n_matches')
			# 	df_snps_few_matches= pd.DataFrame(columns=cols) #df.columns is a Index object
			row_query = df.ix[i]
			row_query['n_matches'] = len(match_ID)
			df_snps_few_matches = df_snps_few_matches.append(row_query) # select row (df.ix[i]) --> gives Series object

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

def write_set_file(path_output, df_collection):
	user_snps_set_file = path_output+"/set_file.tab"
	matrix_file = path_output+"/snps_matrix.tab" #TODO OBS: FIX THIS. the file name should be parsed to the function
	#TODO: check 'integrity' of df_matrix before reading?
	# TWO DIFFERENT VERSIONS. None of them set the index explicitly, but rely either on header or pandas naming columns [0,1,2,...] where 0 is giving to the index
	
	# version READ HEADER: gives index {set1, set2,...}
	#df_matrix = pd.read_csv(matrix_file, index_col=0, header=0, delim_whitespace=True) # index is PARRENT snpID.
	
	# version SKIP HEADER: gives index {0, 1, 2}
	df_matrix = pd.read_csv(matrix_file, index_col=0, header=None, skiprows=1, delim_whitespace=True) # index is PARRENT snpID.

	if os.path.exists(user_snps_set_file):
		print "user_snps_set_file exists. removing file before annotating..."
		os.remove(user_snps_set_file)

	f_set = open(user_snps_set_file, 'a')
	idx_input_snps = range(len(df_matrix)) # REMEMBER: both python and pandas are zero-based
	print "START: creating set_file"
	start_time = time.time()
	for i in idx_input_snps: # len(df_matrix) is equal to the number of user_snps found in db.
		print "SNP #%s/#%s: creating and writing to CSV set_file" % (i+1, len(idx_input_snps))
		parrent_snp = df_matrix.index[i] # type --> string
		match_snps = df_matrix.ix[i] # series
		set_idx = df_matrix.columns.values 	# copying COLUMN NAMES to np.array, better than: set_idx = range(1,len(df_matrix.columns)+1)
											# gives np.array([1, 2, 3, 4,...]) because 0 is taking by 'index' when header is skipped
		df_container = pd.DataFrame(set_idx, columns=['set']) # SEMI IMPORTANT: new data frame + setting name of column
		df_container.ix[:,'input_snp'] = parrent_snp # creating new column with identical elements

		df_match = df_collection.ix[match_snps.values] # IMPORTANT: fetching snps from collection
		df_match.index.name = df_collection.index.name # Copy index name, e.g. df_match.index.name = 'snpID'
		df_match.reset_index(inplace=True) # 'freeing' snpID index. Index is now 0,1,2... 

		df_final = pd.concat([df_container, df_match], axis=1) # Concatenating: notice ORDER of data frames.
		df_final.set_index('set',inplace=True) # SEMI important: setting index. THEN YOU MUST PRINT index and index_label
		# Writing/appending to CSV file
		if i==0: # write out header - ONLY FIRST TIME!
			df_final.to_csv(f_set, sep='\t', index=True, header=True, index_label='set') # filehandle in appending mode is given
		else:
			df_final.to_csv(f_set, sep='\t', index=True, header=False) # filehandle in appending mode is given
	
	elapsed_time = time.time() - start_time
	print "END: creating set_file %s s (%s min)" % (elapsed_time, elapsed_time/60)




def ParseArguments():
	""" Handles program parameters and returns an argument class containing 
	all parameters """
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
	arg_parser.add_argument("--output_dir", type=ArgparseAdditionalUtils.check_if_writable, help="Directory in which output files, i.e. random SNPs will be written", required=True)
	arg_parser.add_argument("--distance_type", help="ld or kb", required=True)
	arg_parser.add_argument("--distance_cutoff", help="r2, or kb distance", required=True)

	### MATCH arguments
	arg_parser_match.add_argument("--N_sample_sets", type=int, help="Number of matched SNPs to retrieve", required=True) # 1000 - "Permutations?" TODO: change name to --n_random_snp_sets or --N
	#TODO: add argument that describes if ABSOLUTE of PERCENTAGE deviation should be used
	arg_parser_match.add_argument("--max_freq_deviation", type=int,help="Maximal deviation of SNP MAF bin [MAF +/- deviation]", default=5) # 5
	arg_parser_match.add_argument("--max_distance_deviation", type=int, help="Maximal PERCENTAGE POINT deviation of distance to nearest gene [distance +/- %%deviation])", default=5) # 20000
	#TODO: CHECK THAT max_distance_deviation > 1 %
	arg_parser_match.add_argument("--max_genes_count_deviation", type=float, help="Maximal PERCENTAGE POINT deviation of genes in locus [gene_density +/- %%deviation]", default=5) # 0.2
	arg_parser_match.add_argument("--set_file", help="Bool (switch, takes no value after argument); if set then write out set files to rand_set..gz. Default is false", action='store_true')

	args = arg_parser.parse_args()

	# PRINT RUNNING DESCRIPTION 
	now = datetime.datetime.now()
	print '# ' + ' '.join(sys.argv)
	print '# ' + now.strftime("%a %b %d %Y %H:%M")
	print '# CWD: ' + os.getcwd()
	print '# COMMAND LINE PARAMETERS SET TO:'
	for arg in dir(args):
		if arg[:1]!='_':
			print '# \t' + "{:<30}".format(arg) +\
				  "{:<30}".format(getattr(args, arg))

	return args

def run_match(path_data, path_output, prefix, user_snps_file, N_sample_sets, max_freq_deviation, max_distance_deviation, max_genes_count_deviation, set_file):
	print "running match"
	file_db = locate_db_file(path_data, prefix) # Locate DB files. TODO: make function more robust
	file_collection = locate_collection_file(path_data, prefix) # Locate DB files. TODO: make function more robust
	user_snps = read_user_snps(user_snps_file) # Read input SNPs. Return list
	user_snps_df = lookup_user_snps_iter(file_db, user_snps) # Query DB, return DF
	write_snps_not_in_db(path_output, user_snps, user_snps_df) # Report number of matches to DB (print STDOUT and file)
	
	write_user_snps_stats(path_output, user_snps_df) # write stats file (no meta annotation)
	query_similar_snps(file_db, path_output, user_snps_df, N_sample_sets, max_freq_deviation, max_distance_deviation, max_genes_count_deviation)

	### TODO: complete write function!
	if set_file: # if argument is true, then run set files
		df_collection = read_collection(file_collection)
		write_set_file(path_output, df_collection)

def run_annotate(path_data, path_output, prefix, user_snps_file):
	print "running annotate"
	file_db = locate_db_file(path_data, prefix) # Locate DB files. TODO: make function more robust
	file_collection = locate_collection_file(path_data, prefix) # Locate DB files. TODO: make function more robust
	user_snps = read_user_snps(user_snps_file) # Read input SNPs. Return list
	user_snps_df = lookup_user_snps_iter(file_db, user_snps) # Query DB, return DF
	write_snps_not_in_db(path_output, user_snps, user_snps_df) # Report number of matches to DB (print STDOUT and file)
	
	df_collection = read_collection(file_collection)
	write_user_snps_annotation(path_output, user_snps_df, df_collection)


def main():	
	args = ParseArguments()

	### CONSTANTS ###
	#path_data = os.path.abspath("/Users/pascaltimshel/snpsnap/data/step3") ## OSX - HARD CODED PATH!!
	path_data = os.path.abspath("/cvar/jhlab/snpsnap/data/step3/ld0.5") ## BROAD - HARD CODED PATH!!
	prefix = args.distance_type + args.distance_cutoff
	path_output = os.path.abspath(args.output_dir)

	user_snps_file = args.user_snps_file


	start_time = time.time()
	## Run appropriate subfunction
	if args.subcommand == "match":
		max_freq_deviation = args.max_freq_deviation
		max_distance_deviation = args.max_distance_deviation
		max_genes_count_deviation = args.max_genes_count_deviation
		N_sample_sets = args.N_sample_sets
		set_file = args.set_file
		run_match(path_data, path_output, prefix, user_snps_file, N_sample_sets, max_freq_deviation, max_distance_deviation, max_genes_count_deviation, set_file)
	elif args.subcommand == "annotate":
		run_annotate(path_data, path_output, prefix, user_snps_file)
	else:
		print "ERROR: command line arguments not passed correctly. Fix source code!"
		print "Exiting..."
		sys.exit(1)
	elapsed_time = time.time() - start_time
	print "TOTAL RUNTIME: %s s (%s min)" % (elapsed_time, elapsed_time/60)




if __name__ == '__main__':
	main()



