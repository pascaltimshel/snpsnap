#!/usr/bin/env python2.7

# TODO: Add chr and position to gene files
# TODO: Limit to LD friends

#import re
import os
import sys
import math
import random
import pdb
import collections
from sets import Set
from random import choice
import argparse
sys.path.append('/home/projects/tp/tools/matched_snps/src')
from queue import QueueJob,ArgparseAdditionalUtils

# Function used to have dictionary of dictionaries
def makehash():
	return collections.defaultdict(makehash) 

# Function to return ordered neighboring frequency bins
def get_freq_neighbours(frq, frq_max_deviation,allowed_min_frq,allowed_max_frq):
	frq_max_deviation_up = frq_max_deviation
	frq_max_deviation_down = frq_max_deviation

	# Lower boundary 
	min_frq = max(allowed_min_frq,frq-frq_max_deviation_down)
	frq_max_deviation_up = frq_max_deviation_up + (frq_max_deviation - (frq-min_frq) ) # The term in parentheses adds the frequency bins that were lost on the lower end

	# Upper boundary
	max_frq = min(allowed_max_frq,frq+frq_max_deviation_up)
	frq_max_deviation_down = frq_max_deviation_down + (frq_max_deviation + (frq-max_frq) ) 
	min_frq = min(min_frq,frq-frq_max_deviation_down)

	# Makes freq list
	frq_down = range(min_frq,frq,1)
	frq_up = range(frq+1,max_frq+1,1)
	frq_list = [frq]
	for i in range(0,max(len(frq_down),len(frq_up)),1):
		if i<len(frq_up):
			frq_list.append(frq_up[i])
		if i<len(frq_down):
			frq_list.append(frq_down[(len(frq_down)-1)-i])
	return frq_list

# Function to read observed SNPs
def read_obs_snps(obs_snps_file,freq):
	observed_snps = makehash()
	infile = open(obs_snps_file,'r')
	lines = infile.readlines()
	for line in lines:
		words = line.strip().split('\t')
		observed_snps[words[0]]['freq'] = freq[words[0]]
		observed_snps[words[0]]['dist'] = int(words[2])
		observed_snps[words[0]]['numgenes'] = int(words[3])
		observed_snps[words[0]]['nearest_gene'] = words[4]
		observed_snps[words[0]]['genes'] = words[5]
	infile.close()
	return observed_snps

# Function to map frequency to percentile bin
def get_freq_bin(f):
	if f > 0.5:
		f = 1 - f	
	f_int = math.floor(f*float(100))
	bin = 0
	bins = range(0,50,freq_bin_size)
	for i in range(1,len(bins),1):
		if f_int >= bins[i-1] and f_int <= bins[i]:
			break
		else:
			bin += 1	
	return bin

# Function to read userdefined list of SNPs
def read_user_snps(user_snps_file,user_snps_file_snpcol,user_snps_file_sep):
	user_snps = {}
	infile = open(user_snps_file,'r')
	lines = infile.readlines()
	infile.close()
	#pdb.set_trace()
	if user_snps_file_sep == "tab": 
		user_snps_file_sep = "\t"
	elif user_snps_file_sep == "space": 
		user_snps_file_sep = "\s"
	for line in lines:
		words = line.strip().split(user_snps_file_sep)
		user_snps[words[user_snps_file_snpcol]] = 1
	return user_snps

# Function to read in list of all randomized SNPs
def read_randomized_snps(random_snps_file,user_snps):
	random_snps = makehash()
	infile = open(random_snps_file,'r')
	lines = infile.readlines()
	infile.close()
	for line in lines:
		words = line.strip().split()
		if words[0] in user_snps: 
			random_snps[words[1]][words[0]][words[2]][words[3]]['nearest_gene'] = words[4]
			random_snps[words[1]][words[0]][words[2]][words[3]]['genes'] = words[5]
	return random_snps

# Function to read in summary statiscs and bin SNPs into MAF percentiles
def read_freq(freq_file):
	infile = open(freq_file,'r')
	lines = infile.readlines()[1:]
	freq = {}
	for line in lines:
		words = line.strip().split()
		freq[words[1]] = float(words[4])
	infile.close()
	return freq

