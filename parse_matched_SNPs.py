#! /usr/bin/env python2.7

import glob
import pdb
import sys
import collections
import os
import argparse
import re #Pascal


def makehash():
	return collections.defaultdict(makehash) 

# Function to read gene positions
def read_gene_info(infile):
	# ENSG00000125454 SLC25A19        17      -1 70780669 70797109

	# Ensembl Gene ID,Transcript Start (bp),Transcript End (bp),Strand,Gene Start (bp),Chromosome Name,Gene End (bp)
	# ENSG00000239156,20113,20230,1,20113,GL000228.1,20230
	# ENSG00000238762,22673,22791,1,22673,GL000228.1,22791
	# ENSG00000240442,21191674,21191827,1,21191674,18,21191827
	infile = open(infile,"r")
	lines = infile.readlines()[1:] #REMEMBER: skip head line
	info = makehash()
	info_red = makehash()
	chr_pattern = re.compile('^([1-9]|1[0-9]|2[0-4]|[X,Y])$', re.IGNORECASE) # this should match the numeric range 1-24 and X,Y. Match case insensitive.
	for line in lines:
		words = line.strip().split(',') # comma separated file
		#chr = words[2]
		chr = words[5]

		# IMPORTANT: there exists strange chr names such as GL000228.1, LRG_13 etc...
		if not chr_pattern.match(chr):
			continue 
		# Convert everything to numeric to enable comparison afterwards
		if chr == "X":
			chr = "23"
		if chr == "Y":
			chr = "24"

		#info[chr][words[4]] = words[0] #@TODO test if start exists
		info[chr][words[0]] = 1
		#info_red[words[0]]['sta'] = words[4] # old ENSEMBLE Tune
		#info_red[words[0]]['end'] = words[5] # old ENSEMBLE Tune
		info_red[words[0]]['sta'] = words[1] # ===> Transcript Start (bp)
		info_red[words[0]]['end'] = words[2] # ===> Transcript End (bp)
	infile.close()
	return info,info_red

