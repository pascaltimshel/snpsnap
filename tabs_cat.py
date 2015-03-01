#!/usr/bin/env python2.7


import sys
import glob
import os

import datetime
import time
import argparse

import pplaunch
import pphelper
import pplogger

import re
import subprocess
import logging


import pdb


# # Function to read frq file
# def read_file_frq(file_frq):
# 	logger.info("Reading file_frq file into hashes: {}".format(file_frq) )
# 	### File snippet
# 	### NB: ALL SNPs (rsIDs) should be unique at this stage
# 	# CHR                                  SNP   A1   A2          MAF  NCHROBS
# 	#   1                              1:11008    G    C      0.08847     1006
# 	#   1                              1:11012    G    C      0.08847     1006
# 	#   1                              1:13110    A    G      0.05666     1006
# 	#   1                          rs201725126    G    T       0.1869     1006
# 	#   1                          rs200579949    G    A       0.1869     1006
# 	#   1                              1:13273    C    G       0.1471     1006
# 	#   1                              1:14464    T    A       0.1859     1006
# 	#   1                              1:14599    A    T        0.161     1006
# 	#   1                              1:14604    G    A        0.161     1006
# 	snps_from_batches = {}
# 	with open(file_frq, 'r') as f:
# 		for line in f: # reading line by line
# 			fields = line.strip().split()
# 			SNP = fields[1]
# 			### Additional check - REMEMBER: all rsID should be unique at this point.
# 			if SNP in snps_from_batches: # we have seen this rsID before
# 				logger.critical( "Have seen rsID={SNP} before. THIS SHOULD NOT HAPPEN THOUGH. Check the plink .frq file for duplicate rsIDs." )

# 			### Saving MAF in dict
# 			snps_from_batches[SNP] = 1

# 	logger.info( "Done reading file_frq" )
# 	return snps_from_batches



def validate_combined_file(attempt="NoArgumentParsed"):
	### TODO: add the failed line number to the "status string" for easier debugging

	### If you have problems with this step, you can use the following perl one-line to debug:
	# perl -lane '@t = split("\t", -1); print scalar(@t)' <FILENAME> | sort | uniq -c
	### After that you can use something like this
	# perl -lane '@t = split("\t"); if (scalar(@t)==<DEVIATING COLUMN NUMBER>) {print "$. | $_"}' <FILENAME>

	status = "passed" # default

	# n_batch_snps --> "GLOBAL" namespace. Consider parsing it as argument
	n_combined_snps = 0

	with open(outpath_combined_tab, "r") as f:
		### All lines should have the same number of columns - ALSO THE HEADER
		n_cols = len(next(f).split("\t")) # IMPORTANT TO SPLIT ON CORRECT DELIMITER. Note: we do not need to call .strip(), since it is ok that the last field has an extra newline
			## --> SIDENOTE: do NOT mix line iterators with other file methods (like readline())
		for line in f:
			n_combined_snps += 1
			tmp_n_cols = len(line.split("\t"))
			if not tmp_n_cols == n_cols:
				status = "failed"
				# consider breaking out of loop here. However, then you will loose the information about "n_combined_snps"

	snp_difference = n_batch_snps - n_combined_snps
	with open(file_status, "a") as f: # *IMPORTANT*: open in append-mode
		status_string = "status={status} | diff = {snp_difference} | pipeline_identifier={pipeline_identifier} | batch_time={batch_time}".format(status=status, snp_difference=snp_difference, pipeline_identifier=pipeline_identifier, batch_time)
		f.write(status_string+"\n")

		logger.info( status_string )


