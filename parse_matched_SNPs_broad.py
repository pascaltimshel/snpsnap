#! /usr/bin/env python2.7

import glob
import pdb
import sys
import collections
import os
import argparse
import re #Pascal

import time

import pplaunch
import pphelper
import pplogger


def makehash():
	return collections.defaultdict(makehash) 

# Function to read frq file
def read_file_frq(file_frq):
	print "Reading file_frq file into hashes: {}".format(file_frq)
	### File snippet
	### NB: ALL SNPs (rsIDs) should be unique at this stage
	# CHR                                  SNP   A1   A2          MAF  NCHROBS
	#   1                              1:11008    G    C      0.08847     1006
	#   1                              1:11012    G    C      0.08847     1006
	#   1                              1:13110    A    G      0.05666     1006
	#   1                          rs201725126    G    T       0.1869     1006
	#   1                          rs200579949    G    A       0.1869     1006
	#   1                              1:13273    C    G       0.1471     1006
	#   1                              1:14464    T    A       0.1859     1006
	#   1                              1:14599    A    T        0.161     1006
	#   1                              1:14604    G    A        0.161     1006
	snp_maf_dict = {}
	with open(file_frq, 'r') as f:
		for line in f: # reading line by line
			fields = line.strip().split()
			SNP = fields[1]
			MAF = fields[4]
			
			### Additional check - REMEMBER: all rsID should be unique at this point.
			if SNP in snp_maf_dict: # we have seen this rsID before
				print "Have seen rsID={SNP} before. Old MAF will be overwriten. Now you know... THIS SHOULD NOT HAPPEN THOUGH. Check the plink .frq file for duplicate rsIDs."

			### Saving MAF in dict
			snp_maf_dict[SNP] = MAF

	print "Done reading file_frq"
	return snp_maf_dict


# Function to read gene positions
def read_gene_info(infile):
	print "Reading ENSEMBL file into hashes"
	### File snippet - SNPsnap_production_v1
	# Ensembl Gene ID,Transcript Start (bp),Transcript End (bp),Strand,Gene Start (bp),Chromosome Name,Gene End (bp)
	# ENSG00000239156,20113,20230,1,20113,GL000228.1,20230
	# ENSG00000238762,22673,22791,1,22673,GL000228.1,22791
	# ENSG00000240442,21191674,21191827,1,21191674,18,21191827

	### File snippet - NEW FEBRUARY 2015 - SNPsnap_production_v2
	# Ensembl Gene ID,Chromosome Name,Gene Start (bp),Gene End (bp),Strand,Gene type,HGNC symbol,Source (gene),Status (gene)
	# ENSG00000261657,HG991_PATCH,66119285,66465398,1,protein_coding,SLC25A26,havana,KNOWN
	# ENSG00000223116,13,23551994,23552136,-1,miRNA,,ensembl,NOVEL
	### COLS (zero based enumeration)
	# 0: Ensembl Gene ID
	# 1: Chromosome Name
	# 2: Gene Start (bp)
	# 3: Gene End (bp)
	# 4: Strand
	# 5: Gene type
	# 6: HGNC symbol
	# 7: Source (gene)
	# 8: Status (gene)
	infile = open(infile,"r")
	lines = infile.readlines()[1:] #REMEMBER: skip head line
	gene_info = makehash()
	gene_info_red = makehash()
	chr_pattern = re.compile('^([1-9]|1[0-9]|2[0-4]|[X,Y])$', re.IGNORECASE) # this should match the numeric range 1-24 and X,Y. Match case insensitive.
	for line in lines:
		words = line.strip().split(',') # comma separated file
		
		ensembl_gene_id = words[0]
		chromosome = words[1]
		gene_start = words[2]
		gene_end = words[3]
		strand = words[4]
		gene_type = words[5]
		hgnc_symbol = words[6]

		# IMPORTANT: there exists strange chromosome names such as GL000228.1, LRG_13 etc...
		if not chr_pattern.match(chromosome):
			continue 

		### *IMPORTANT* the ENSEMBL file uses "X"/"Y" for the sex chromosome. PLINK uses numeric codes 23/34.
		### Failing to do this conversion resulted *BUG* in the collection file for all X-chromosome variants!
		### DATE OF FIX: 29th July 2015
		# Convert Ensembl format X-chromosome to numeric codes used by PLINK.
		if chromosome == "X":
			chromosome = "23"
		if chromosome == "Y":
			chromosome = "24"

		############# Saving ENSEMBLE ID in dict ###################
		gene_info[chromosome][ensembl_gene_id] = 1

		############# Saving gene "METADATA" ###################
		gene_info_red[ensembl_gene_id]['gene_type'] = gene_type # we are looking for "protein_coding" later in the script
		gene_info_red[ensembl_gene_id]['hgnc_symbol'] = hgnc_symbol

		########################## USING TRANSCRIPTION START/END ######################
		### OBS: that there may be many different Transcript Start/End FOR THE SAME ENSEMBL ID
		### ----> SEE 'exp_gene_definition.txt' for details
		
		#if ensembl_gene_id == 'ENSG00000176771': pdb.set_trace()
		########################## USING GENE START/END ######################
		if strand == '1': # Strand is FORWARD
			gene_info_red[ensembl_gene_id]['sta'] = int(gene_start) # ===> Gene Start (bp)
			gene_info_red[ensembl_gene_id]['end'] = int(gene_end) # ===> Gene End (bp)
		elif strand == '-1': # Strand is REVERSE - then START should be END by ENSEMBL convention
			gene_info_red[ensembl_gene_id]['sta'] = int(gene_end) # ===> Gene End (bp)
			gene_info_red[ensembl_gene_id]['end'] = int(gene_start) # ===> Gene Start (bp)
		else:
			print "Warning: strange 'Strand' column entry in ENSEMBL file. Expected '1' or '-1' got [%s]. The below shows the full line:\n%s" % ( strand, line )
			#TODO: make some exeption or print
			# Currently we skip genes that do have stran '1' or '-1'
			# This is OK since I checked this: 
			#	cut -d',' -f4 ensg_mart_ensembl64_buildGRCh37.p5.tab | egrep -v '(-1)|(1)'
			# 	--> gives only "Strand"

	infile.close()
	print "done reading ENSEMBL file"

	return gene_info,gene_info_red