# Function that reads ld files and prints matched SNPs
def get_matched_snps(observed_snps,random_snps,frq_max_deviation, allowed_min_frq, allowed_max_frq, output_snp_nr, margin_distance, margin_genes_in_locus):
	matched_snps = {}
	matched_snp_nearestgene = {}
	matched_snp_genes = {}
	counter = 0
	for rsID in observed_snps:

		full_flag = 0

		# Allow +-2 percent. points deviation (take care of bourndaries)
		obs_freq_bin = get_freq_bin(observed_snps[rsID]['freq'])
		freq_bins = get_freq_neighbours(obs_freq_bin, frq_max_deviation, allowed_min_frq, allowed_max_frq)

		# Loop over SNPs in frequency bins
		matched_rsIDs  = []
		for freq in freq_bins:
			freq_bin = str(freq) + "-" + str(freq+1)
			freq_rsIDs = random_snps[freq_bin].keys()
			random.shuffle(freq_rsIDs)

			# Loop over distance to nearest gene
			for freq_rsID in freq_rsIDs:

				# Filter by distance to nearest gene
				dist = int(random_snps[freq_bin][freq_rsID].keys()[0])
				if dist < math.floor(observed_snps[rsID]['dist'] + margin_distance):

					# Filter by gene density
					count = int(random_snps[freq_bin][freq_rsID][str(dist)].keys()[0])
					if count >= math.floor(observed_snps[rsID]['numgenes'] - observed_snps[rsID]['numgenes']*margin_genes_in_locus) and count <= math.ceil(observed_snps[rsID]['numgenes'] + observed_snps[rsID]['numgenes'] *margin_genes_in_locus ):

						#count = len(random_snps[freq_bin][freq_rsID][str(dist)][str(count)]['genes'].split(',')) 
						matched_rsIDs.append(freq_rsID)

						# Save nearest gene and neighbour genes for matched snps
						matched_snp_nearestgene[freq_rsID] = random_snps[freq_bin][freq_rsID][str(dist)][str(count)]['nearest_gene']
						matched_snp_genes[freq_rsID] = random_snps[freq_bin][freq_rsID][str(dist)][str(count)]['genes']

						# Only save limited number of SNPs
						if len(matched_rsIDs) == output_snp_nr:
							full_flag = 1
				if full_flag:
					break

			if full_flag:
				break

		# For the given rsID, we now have all SNPs that we could sample
		matched_snps[rsID] = matched_rsIDs
	
		# Counter
		counter += 1
		print("%.2f" % ((counter/float(len(observed_snps)))*100))

	return matched_snps,matched_snp_nearestgene,matched_snp_genes

