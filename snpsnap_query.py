#!/usr/bin/env python2.7

import os
import sys
import collections
import argparse
from queue import QueueJob,ArgparseAdditionalUtils

import glob

import pandas as pd
import numpy as np

import time
import timeit
#import cProfile #or profile
import memory_profiler
import profilehooks

import pdb

## Example calls:
#./snpsnap_query.py --user_snps_file /Users/pascaltimshel/git/snpsnap/samples/sample_10randSNPs.list --output_dir /Users/pascaltimshel/snpsnap/data/query --distance_type ld --distance_cutoff 0.5 --N_sample_sets 10


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

def locate_HDF5_data(path, prefix):
	#TODO fix this. Make checks
	file_db = "{path}/{type}_db.{ext}".format(path=path, type=prefix, ext='h5')
	file_meta = "{path}/{type}_meta.{ext}".format(path=path, type=prefix, ext='h5')
	#if not ( os.path.exists(file_db) and os.path.exists(file_meta) ): # both file must exists
	if not os.path.exists(file_db): # TODO- FIX THIS LATER
		print "Could not find database files. Exiting"
		sys.exit(1)
	return (file_db, file_meta)



# Function to read userdefined list of SNPs
def read_user_snps(user_snps_file):
	#TODO error check:
	# check for match to X:YYYYYY partern: '\d{1-2}:\d+'
	# check for duplicates in list ---> most important
	user_snps = {}
	infile = open(user_snps_file,'r')
	lines = infile.readlines()
	infile.close()
	for line in lines:
		words = line.strip()
		if not words in user_snps:
			#user_snps.append(words)
			user_snps[words] = 1
		else:
			print "Warning: user input file contains dublicates"
	print "Read %d unique user SNPs" % len(user_snps)
	return user_snps

# Function to read in list of all randomized SNPs
#@memory_profiler.profile
#@profilehooks.profile
def lookup_user_snps(file_db, user_snps):
	store = pd.HDFStore(file_db, 'r')
	quoted_list = (', '.join("'" + item + "'" for item in user_snps.keys() ))
	#print quoted_list
	query = "index=[%s]" % quoted_list
	user_snps_df = store.select('dummy', query)
	#TODO: print out SNPs that were NOT found in the database
	store.close()
	return user_snps_df


def write_user_snps_stats(path_output, user_snps, df):
	user_snps_stats_file = path_output+"/query_stats.out"
	snps_not_in_db = []
	for snp in user_snps.keys():
		if not (df.index == snp).any():
			snps_not_in_db.append(snp)
	if not len(snps_not_in_db)==0:
		print "Warning: %d SNPs not found in data base:" % len(snps_not_in_db)
		#print "List of user SNPs not found in data base:"
		print "\n".join(snps_not_in_db)
		#TODO: print list of SNPs not found to file
	print "Found %d out of %d SNPs in data base" % (df.shape[0], len(user_snps))
	df.to_csv(user_snps_stats_file, sep='\t', header=True, index=True,  mode='w')



def query_similar_snps(file_db, path_output, df, N_sample_sets, max_freq_deviation, max_distance_deviation, max_genes_count_deviation):
	user_snps_matrix_file = path_output+"/matrix.out"
	np.random.seed(1)
	n_attempts = 5

	store = pd.HDFStore(file_db, 'r')
	for i in xrange(len(df.index)): # pandas DF indecies is zero based like python
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

		#print (freq_low, freq_high)
		#print (gene_count_low, gene_count_high)
		#print (dist_low, dist_high)

		match_ID_old = None
		match_ID = None
		for i in xrange(n_attempts):
		    query_freq = '(freq_bin >= %s & freq_bin <= %s)' % (freq_low[i], freq_high[i])
		    query_gene_count = '(gene_count >= %s & gene_count <= %s)' % (gene_count_low[i], gene_count_high[i])
		    query_dist = '(dist_nearest_gene  >= %s & dist_nearest_gene  <= %s)' % (dist_low[i], dist_high[i])
		    
		    query = "%s & %s & %s" % (query_freq, query_gene_count, query_dist)
		    match_ID = store.select('dummy', query, columns=[]).index.values # return no columns --> only index
		    #df_matches = store.select('dummy', query)
		    
		    print "SNP: {%s} query #%d: found %d hits" % ("placeholder", i, len(match_ID))
		    if len(match_ID) < N_sample_sets:
		        match_ID_old = match_ID
		    else: #we have enough matches
		        break

		#df_matches.head(20)
		#print len(match_ID_old)
		#print len(match_ID)


		if len(match_ID) < N_sample_sets:
			print "******** Found SNP with too few matches; n_matches=%s" % len(match_ID)
		else:
			match_ID_uniq_new = np.setdiff1d(match_ID, match_ID_old, assume_unique=True) #Return the sorted, unique values in ar1 that are not in ar2
			#print len(match_ID_uniq_new)# validated: gives same result as print len(match_ID) - len(match_ID_old)
			n_elements_to_fill = N_sample_sets - len(match_ID_old)
			#print n_elements_to_fill
			match_ID_uniq_new_sample = np.random.choice(match_ID_uniq_new, size=n_elements_to_fill, replace=False, p=None) # sample uniformly from NEW matches
			match_ID_final = np.concatenate((match_ID_old, match_ID_uniq_new_sample))
			#print len(match_ID_final)

			with open(user_snps_matrix_file,'a') as f_handle:
			    np.savetxt(f_handle, np.insert(match_ID_final, 0, query_snpID), fmt="%s", newline="\t")
	

	store.close()





