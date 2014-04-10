#! /usr/bin/env python2.7

import glob
import pdb
import sys
import collections
import os
import argparse

def makehash():
	return collections.defaultdict(makehash) 

# Function to read gene positions
def read_gene_info(infile):
	# ENSG00000125454 SLC25A19        17      -1 70780669 70797109 
	infile = open(infile,"r")
	lines = infile.readlines()
	info = makehash()
	info_red = makehash()
	for line in lines:
		words = line.strip().split()
		chr = words[2]
		if chr == "X":
			chr = "23"
		if chr == "Y":
			chr = "24"
		info[chr][words[4]] = words[0]
		info_red[words[0]]['sta'] = words[4]
		info_red[words[0]]['end'] = words[5]
	infile.close()
	return info,info_red

# Function that reads ld files and prints matches SNPs
def get_matched_snps(path,outfilename):

	outfile = open(outfilename,'w')
	ldfiles = glob.glob(path+"*.ld")
	for ldfile in ldfiles:

		matched_snps_boundaries = makehash()
	
		# Read all SNPs and their LD budies 
		infile = open(ldfile,'r')
		lines = infile.readlines()[1:]
		for line in lines:
			words = line.strip().split()
	
			if not words[2] in matched_snps_boundaries:
				matched_snps_boundaries[words[2]]['chr'] = int(words[0])
				matched_snps_boundaries[words[2]]['pos'] = int(words[1])
				matched_snps_boundaries[words[2]]['up'] = int(words[4])
				matched_snps_boundaries[words[2]]['down'] = int(words[4])
			else:
				if int(words[4]) < matched_snps_boundaries[words[2]]['up']:
					matched_snps_boundaries[words[2]]['up'] = int(words[4])
				if int(words[4]) > matched_snps_boundaries[words[2]]['down']:
					matched_snps_boundaries[words[2]]['down'] = int(words[4])
		infile.close()
	
		# Loop over matched SNPs and report gene density as observed SNP
		for matched_rsID in matched_snps_boundaries:
		
			genes_in_matched_locus = {}
		
			# Loop over all genes on chromosome
			# TODO Maybe sort and break
			matched_nearest_gene = "" 
			matched_nearest_gene_dist = float("inf")
			for tss in gene_info[str(matched_snps_boundaries[matched_rsID]['chr'])]:
	
				e = gene_info[str(matched_snps_boundaries[matched_rsID]['chr'])][tss] 
				end = gene_info_red[e]['end']
		
				# Mark if gene overlaps matched locus
				if (int(tss) > matched_snps_boundaries[matched_rsID]['up'] and int(tss) < matched_snps_boundaries[matched_rsID]['down']) or (int(end) > matched_snps_boundaries[matched_rsID]['up'] and int(end) < matched_snps_boundaries[matched_rsID]['down']) or (int(tss) < matched_snps_boundaries[matched_rsID]['up'] and int(end) > matched_snps_boundaries[matched_rsID]['down']):
					genes_in_matched_locus[e]= 1
					#pdb.set_trace()
		
				# Update nearest gene
				dist = abs( int(tss) - matched_snps_boundaries[matched_rsID]['pos'] )
				if dist < matched_nearest_gene_dist: 
					matched_nearest_gene = gene_info[str(matched_snps_boundaries[matched_rsID]['chr'])][tss] 
					matched_nearest_gene_dist = dist
		
			# Add nearest gene to genes in matched locus
			genes_in_matched_locus[matched_nearest_gene] = 1
		
			# Report distance to nearest gene
			matched_dist_to_nearest_gene = int(abs( matched_snps_boundaries[matched_rsID]['pos'] - int(gene_info_red[matched_nearest_gene]['sta'])))
		
			# Report gene density
			matched_gene_count = len(genes_in_matched_locus)
	
			tmp = ldfile.split("/")
			freq_bin = "-"
			if 'freq' in tmp[len(tmp)-1]:
				tmp1 = tmp[len(tmp)-1].split('freq')[1].split('-')
				freq_bin = tmp1[0]+"-"+tmp1[1]
	
			outfile.write("%s\t%s\t%s\t%s\t%s\t%s\n"%(matched_rsID,freq_bin,matched_dist_to_nearest_gene,matched_gene_count,matched_nearest_gene,",".join(genes_in_matched_locus.keys())))
	outfile.close()
	
	
# Variables
gene_information_file = "/home/projects/tp/data/mapping/biomart/ensg_mart_ensembl54_build36.tab" # Ensembl 54, HG16

#
# Parse arguments  
#
arg_parser = argparse.ArgumentParser(description="Parse plink output and construct loci")
arg_parser.add_argument("--ldfiles_prefix", help="Prefix to Plink .ldf files ('*' suffixed in above method)")
arg_parser.add_argument("--outfilename", help="Filename for outfile")
args = arg_parser.parse_args()

#
# Analysis
#
gene_info,gene_info_red = read_gene_info(gene_information_file)
get_matched_snps(args.ldfiles_prefix,args.outfilename)