# Function that reads ld files and prints matches SNPs
def get_matched_snps(path,outfilename):
	#TODO: gene_info,gene_info_red are NOT parsed as arguments to this function.
	#	- instead they are global variables. BAD PRACTICE!!!! 
	# gene_info == gene_info
	# gene_info_red == gene_info_red
	outfile = open(outfilename,'w')
	# outfile = open(outfilename,'w', buffering=0) # JUNE 18 2014 - only for TEST - do not use without buffer
	ldfiles = glob.glob(path+"*.ld")
	for ldfile in ldfiles:
		print "Running ldfile={}".format(ldfile)

		matched_snps_boundaries = makehash()
	
		# Setting freq_bin
		# example:  ...long_path/freq1-2-part0-10000.ld
		filename_ld = os.path.basename(ldfile) # gives e.g. freq1-2-part0-10000.ld
		freq_bin = '??'
		if 'freq' in filename_ld:
			tmp1 = filename_ld.split('freq')[1] # gives e.g. 1-2-part0-10000.ld
			freq_bin = tmp1.split('-')[0] # gives e.g. 1
		else:
			print "Warning: unknow ldfile name format. Cannot set freq_bin. Check source code"


		### Count the number of lines in the file
		n_lines_ldfile = sum(1 for line in open(ldfile,'r')) # this is pretty fast (only a bit slower than "wc -l"). 3.5 sec for a 1 GB file

		time_start_loop = time.time()

		print "Readings all SNPs and finding their LD budies (matched_snps_boundaries)"
		# Read all SNPs and their LD budies
		with open(ldfile, 'r') as infile:
			next(infile) # SKIPPING THE FIRST LINE!
			for line_no, line in enumerate(infile, start=1):
				
				### Some stats
				if line_no % 100000 == 0:
					time_elapsed_loop = time.time() - time_start_loop # <type 'float'>
					print "Main loop - looping over LD-file | #{line_no}/#{n_lines} | {pct_complete:.2f} % done | {sec:.2f} sec [{min:.2f} min]".format(line_no=line_no, n_lines=n_lines_ldfile, pct_complete=(line_no/float(n_lines_ldfile))*100, sec=time_elapsed_loop, min=time_elapsed_loop/60)
				
				### Split and process
				words = line.strip().split()
				CHR_A = words[0]
				BP_A = words[1]
				SNP_A = words[2]
				CHR_B = words[3]
				BP_B = words[4]
				SNP_B = words[5]

				if not SNP_A in matched_snps_boundaries:
					# SNP_A == input SNP?
					# CHR_A         BP_A        SNP_A  CHR_B         BP_B        SNP_B           R2
	     			# 1      1011095   rs11810785      1      1011095   rs11810785            1
	     			# 1      1011095   rs11810785      1      1025301    rs9442400      0.61996
					matched_snps_boundaries[SNP_A]['chr'] = int(CHR_A) # Chromosomes ARE ALL NUMERIC --> X chromosome is assigned numeric code n+1
					matched_snps_boundaries[SNP_A]['pos'] = int(BP_A)
					matched_snps_boundaries[SNP_A]['up'] = int(BP_B)
					matched_snps_boundaries[SNP_A]['down'] = int(BP_B)

					############## NEW JUNE 18 2014 ###############
					matched_snps_boundaries[SNP_A]['ld_buddies'] = 0 # first time we see the SNP the buddy is with itself
				else:
					matched_snps_boundaries[SNP_A]['ld_buddies'] += 1 # we count the number of ld_buddies
					if int(BP_B) < matched_snps_boundaries[SNP_A]['up']:
						matched_snps_boundaries[SNP_A]['up'] = int(BP_B)
					if int(BP_B) > matched_snps_boundaries[SNP_A]['down']:
						matched_snps_boundaries[SNP_A]['down'] = int(BP_B)
			
		
		# Loop over matched SNPs and report gene density as observed SNP
		#for matched_rsID in matched_snps_boundaries: # <<<<--- THIS unsorted loop was used for generating 1KG_snpsnap_production_v1 data on CBS (the parse_matched_SNPs.py) was run around June 20 (06/20/2014).
		# ^^ It is impractical printing out the SNPs in 'random' order for each bin. If you sort on the matched_rsID (rsID) you should get SNP files with rsID in the same order. Then you can use 'cut' and other unix tools
		# NB: the sorting should be ok. The freq1-2 bin have around 1 Million SNPs, which needs to be sorted
		# OBS: consider using collections.OrderedDict() which remembers the order in which the elements have been inserted
		#	----> no do not do that. Sorting is more stable because we do not have to reply on the order in which the SNPs is inserted.
		print "sorting keys of matched_snps_boundaries"
		matched_snps_boundaries_sorted_keys = sorted(matched_snps_boundaries.keys())
		print "DONE sorting keys of matched_snps_boundaries"


		count_total = len(matched_snps_boundaries_sorted_keys)
		time_start_loop = time.time()

		for count_now, matched_rsID in enumerate(matched_snps_boundaries_sorted_keys, start=1): #

			### Some stats
			if count_now % 1000 == 0:
				time_elapsed_loop = time.time() - time_start_loop # <type 'float'>
				print "Main loop - looping over Matched SNPs | #{count_now}/#{count_total} | {pct_complete:.2f} % done | {sec:.2f} sec [{min:.2f} min]".format(count_now=count_now, count_total=count_total, pct_complete=(count_now/float(count_total))*100, sec=time_elapsed_loop, min=time_elapsed_loop/60)
			

			### processing
			snp_chr = matched_snps_boundaries[matched_rsID]['chr'] # *TYPE=integer* [all Chromosomes are NUMERIC, converted by PLINK]
			snp_position = matched_snps_boundaries[matched_rsID]['pos'] # *TYPE=integer*
			snp_maf = snp_maf_dict[matched_rsID] #snp_maf_dict.get(matched_rsID, '') # We could also use .get() method so the script does not crash if the the SNP for some weird reason did not exist in the .frq file

			genes_in_matched_locus = {} # orig
		
			matched_nearest_gene = "" 
			matched_nearest_gene_dist = float("inf")
			
			### NEW JUNE 18 2014 ########
			matched_nearest_gene_located_within = "" 
			matched_nearest_gene_dist_located_within = float("inf")

			########################### NEW FEBRUARY 26 2015 - protein coding ######################
			## NOTE: we need to account for both types of distances [nearest and located_within] to calculate the "snpsnap distance"
			# nearest gene #
			matched_nearest_gene_protein_coding = "" 
			matched_nearest_gene_dist_protein_coding = float("inf")
			# nearest gene located_within #
			matched_nearest_gene_located_within_protein_coding = "" 
			matched_nearest_gene_dist_located_within_protein_coding = float("inf")
			#######################################################################


			########################### NEW FEBRUARY 26 2015 - flag for SNP within gene ######################
			flag_snp_within_gene = False
			flag_snp_within_gene_protein_coding = False

			# Loop over all genes on chromosome
			# TODO: sort the genes. Running the loop in a sorted order gives MORE RELIABLE results (at least when debugging etc.)
			#	---> Pascal likes sorted dicts...
			# OBS: consider using collections.OrderedDict() which remembers the order in which the elements have been inserted
			#	----> Yes use this. Do not sort this has inside another for loop. That will be waay to slow.
			for gene in gene_info[str(snp_chr)]: # e.g. gene_info['5'] returns all ENSEMBL IDs in chromosome 5.

				# gene is a key in hash, i.e. a ENSEMBL ID string. gene_info[] is a hash
				#gene_start is transcription start site
				gene_start = gene_info_red[gene]['sta'] # This should be an integer
				gene_end = gene_info_red[gene]['end'] # This should be an integer

				gene_type = gene_info_red[gene]['gene_type']
		
				# Mark if gene overlaps matched locus
				##@DOC We cover four possible scenarios: 
				# 1. line: gene START is within locus. this applies both to forward and reverse genes
				# 2. line: gene END is within locus. this applies both to forward and reverse genes
				# 3. line: gene extends through locus. gene is on FORWARD strand (gene_start < gene_end)
				# 4. line: gene extends through locus. gene is on REVERSE strand (gene_start > gene_end)
				# NB: read_gene_info() sets the gene gene_start and gene_end correctly according the the ENSEMBL convention "strand" information
				if (int(gene_start) > matched_snps_boundaries[matched_rsID]['up'] and int(gene_start) < matched_snps_boundaries[matched_rsID]['down']) \
				or (int(gene_end) > matched_snps_boundaries[matched_rsID]['up'] and int(gene_end) < matched_snps_boundaries[matched_rsID]['down']) \
				or (int(gene_start) < matched_snps_boundaries[matched_rsID]['up'] and int(gene_end) > matched_snps_boundaries[matched_rsID]['down']) \
				or (int(gene_end) < matched_snps_boundaries[matched_rsID]['up'] and int(gene_start) > matched_snps_boundaries[matched_rsID]['down']):
					genes_in_matched_locus[gene]= 1
				
		
				############################ FINDING NEAREST GENE AND DIST ########################
				# Update nearest gene
				dist = abs( int(gene_start) - snp_position ) #
				
				if dist < matched_nearest_gene_dist: 
					matched_nearest_gene = gene 
					matched_nearest_gene_dist = dist # this is dist_nearest_gene
				
				### NEW FEB 2015 - PROTEIN CODING
				if (dist < matched_nearest_gene_dist_protein_coding) and (gene_type == "protein_coding"):
					matched_nearest_gene_protein_coding = gene
					matched_nearest_gene_dist_protein_coding = dist


				################ NEW JUNE 18 2014 - FINDING NEAREST GENE DIST WITHIN #############
				## 1. gene_start <= snp_position <= gene_end | ===> SNP position within gene on FORWARD strand
				## 2. gene_end <= snp_position <= gene_start | ===> SNP position within gene on REVERSE strand
				# NB: you could "merge" the nested 'if statement' by using "and". 
				# I chose a nested if statement for code readability
				if (gene_start <= snp_position <= gene_end) \
				or (gene_end <= snp_position <= gene_start): # if condition is true ===> SNP position is inside gene
					if dist < matched_nearest_gene_dist_located_within: # if condition in true ===> distance to current gene is the smallest seen so far
						flag_snp_within_gene = True # setting flag True - this could also be placed before "if dist < matched_nearest_gene_dist_located_within"
						matched_nearest_gene_located_within = gene
						matched_nearest_gene_dist_located_within = dist
					
					### NEW FEB 2015 - PROTEIN CODING
					if (dist < matched_nearest_gene_dist_located_within_protein_coding) and (gene_type == "protein_coding"):
						flag_snp_within_gene_protein_coding = True # setting flag True
						matched_nearest_gene_located_within_protein_coding = gene
						matched_nearest_gene_dist_located_within_protein_coding = dist



			# Report gene density
			matched_gene_count = len(genes_in_matched_locus)
			

			################ NEW JUNE 18 2014 - WRITE OUT #############

			#1=rsID
			#2=freq_bin
			#3=chromosome number of rsID
			#4=position of rsID
			#5=gene count in matched locus
			#6=dist to nearest gene - SNPSNAP DISTANCE (NEW!)
			#7=dist to nearest gene
			#8=dist to nearest gene LOCATED WITHIN (NEW!)
			#9=boundary_upstream
			#10=boundary_downstream
			#11=nearest_gene SNPSNAP (NEW!)
			#12=nearest_gene
			#13=nearest_gene LOCATED WITHIN (may be empty) (NEW!)
			#14=ld buddies count (NEW!)
			#15=genes in matches locus, multiple ENSEMBL IDs

			####### NOW FIND the "snpsnap" distance and ENSEMBL gene:
			## "snpsnap" gene distance: 
			## 1) distance to gene where SNP is located within the gene has highest precedence. (matched_nearest_gene_dist_located_within)
			## 2) If the SNP is not located within a gene, then use the distance to the nearest gene (matched_nearest_gene_dist)
			
			## Initialize snpsnap distance variables
			matched_nearest_gene_snpsnap = ""
			matched_nearest_gene_dist_snpsnap = float("inf") # this is just one way to initialize the variable. You could also use e.g None

			if matched_nearest_gene_dist_located_within != float("inf"): # if matched_nearest_gene_dist_located_within is NOT float('inf') then the SNP is located within a gene
				matched_nearest_gene_snpsnap = matched_nearest_gene_located_within
				matched_nearest_gene_snpsnap_HGNC_symbol = gene_info_red[matched_nearest_gene_snpsnap]['hgnc_symbol'] # NEW FEB 2015
				matched_nearest_gene_dist_snpsnap = matched_nearest_gene_dist_located_within
			else: # SNP is not located within a gene
				matched_nearest_gene_snpsnap = matched_nearest_gene
				matched_nearest_gene_snpsnap_HGNC_symbol = gene_info_red[matched_nearest_gene_snpsnap]['hgnc_symbol'] # NEW FEB 2015
				matched_nearest_gene_dist_snpsnap = matched_nearest_gene_dist

			###  <------ NEW FEB 2015 | finding nearest protein_coding gene using snpsnap distance ------>  ####
			## Initializing
			matched_nearest_gene_snpsnap_protein_coding = ""
			matched_nearest_gene_dist_snpsnap_protein_coding = float("inf")
			### Determine snpsnap distance
			if matched_nearest_gene_dist_located_within_protein_coding != float("inf"):
				matched_nearest_gene_snpsnap_protein_coding = matched_nearest_gene_located_within_protein_coding
				matched_nearest_gene_snpsnap_protein_coding_HGNC_symbol = gene_info_red[matched_nearest_gene_snpsnap_protein_coding]['hgnc_symbol'] # NEW FEB 2015
				matched_nearest_gene_dist_snpsnap_protein_coding = matched_nearest_gene_dist_located_within_protein_coding
			else: 
				matched_nearest_gene_snpsnap_protein_coding = matched_nearest_gene_protein_coding
				matched_nearest_gene_snpsnap_protein_coding_HGNC_symbol = gene_info_red[matched_nearest_gene_snpsnap_protein_coding]['hgnc_symbol'] # NEW FEB 2015
				matched_nearest_gene_dist_snpsnap_protein_coding = matched_nearest_gene_dist_protein_coding

			## FEATURE NEW FEB 2015
			#OK - matched_nearest_gene_dist_snpsnap_protein_coding | dist
			#OK - matched_nearest_gene_snpsnap_protein_coding | ENSEMBL symbol
			#OK - matched_nearest_gene_snpsnap_protein_coding_HGNC_symbol | HGNC symbol
			#OK - matched_nearest_gene_snpsnap_HGNC_symbol | HGNC symbol
			#OK - flag_snp_within_gene | flag
			#OK - flag_snp_within_gene_protein_coding | flag
			#OK - snp_maf

			#TODO: 
			# - consider printing 'NA' instead of nothing if genes_in_matched_locus is empty.
			# - this will give a nicer human readble output
			# - both R (na.strings = "NA") and pandas will handle this as a missing value by default 

			# IMPORTANT: 
			# - REMEMBER THAT THE NUMBER OF COLUMS MUST BE UPDATED IN THE VALIDATION IN run_parse_matched_SNPs.py
			# - First column MUST be rs_ID
			### NEW FEB 2015 - added 6 columns [HGNC_snpsnap; dist+gene+HGNC for protein coding; 2x SNP location flags]
			outfile.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}\t{10}\t{11}\t{12}\t{13}\t{14}\t{15}\t{16}\t{17}\t{18}\t{19}\t{20}\t{21}\n".format( \
				matched_rsID, \
				freq_bin, \
				snp_maf, \
				snp_chr, \
				snp_position, \
				matched_gene_count, \
				matched_nearest_gene_dist_snpsnap, \
				matched_nearest_gene_dist_snpsnap_protein_coding, \
				matched_nearest_gene_dist, \
				matched_nearest_gene_dist_located_within, \
				matched_snps_boundaries[matched_rsID]['up'], \
				matched_snps_boundaries[matched_rsID]['down'], \
				matched_nearest_gene_snpsnap, \
				matched_nearest_gene_snpsnap_protein_coding, \
				matched_nearest_gene, \
				matched_nearest_gene_located_within, \
				matched_nearest_gene_snpsnap_HGNC_symbol, \
				matched_nearest_gene_snpsnap_protein_coding_HGNC_symbol, \
				matched_snps_boundaries[matched_rsID]['ld_buddies'], \
				flag_snp_within_gene, \
				flag_snp_within_gene_protein_coding, \
			";".join(genes_in_matched_locus.keys()) )) # pascal - with added extension

			### *BEFORE* FEB 2015
			# outfile.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}\t{10}\t{11}\t{12}\t{13}\t{14}\n".format( \
			# 	matched_rsID, \
			# 	freq_bin, \
			# 	snp_chr, \
			# 	snp_position, \
			# 	matched_gene_count, \
			# 	matched_nearest_gene_dist_snpsnap, \
			# 	matched_nearest_gene_dist, \
			# 	matched_nearest_gene_dist_located_within, \
			# 	matched_snps_boundaries[matched_rsID]['up'], \
			# 	matched_snps_boundaries[matched_rsID]['down'], \
			# 	matched_nearest_gene_snpsnap, \
			# 	matched_nearest_gene, \
			# 	matched_nearest_gene_located_within, \
			# 	matched_snps_boundaries[matched_rsID]['ld_buddies'], \
			# ";".join(genes_in_matched_locus.keys()) )) # pascal - with added extension
				


	outfile.close()
	