#TODO: check input variable types!
# check for integers ans strings
# check for distance and distance cutoff value: ONLY CERTAIN VALUES ALLOWED
arg_parser = argparse.ArgumentParser(description="Program to get background distribution matching user input SNPs on the following parameters {MAF, distance to nearest gene, gene density}")
arg_parser.add_argument("--user_snps_file", help="Path to file with user-defined SNPs", required=True) # TODO: make the program read from STDIN via '-'
arg_parser.add_argument("--output_dir", type=ArgparseAdditionalUtils.check_if_writable, help="Directory in which output files, i.e. random SNPs will be written", required=True)
arg_parser.add_argument("--distance_type", help="ld or kb", required=True)
arg_parser.add_argument("--distance_cutoff", help="r2, or kb distance", required=True)
arg_parser.add_argument("--N_sample_sets", type=int, help="Number of matched SNPs to retrieve", required=True) # 1000 - "Permutations?" TODO: change name to --n_random_snp_sets or --N
#TODO: add argument that describes if ABSOLUTE of PERCENTAGE deviation should be used
arg_parser.add_argument("--max_freq_deviation", type=int,help="Maximal deviation of SNP MAF bin [MAF +/- deviation]", default=5) # 5
arg_parser.add_argument("--max_distance_deviation", type=int, help="Maximal PERCENTAGE POINT deviation of distance to nearest gene [distance +/- %deviation])", default=5) # 20000
	#TODO: CHECK THAT max_distance_deviation > 1 %
arg_parser.add_argument("--max_genes_count_deviation", type=float, help="Maximal PERCENTAGE POINT deviation of genes in locus [gene_density +/- %deviation]", default=5) # 0.2
args = arg_parser.parse_args()


### CONSTANTS ###
#path_data = "/Users/pascaltimshel/snpsnap/data/step3/tmp" ## HARD CODED PATH!!
path_data = "/Users/pascaltimshel/snpsnap/data/step3" ## HARD CODED PATH!!
path_data = os.path.abspath(path_data) # make sure that trailing newline is removed. DELETE LATER!
prefix = args.distance_type + args.distance_cutoff

path_output = os.path.abspath(args.output_dir)

(file_db, file_meta) = locate_HDF5_data(path_data, prefix) # Locate DB files. TODO: make function more robust
user_snps = read_user_snps(args.user_snps_file) # Read input SNPs. Return dict
user_snps_df = lookup_user_snps(file_db, user_snps) # Query DB, return DF
write_user_snps_stats(path_output, user_snps, user_snps_df) # Report matches to DB and write stats file
print user_snps_df
query_similar_snps(file_db, path_output, user_snps_df, args.N_sample_sets, args.max_freq_deviation, args.max_distance_deviation, args.max_genes_count_deviation)


#matched_snp_sets,matched_snp_nearestgene,matched_snp_genes = get_matched_snps(observed_snps,random_snps,args.max_freq_deviation, allowed_min_frq, allowed_max_frq, args.output_snp_nr,args.max_distance_deviation, args.max_genes_count_deviation)
#write(observed_snps,matched_snp_sets,matched_snp_nearestgene,matched_snp_genes,args.output_snp_nr,args.working_dir)



