#!/usr/bin/env python2.7

import os
import sys
import random
import collections
import argparse
from queue import QueueJob,ArgparseAdditionalUtils

import pandas as pd

import time
import pdb

## Example calls:




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
		user_snps[words] = 1
	return user_snps

# Function to read in list of all randomized SNPs
def read_randomized_snps(random_snps_file,user_snps):
	random_snps = makehash()
	infile = open(random_snps_file,'r')
	lines = infile.readlines()
	infile.close()
	for line in lines:
		words = line.strip().split()
		if words[0] in user_snps: #NOTE: checks if rsID of random_snps exists in user_snps
			random_snps[words[1]][words[0]][words[2]][words[3]]['nearest_gene'] = words[4]
			random_snps[words[1]][words[0]][words[2]][words[3]]['genes'] = words[5]

	return random_snps





arg_parser = argparse.ArgumentParser(description="Program to get background distribution matching user input SNPs on the following parameters {MAF, distance to nearest gene, gene density}")
arg_parser.add_argument("--user_snps_file", help="Path to file with user-defined SNPs", required=True) # TODO: make the program read from STDIN via '-'
arg_parser.add_argument("--output_dir", type=ArgparseAdditionalUtils.check_if_writable, help="Directory in which output files, i.e. random SNPs will be written", required=True)
arg_parser.add_argument("--N_sample_sets", type=int, help="Number of matched SNPs to retrieve", required=True) # 1000 - "Permutations?" TODO: change name to --n_random_snp_sets or --N
arg_parser.add_argument("--frq_max_deviation", type=int,help="Percentage point deviation on either side of SNP frequency", default=5) # 5
arg_parser.add_argument("--margin_distance", type=int, help="Margin in distance to nearest gene (matched_dist < [observed distance + margin])", default=20000) # 20000
arg_parser.add_argument("--margin_genes_in_locus", type=float, help="Deviation of genes in locus", default=2) # 0.2
args = arg_parser.parse_args()


user_snps = read_user_snps(args.user_snps_file) # returns hash
random_snps = read_randomized_snps(args.random_snps_file,user_snps)
matched_snp_sets,matched_snp_nearestgene,matched_snp_genes = get_matched_snps(observed_snps,random_snps,args.frq_max_deviation, allowed_min_frq, allowed_max_frq, args.output_snp_nr,args.margin_distance, args.margin_genes_in_locus)
write(observed_snps,matched_snp_sets,matched_snp_nearestgene,matched_snp_genes,args.output_snp_nr,args.working_dir)