################################# ENSEMBL Gene file #######################################################
### Production v1 ###
#gene_information_file="/home/projects/tp/childrens/snpsnap/data/misc/ensg_mart_ensembl64_buildGRCh37.p5.tab"
#gene_information_file="/cvar/jhlab/snpsnap/data/misc/ensg_mart_ensembl64_buildGRCh37.p5.tab"

### FEB 2015 - Production v2 ###
#gene_information_file="/cvar/jhlab/snpsnap/data/misc/biomart_download-2015-02-26-snpsnap_production_v2-ensembl-release_GRCh37.p13_processed-GENCODE.csv"
gene_information_file="/cvar/jhlab/snpsnap/data/misc/biomart_download-2015-02-26-snpsnap_production_v2-ensembl-release_GRCh37.p13_processed-GENCODE.chrosome_clean.unique-ENSG_ID.csv"
# Ensembl Gene ID,Chromosome Name,Gene Start (bp),Gene End (bp),Strand,Gene type,HGNC symbol,Source (gene),Status (gene)
# ENSG00000261657,HG991_PATCH,66119285,66465398,1,protein_coding,SLC25A26,havana,KNOWN
# ENSG00000223116,13,23551994,23552136,-1,miRNA,,ensembl,NOVEL
# ENSG00000233440,13,23708313,23708703,1,pseudogene,HMGA1P6,havana,KNOWN
# ENSG00000207157,13,23726725,23726825,-1,misc_RNA,RNY3P4,ensembl,KNOWN