# Function that reads ld files and prints matches SNPs
def get_matched_snps(path,outfilename):
	#TODO: gene_info,gene_info_red are NOT parsed as arguments to this function.
	#	- instead they are global variables. BAD PRACTICE!!!! 
	# gene_info == info
	# gene_info_red == info_red
	outfile = open(outfilename,'w')
	ldfiles = glob.glob(path+"*.ld")
	for ldfile in ldfiles:

		matched_snps_boundaries = makehash()
	
		# Read all SNPs and their LD budies 
		infile = open(ldfile,'r')
		lines = infile.readlines()[1:] #skipping header
		for line in lines:
			words = line.strip().split()
			##@TODO insert data snippet
			if not words[2] in matched_snps_boundaries:
				# words[2] == input SNP?
				# CHR_A         BP_A        SNP_A  CHR_B         BP_B        SNP_B           R2
     			# 1      1011095   rs11810785      1      1011095   rs11810785            1
     			# 1      1011095   rs11810785      1      1025301    rs9442400      0.61996
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
			snp_chr = matched_snps_boundaries[matched_rsID]['chr'] # NB. integer!
			snp_position = matched_snps_boundaries[matched_rsID]['pos'] # NB. integer!

			genes_in_matched_locus = {} # orig
			#genes_in_matched_locus = 0 ## tune and pascal counter. Pascal outcomment again 04-17-2014
		
			# Loop over all genes on chromosome
			# TODO Maybe sort and break
			matched_nearest_gene = "" 
			matched_nearest_gene_dist = float("inf")
			#for tss in gene_info[str(matched_snps_boundaries[matched_rsID]['chr'])]:
			#pdb.set_trace()
			
			for gene in gene_info[str(snp_chr)]:
				# matched_snps_boundaries[matched_rsID] ===> "original input snp"
				# str(matched_snps_boundaries[matched_rsID]['chr']) ===> chromosome number
				# e.g. gene_info['5'] returns all ENSEMBL IDs in chromosome 5.

				# gene is a key in hash, i.e. a ENSEMBL ID string. gene_info[] is a hash
				#tss is transcription start site
				tss = gene_info_red[gene]['sta']

				#e = gene_info[str(matched_snps_boundaries[matched_rsID]['chr'])][tss] 
				#end = gene_info_red[e]['end']
				end = gene_info_red[gene]['end']
		
				# Mark if gene overlaps matched locus
				##@DOC We cover four possible scenarios: 
				if (int(tss) > matched_snps_boundaries[matched_rsID]['up'] and int(tss) < matched_snps_boundaries[matched_rsID]['down']) \
				or (int(end) > matched_snps_boundaries[matched_rsID]['up'] and int(end) < matched_snps_boundaries[matched_rsID]['down']) \
				or (int(tss) < matched_snps_boundaries[matched_rsID]['up'] and int(end) > matched_snps_boundaries[matched_rsID]['down']):
					genes_in_matched_locus[gene]= 1
					#genes_in_matched_locus += 1 # tune and pascal. Pascal outcomment 04-17-2014
					
					#pdb.set_trace()
		
				# Update nearest gene
				dist = abs( int(tss) - snp_position ) #
				if dist < matched_nearest_gene_dist: 
					#matched_nearest_gene = gene_info[str(matched_snps_boundaries[matched_rsID]['chr'])][tss] # outcommented by pascal and Tune
					matched_nearest_gene = gene # pascal new, 04-17-2014. Save ENSEMBLE ID of nearest gene. Saves gene name in correct scope
					matched_nearest_gene_dist = dist
		
			# Add nearest gene to genes in matched locus. 
			# PASCAL NOTE: this ensures that there is always at least ONE gene in the locus
			# genes_in_matched_locus[matched_nearest_gene] = 1 # orig. OUTCOMMENTED by Tune and Pascal
			#pdb.set_trace()
			# Report distance to nearest gene
			#@DOC Distance is measured as distance to nearest start site
			#matched_dist_to_nearest_gene = int(abs( matched_snps_boundaries[matched_rsID]['pos'] - int(gene_info_red[gene]['sta']))) # pascal and Tune - PASCAL NOTE: CHECK IF THIS IS CORRECT!
			#print "DEBUG-message | chr = " + str(matched_snps_boundaries[matched_rsID]['chr'])
			#print "DEBUG-message | gene = " + gene
			#print "DEBUG-message | position of nearest gene (gene_info_red[gene]['sta']) = " + gene_info_red[gene]['sta']
			#print "DEBUG-message | gene_info_red[matched_nearest_gene]['sta'] =" + gene_info_red[matched_nearest_gene]['sta']
			matched_dist_to_nearest_gene = int(abs( snp_position - int(gene_info_red[matched_nearest_gene]['sta']))) # original - works?
		


			# Report gene density
			matched_gene_count = len(genes_in_matched_locus)
	
			tmp = ldfile.split("/")
			freq_bin = "-"
			if 'freq' in tmp[len(tmp)-1]:
				tmp1 = tmp[len(tmp)-1].split('freq')[1].split('-')
				freq_bin = tmp1[0]+"-"+tmp1[1]
	
			#outfile.write("%s\t%s\t%s\t%s\t%s\t%s\n"%(matched_rsID,freq_bin,matched_dist_to_nearest_gene,genes_in_matched_locus,matched_nearest_gene,",".join(genes_in_matched_locus.keys()))) # pascal and tune style
			#outfile.write("%s\t%s\t%s\t%s\t%s\t%s\n"%(matched_rsID,freq_bin,matched_dist_to_nearest_gene,matched_gene_count,matched_nearest_gene,",".join(genes_in_matched_locus.keys()))) # orig - works, but needed extension
			
			#rs201245847     9-10    49791307        1               ENSG00000212587
			
			#1=rsID
			#2=freq_bin
			#3=chromosome number
			#4=position of rsID
			#5=gene count in matched locus (density)
			#6=dist to nearest gene
			#7=nearest_gene ENSEMBL_ID (alway present)
			#8=genes in matches locus, multiple ENSEMBL IDs

			outfile.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\n".format( \
				matched_rsID, \
				freq_bin, \
				snp_chr, \
				snp_position, \
				matched_gene_count, \
				matched_dist_to_nearest_gene, \
				matched_nearest_gene, \
			",".join(genes_in_matched_locus.keys()) )) # pascal - with added extension
				
			# print '<a href="%(url)s">%(url)s</a>' % {'url': my_url}
			# print('<a href="{0}">{0}</a>'.format(my_url))
	outfile.close()
	
	
# Variables
#gene_information_file = "/home/projects/tp/data/mapping/biomart/ensg_mart_ensembl54_build36.tab" # Ensembl 54, HG16
# ENSG00000125454 SLC25A19        17      -1 70780669 70797109
# ENSG00000163328 GPR155  2       -1 175004621 175060068
# ENSG00000167555 ZNF534  19      1 57592933 57647004
# ENSG00000156976 EIF4A2  3       1 187984055 187990377
gene_information_file="/home/projects/tp/childrens/snpsnap/data/misc/ensg_mart_ensembl64_buildGRCh37.p5.tab"
# Ensembl Gene ID,Transcript Start (bp),Transcript End (bp),Strand,Gene Start (bp),Chromosome Name,Gene End (bp)
# ENSG00000239156,20113,20230,1,20113,GL000228.1,20230
# ENSG00000238762,22673,22791,1,22673,GL000228.1,22791
# ENSG00000240442,21191674,21191827,1,21191674,18,21191827
# ENSG00000242521,21868882,21868958,1,21868882,18,21868958
# ENSG00000244478,63142749,63142836,1,63142749,18,63142836
#@TODO: update biomart file. Download via web. Use scp
#
# Parse arguments  
#
arg_parser = argparse.ArgumentParser(description="Parse plink output and construct loci")
arg_parser.add_argument("--ldfiles_prefix", help="Prefix to Plink .ld files ('*' suffixed in above method)")
arg_parser.add_argument("--outfilename", help="Filename for outfile")
args = arg_parser.parse_args()

#
# Analysis
#
gene_info,gene_info_red = read_gene_info(gene_information_file) # Finds position of each gene
# saves hashes global

get_matched_snps(args.ldfiles_prefix,args.outfilename)