# Function to write out matched SNPs
def write(observed_snps,matched_snps,matched_snp_nearestgene,matched_snp_genes,output_snp_nr,working_dir):
	outfile = open(working_dir + "/"+str(output_snp_nr)+"matchedloci.csv",'w')

	# Write rows with meta data
	for field in ['rsID','freq','numgenes','dist','num_matched_snps']:
		counter = 0
		for rsID in observed_snps:
			counter += 1
			if field == 'rsID':
				outfile.write("%s"%(rsID))
			elif field == 'num_matched_snps': 
				outfile.write("%s"%(len(matched_snps[rsID])))
			else:
				outfile.write("%s"%(observed_snps[rsID][field]))
			if counter < len(observed_snps):
				outfile.write(",")
			else:
				outfile.write("\n")

	# Reformat matched SNP sets
	# FROM: observedSNP-> matchedSNP1, matchedSNP2, ...
	# TO: set1-> observedSNP1-> matchedSNP1, matchedSNP2, ...
	matched_snp_sets = {}
	small_sets = {}
	for i in range(0,output_snp_nr,1):
		matched_snp_sets[i] = {}
		for rsID in observed_snps:
			if i < len(matched_snps[rsID]):
				matched_snp_sets[i][rsID] = matched_snps[rsID][i]
			else:
				matched_snp_sets[i][rsID] = "NA"
				small_sets[rsID] = 1

	# Write out names of SNPs for which only a limited number of SNPs could be matched
	for rsID in small_sets:
		print("%s only %s SNPs (below requested %s SNPs)"%(rsID, len(matched_snps[rsID]), output_snp_nr))

	#pdb.set_trace()
	# Write SNPs to rsID file, and detailed set-specific files
	seen_in_set = {}
	for set in matched_snp_sets:
		set_outfile = open(working_dir + "/"+str(output_snp_nr)+"matchedsets/set" + str(set+1) + ".tab",'w')
		counter = 0
		seen_in_set[set] = {}
		for rsID in observed_snps:
			counter += 1
			matched_rsID = matched_snp_sets[set][rsID] 
			if matched_rsID != "NA" and matched_rsID not in seen_in_set[set]:
				outfile.write(matched_rsID)
				set_outfile.write("%s\t%s\t%s\n"%(matched_rsID,matched_snp_nearestgene[matched_rsID],matched_snp_genes[matched_rsID]))
				seen_in_set[set][matched_rsID] = 1
			else:
				# Find random SNP from list
				matched_rsID_backup = matched_rsID
				while (matched_rsID_backup in seen_in_set[set]) or matched_rsID_backup == "NA":
					matched_rsID_backup = choice(matched_snps[rsID])
				seen_in_set[set][matched_rsID_backup] = 1
				outfile.write(matched_rsID_backup)
				set_outfile.write("%s\t%s\t%s\n"%(matched_rsID_backup,matched_snp_nearestgene[matched_rsID_backup],matched_snp_genes[matched_rsID_backup]))
				
			if counter < len(observed_snps): 
				outfile.write(",")
			else:
				outfile.write("\n")
		set_outfile.close() 
	
	outfile.close()
		
# Fixed Variables
freq_file = "/home/projects/tp/data/hapmap/phase2/hapmap_CEU_r23a.frq"
freq_bin_size = 1
allowed_min_frq = 2 # Do not sample SNPs below this frequency
allowed_max_frq = 49 # Covers 49-50%

#
#Parse arguments
#
arg_parser = argparse.ArgumentParser(description="Get matched SNPs")
arg_parser.add_argument("--user_snps_file", help="Path to file with user-defined SNPs") 
arg_parser.add_argument("--user_snps_file_snpcol", help="SNP rsID column in file with user-defined SNPs") 
arg_parser.add_argument("--user_snps_file_sep", help="Separator in file with user-defined SNPs") 
arg_parser.add_argument("--random_snps_file", help="Path to pre-computed 'matchedsnps.csv' file") 
arg_parser.add_argument("--working_dir", type=ArgparseAdditionalUtils.check_if_writable, help="Directory in which observed 'observedsnps.csv' resides and output will be written")
arg_parser.add_argument("--output_snp_nr", type=int, help="Number of matched SNPs to retrieve") # 1000
arg_parser.add_argument("--frq_max_deviation", type=int,help="Percentage point deviation on either side of SNP frequency") # 5
arg_parser.add_argument("--margin_distance", type=int, help="Margin in distance to nearest gene (matched_dist < [observed distance + margin])") # 20000
arg_parser.add_argument("--margin_genes_in_locus", type=float, help="Deviation of genes in locus") # 0.2

args = arg_parser.parse_args()

#
# Make folder
#
if not os.path.isdir(args.working_dir + "/"+str(args.output_snp_nr)+"matchedsets"):
	os.makedirs(args.working_dir + "/"+str(args.output_snp_nr)+"matchedsets")

#
# Run analysis
#
freq = read_freq(freq_file)
obs_snps_file = args.working_dir + "/observedloci.tab" # Read observed loci
observed_snps = read_obs_snps(obs_snps_file,freq) 
user_snps = read_user_snps(args.user_snps_file,int(args.user_snps_file_snpcol),args.user_snps_file_sep)
random_snps = read_randomized_snps(args.random_snps_file,user_snps)
matched_snp_sets,matched_snp_nearestgene,matched_snp_genes = get_matched_snps(observed_snps,random_snps,args.frq_max_deviation, allowed_min_frq, allowed_max_frq, args.output_snp_nr,args.margin_distance, args.margin_genes_in_locus)
write(observed_snps,matched_snp_sets,matched_snp_nearestgene,matched_snp_genes,args.output_snp_nr,args.working_dir)