#
# Parse arguments  
#
arg_parser = argparse.ArgumentParser(description="Parse plink output and construct loci")
arg_parser.add_argument("--ldfiles_prefix", required=True, help="Prefix to Plink .ld files ('*' suffixed in above method)")
arg_parser.add_argument("--super_population", required=True, help="Super population") # e.g. EUR
arg_parser.add_argument("--outfilename", required=True, help="Filename for outfile") # e.g. .;long_path../ld0.5/stat_gene_density/freq0-1.tab
args = arg_parser.parse_args()

### get arguments
super_population = args.super_population
ldfiles_prefix = args.ldfiles_prefix
outfilename = args.outfilename


###################################### *OBS* HARDCODED PATH - setting file_frq ######################################
file_frq = "/cvar/jhlab/snpsnap/data/step1/production_v2_QC_full_merged_duplicate_rm/{super_population}/ALL.chr_merged.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.frq".format(super_population=super_population)
# e.g. /cvar/jhlab/snpsnap/data/step1/production_v2_QC_full_merged_duplicate_rm/EUR/ALL.chr_merged.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.frq

### read .frq file
snp_maf_dict = read_file_frq(file_frq)

gene_info,gene_info_red = read_gene_info(gene_information_file) # Finds position of each gene
# saves hashes global

get_matched_snps(ldfiles_prefix, outfilename)