def cat_tabs():

	##### Writing out header to file. OVERWRITING ANY EXISTING FILE! #####
	### *NEW FEB 2015* - ENSEMBL file for GENCODE genes. added: protein_coding, HGNC symbols and 2 x SNP_location_flags
	# dist_nearest_gene_snpsnap_protein_coding
	# ID_nearest_gene_snpsnap_protein_coding
	# HGNC_nearest_gene_snpsnap
	# HGNC_nearest_gene_snpsnap_protein_coding
	# flag_snp_within_gene
	# flag_snp_within_gene_protein_coding
	# snp_maf

	logger.info( 'cat_tabs: writing header')
	header_str = "rsID freq_bin snp_maf snp_chr snp_position gene_count dist_nearest_gene_snpsnap dist_nearest_gene_snpsnap_protein_coding dist_nearest_gene dist_nearest_gene_located_within loci_upstream loci_downstream ID_nearest_gene_snpsnap ID_nearest_gene_snpsnap_protein_coding ID_nearest_gene ID_nearest_gene_located_within HGNC_nearest_gene_snpsnap HGNC_nearest_gene_snpsnap_protein_coding LD_boddies flag_snp_within_gene flag_snp_within_gene_protein_coding ID_genes_in_matched_locus"
	### *BEFORE FEB 2015* - old ENSEMBL file
	#header_str = "rsID freq_bin snp_chr snp_position gene_count dist_nearest_gene_snpsnap dist_nearest_gene dist_nearest_gene_located_within loci_upstream loci_downstream ID_nearest_gene_snpsnap ID_nearest_gene ID_nearest_gene_located_within LD_boddies ID_genes_in_matched_locus"
	header_str_tab_sep = "\t".join(header_str.split())
	with open(outpath_combined_tab, 'w') as f:
		f.write(header_str_tab_sep+'\n')
	#################################################

	tabfiles = glob.glob(inpath_stat_gene_density+"/*.tab")
	if not len(tabfiles) == 50:
		logger.error( "Error: did not find 50 .tab files as expected in path: %s" % inpath_stat_gene_density )
		logger.error( "Number of tabfiles found: %s" % len(tabfiles) )
		logger.error( "Aborting script..." )
		raise Exception("See above")
	# Sorting on freq bin
	# It is EXTREMELY important to SORT the tab files before 
	tabfiles.sort(key=lambda x: int(x.split('/')[-1].split('freq')[-1].split('-')[0]))

	################## NEW FEB 2015: trying to STABILIZE concatenation of files ##################
	##### VERSION 1 #####
	### REF: http://stackoverflow.com/a/17749560
	# import shutil

	# with open(outfilename, 'wb') as outfile:
	# 	for filename in glob.glob('*.txt'):
	# 		with open(filename, 'rb') as readfile:
	# 			shutil.copyfileobj(readfile, outfile)

	##### VERSION 2 #####
	## SOURCE: http://stackoverflow.com/a/13613375
	logger.info( "Starting to concatenate files" )
	with open(outpath_combined_tab, 'a') as outfile: # IT IS IMPORTANT TO OPEN FILE IN APPEND MODE!
		for tabfile in tabfiles:
			logger.info( "Cat'ing tabfile={}".format(tabfile) )
			with open(tabfile) as infile:
				for line in infile:
					outfile.write(line)
	logger.info( "cat_tabs() is now finished" )


def ParseArguments():
	arg_parser = argparse.ArgumentParser(description="Python submission Wrapper")
	arg_parser.add_argument("--super_population", required=True, help="")
	arg_parser.add_argument("--distance_type", required=True, help="")
	arg_parser.add_argument("--distance_cutoff", required=True, help="")
	
	args = arg_parser.parse_args()
	return args

def LogArguments():
	# PRINT RUNNING DESCRIPTION 
	now = datetime.datetime.now()
	logger.critical( '# ' + ' '.join(sys.argv) )
	logger.critical( '# ' + now.strftime("%a %b %d %Y %H:%M") )
	logger.critical( '# CWD: ' + os.getcwd() )
	logger.critical( '# COMMAND LINE PARAMETERS SET TO:' )
	for arg in dir(args):
		if arg[:1]!='_':
			logger.critical( '# \t' + "{:<30}".format(arg) + "{:<30}".format(getattr(args, arg)) ) ## LOGGING


###################################### ARGUMENTS ######################################
args = ParseArguments()

super_population = args.super_population
distance_type = args.distance_type
distance_cutoff = args.distance_cutoff

pipeline_identifier = "{super_population}_{distance_type}_{distance_cutoff}".format(super_population=super_population, distance_type=distance_type, distance_cutoff=distance_cutoff) # e.g EUR_ld_0.5


###################################### CONSTANTS ######################################
current_script_name = os.path.basename(__file__).replace('.py','')

start_time_script = time.time()
batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')


###################################### SETUP logging ######################################
log_dir='/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step4_tabs_cat/{super_population}'.format(super_population=super_population)
if not os.path.exists(log_dir):
	os.makedirs(log_dir)

log_name = "{current_script_name}_{pipeline_identifier}_{timestamp}".format(current_script_name=current_script_name, pipeline_identifier=pipeline_identifier, timestamp=batch_time)

logger = pplogger.Logger(name=log_name, log_dir=log_dir, log_format=1, enabled=True).get()
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################


###################################################################################

### NEW FEB 2015* - production_v2
input_dir_base = "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2"


### NEW FEB 2015* - production_v2
inpath_base = "{base}/{super_population}/{distance_type}{distance_cutoff}".format(base=input_dir_base, super_population=super_population, distance_type=distance_type, distance_cutoff=distance_cutoff) # e.g DIR: /data/step2/1KG_snpsnap_production_v2/EUR/ld0.5
inpath_stat_gene_density = inpath_base + '/' + 'stat_gene_density' # DIR: e.g /data/step2/1KG_snpsnap_production_v2/EUR/ld0.5/stat_gene_density
outpath_combined_tab = inpath_base + '/' + 'combined.tab' # FILE: e.g /data/step2/1KG_snpsnap_production_v2/EUR/ld0.5/combined.tab

### *BEFORE FEB 2015* production_v1
# inpath_base = input_dir_base + '/' + distance_type + str(param) # e.g DIR: /data/step3/1KG_snpsnap_production_v1/ld0.5
# inpath_stat_gene_density = inpath_base + '/' + 'stat_gene_density' # DIR: e.g /data/step3/1KG_snpsnap_production_v1/ld0.5/stat_gene_density
# outpath_combined_tab = inpath_base + '/' + 'combined.tab' # FILE: e.g /data/step3/1KG_snpsnap_production_v1/ld0.5/combined.tab
################################################################################################################################		

###################################### Counting the number of SNPs in the freq file ######################################
file_frq = "/cvar/jhlab/snpsnap/data/step1/production_v2_QC_full_merged_duplicate_rm/{super_population}/ALL.chr_merged.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.frq".format(super_population=super_population)
	# --> could also use .bim file
### File snippet
### NB: ALL SNPs (rsIDs) should be unique at this stage
# CHR                                  SNP   A1   A2          MAF  NCHROBS
#   1                              1:11008    G    C      0.08847     1006
#   1                              1:11012    G    C      0.08847     1006
#   1                              1:13110    A    G      0.05666     1006


### Count the number of lines in the file
logger.info( "counting the number of SNPs in file_frq: {}".format(file_frq) )
n_batch_snps = sum(1 for line in open(file_frq,'r')) - 1 # SUBTRACTING HEADER LINE
	# --> this is pretty fast (only a bit slower than "wc -l"). 3.5 sec for a 1 GB file
logger.info( "done" )


################################ *IMPORTANT*: PATH TO STATUS FILE #############################################
# *THIS IS SPECIAL FOR "tabs_cat.py"*
# This script will *APPEND* a "status line" to a file that is SHARED within a super_population. That is, all distance measures writes to the same file.
# (Note that this approach is not *thread* safe: you might corrupt the file (or loose data) in the UNLIKELY event that two "tabs_cat.py" processes wants to append at the same time.

path_status = '/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step4_tabs_cat_status/{super_population}'.format(super_population=super_population)
if not os.path.exists(path_status):
	os.makedirs(path_status)
file_status = path_status + "/tabs_cat_status_file.txt"


###############################################################################################################		


############################# FUNCTION CALLS ##########################################
if os.path.exists(outpath_combined_tab):
	logger.info( "outpath_combined_tab exists. will call VALIDATION function" )
	validate_combined_file(attempt="validating_existing")
else:
	logger.info( "cat'ing file" )
	cat_tabs()
	logger.info( "done cat'ing file. will call VALIDATION function" )
	validate_combined_file(attempt="validating_new")


###################################################################################



elapsed_time = time.time() - start_time_script
logger.info( "%s | TOTAL RUNTIME: %s s (%s min)" % (current_script_name, elapsed_time, elapsed_time/60) )




