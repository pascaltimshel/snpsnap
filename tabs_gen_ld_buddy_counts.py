#!/usr/bin/env python2.7


import sys
import os
import subprocess 

import collections
import time
import datetime

import glob
import pandas as pd

import pplogger

import argparse

import pdb


def create_ld_buddy_counts():
	df_list = [] # this list will contain data frames
	df_index_list = []
	df_length_list = []
	for param in param_list:
		logger.info( 'create_ld_buddy_counts: proccessing param=%s' % param)
		################ PLEASE CHECK THESE PATHS - must correspond to the paths in cat_tabs() ##########################		
		### production_v1
		# #inpath_base = input_dir_base + '/small_test_' + distance_type + str(param) # e.g DIR: /data/step3/1KG_snpsnap_production_v1/ld0.5
		# inpath_base = input_dir_base + '/' + distance_type + str(param) # e.g DIR: /data/step3/1KG_snpsnap_production_v1/ld0.5
		# outpath_combined_tab = inpath_base + '/' + 'combined.tab' # FILE: e.g /data/step3/1KG_snpsnap_production_v1/ld0.5/combined.tab
		
		### NEW FEB 2015* - production_v2
		inpath_base = "{base}/{super_population}/{distance_type}{distance_cutoff}".format(base=input_dir_base, super_population=super_population, distance_type=distance_type, distance_cutoff=param) # e.g DIR: /data/step2/1KG_snpsnap_production_v2/EUR/ld0.5
		inpath_stat_gene_density = inpath_base + '/' + 'stat_gene_density' # DIR: e.g /data/step2/1KG_snpsnap_production_v2/EUR/ld0.5/stat_gene_density
		outpath_combined_tab = inpath_base + '/' + 'combined.tab' # FILE: e.g /data/step2/1KG_snpsnap_production_v2/EUR/ld0.5/combined.tab

		################################################################################################################################		

		################## JUNE 2014 ##################
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


		################## NEW FEB 2015 - production_v2 ##################
		## *<--OBS-->*: REMEMBER TO UPDATE "cols2use"
		## *<--OBS-->*: index column should be the column number where the rsID is positioned

		#1=rsID
		#2=freq_bin
		#3=snp_maf
		#4=chromosome number of rsID
		#5=position of rsID
		#6=gene count in matched locus
		#7=dist to nearest gene - SNPSNAP DISTANCE
		#8=dist to nearest gene protein_coding - SNPSNAP DISTANCE
		#9=dist to nearest gene
		#10=dist to nearest gene LOCATED WITHIN
		#11=boundary_upstream
		#12=boundary_downstream
		#13=nearest_gene SNPSNAP
		#14=nearest_gene SNPSNAP protein_coding
		#15=nearest_gene
		#16=nearest_gene LOCATED WITHIN (may be empty)
		#17=nearest_gene_HGNC
		#18=nearest_gene_HGNC protein_coding
		#19=ld buddies count
		#20=flag_snp_within_gene
		#21=flag_snp_within_gene_protein_coding
		#22=genes in matches locus, multiple ENSEMBL IDs

		### ***IMPORTANT*** to keep in sync with parse_matched_SNPs.py and cat_tabs()! ###
		#cols2use=[0, 13] # SNPsnap production version 1 
		cols2use=[0, 18] # SNPsnap production version 2
		###################################################################################

		start_time = time.time()
		logger.info( "Reading SPECIFIC COLUMNS of tabfile into DataFrame: %s" % outpath_combined_tab )
		df = pd.read_csv( outpath_combined_tab, delimiter="\t", header=0, names=['rsID', 'ld_buddy_count_'+str(param)], index_col=0, usecols=cols2use)
		# ---> OBS: NOTICE the "*RENAMING*"
		# OBS: delim_whitespace=True does NOT work if some columns (in the middle) are blank/empty. 
		# Pandas will skip these blank fields resulting in:
		# 1) 'frameshift': shift of the next columns 
		# 2) consequently: get the wrong number of columns
		elapsed_time = time.time()-start_time
		logger.info( "DONE | elapsed time: %s min" % (elapsed_time/60, ) )


		########## KEEP THIS - Testing different commands for import - note that delim_whitespace=True is not the correct for this data (see above) #########
		#df = pd.read_csv( outpath_combined_tab, delim_whitespace=True, header=0, usecols=[0, 13] )
			# NO ERROR, but gives two columns ('rsID' and 'LD_boddies') along with indexes from 0,1,2,3...
		#df = pd.read_csv( outpath_combined_tab, delim_whitespace=True, header=0, names=[param], usecols=[13] )
			# NO ERROR. however, indexes are 0, 1, 2, 3....
		#df = pd.read_csv( outpath_combined_tab, delim_whitespace=True, header=0, names=[param], index_col=0, usecols=[0] )
			# NO ERROR. The dataframe only consists of indexes
		# delim_whitespace=True, header=0, names=[param], index_col=0, usecols=[0, 13]
			# ERROR: ===> use ValueError: Passed header names mismatches usecols
			# Reason: there is only given one name for the index.
		# default: sep=','. If sep=None pandas uses automatically sniffing

		# Appdening to list
		df_list.append(df) # we merge this list of dfs later...

		df_length_list.append(len(df))
		df_index_list.append(df.index)
	
	################## 'UNIT TESTS' - making sure that the importet data makes sense ##################	
	## we do not need at all-against-all comparison
	## our criteria is that a == b == c == ... == z. For this to be true we only need to check a == b, a == c, ... a == z. 
	## That is, we do NOT need to check b == c, b == d, ..., c == d, ...
	for i in range(len(df_index_list)-1):
		# comparing all indexes and length against the first read data frame (ld0.1)
		elem_ref = 0
		elem_next = i+1

		set_diff = df_index_list[elem_ref].diff(df_index_list[elem_next]) # NB: this computation is a bit heavy. Takes ~ 20 seconds...
		test_set_diff = 'NotDone'
		if len(set_diff) == 0:
			test_set_diff = True # test passed
		else:
			test_set_diff = False
			logger.warning( "%s vs %s | OBS! index set difference:\n%s" % (elem_ref, elem_next, set_diff) )
		
		test_index_equality = df_index_list[elem_ref].equals(df_index_list[elem_next]) # pandas index method
		test_lenght = df_length_list[elem_ref] == df_length_list[elem_next]
		logger.warning( "test_set_diff | %s vs %s | passed = %s" % (elem_ref, elem_next, test_set_diff) )
		logger.warning( "test_index_equality | %s vs %s | passed = %s" % (elem_ref, elem_next, test_index_equality) )
		logger.warning( "test_lenght | %s vs %s | passed = %s" % (elem_ref, elem_next, test_lenght) )
		### Additional tests:
		# 1) check that for each SNP the ld_boddy_count is MONOTONIC DECREASING as you INCREASE ld


	########################################################################################
	###################################### JOIN_OUTER ######################################
	# SNPsnap production version 1: used "ld_buddy_count.tab_join_outer" #
	# SNPsnap production version 2: used "ld_buddy_count.tab_join_outer" #
	
	# concatenate data frames horizontally
	merged = pd.concat(df_list, axis=1, join='outer') 	# ---> row indexes will be unioned and sorted.
														# ***OBS***: index name is NOT kept using 'outer' - I found out about this the hard way
	
	### Set name
	#merged.index.name = df_index_list[0].index.name # ADDED 07/04/2014 - **UNTESTED** - COPYING the index name from the first df in the df_list to fix that index_label is lost using join='outer'
	merged.index.name = df_index_list[0].name # COPYING the index name from the first df in the df_list to fix that index_label is lost using join='outer'
	logger.info( "merged.index.name={}".format(merged.index.name) )

	logger.info( "writing 'merged' data frame to csv..." )
	merged.to_csv(outfile_ld_buddy+"_join_outer", sep='\t', header=True, index=True, index_label=None) # index_label=None ==> use index names from df
	logger.info( 'JOIN_OUTER: len of data frame: %s' % len(merged) )

	if merged.isnull().any(axis=0).any(axis=0): # same as merged.isnull().any().any()
		df_null = merged[merged.isnull().any(axis=1)]
		logger.warning( 'JOIN_OUTER isnull(): *FOUND NULL VALUES* len of data frame: %s' % len(df_null) )
		logger.warning( df_null )
	else:
		logger.warning( 'JOIN_OUTER: there is NO null values' )


	########################################################################################
	###################################### JOIN_INDEX ######################################
	start_time = time.time()
	logger.info( 'JOIN_INDEX: start concat and writing csv' )
	merged = pd.concat(df_list, axis=1, join_axes=[df_index_list[0]]) # index name is kept this way
	merged.to_csv(outfile_ld_buddy+"_join_index", sep='\t', header=True, index=True, index_label=None) 	# index_label=None ==> use index names from df
	elapsed_time = time.time()-start_time
	logger.info( "DONE | elapsed time: %s min" % (elapsed_time/60, ) )
	logger.info( 'JOIN_INDEX: len of data frame: %s' % len(merged) )


	#http://stackoverflow.com/questions/14247586/python-pandas-how-to-select-rows-with-one-or-more-nulls-from-a-dataframe-without
	#http://pandas.pydata.org/pandas-docs/dev/gotchas.html

	# checking there are any null/NaN values in the data frame.
	# Note that merged.isnull().any(axis=0) produces a pandas.Series object, which you need to reduce to a bool type (<type 'numpy.bool_'>) by calling .any one more time
	if merged.isnull().any(axis=0).any(axis=0): # same as merged.isnull().any().any()
	#you could potenitally also use: merged.notnull().all()
		df_null = merged[merged.isnull().any(axis=1)]
		logger.warning( 'JOIN_INDEX isnull(): *FOUND NULL VALUES* len of data frame: %s' % len(df_null) )
		logger.warning( df_null )
	else:
		logger.warning( 'JOIN_INDEX: there is NO null values' )

	########################################################################################
	########################################################################################



def ParseArguments():
	arg_parser = argparse.ArgumentParser(description="Python submission Wrapper")
	arg_parser.add_argument("--super_population", required=True, help=".....", choices=["EUR", "EAS", "WAFR"])
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

###################################### CONSTANTS ######################################
current_script_name = os.path.basename(__file__).replace('.py','')

start_time_script = time.time()
batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')


###################################### SETUP logging ######################################
#log_dir='/cvar/jhlab/snpsnap/logs_pipeline/production_v2/step5_tabs_ld_buddy_counts/{super_population}'.format(super_population=super_population)
log_dir='/cvar/jhlab/snpsnap/logs_pipeline/production_v2_chrX_standalone-altQC/step5_tabs_ld_buddy_counts/{super_population}'.format(super_population=super_population)
if not os.path.exists(log_dir):
	os.makedirs(log_dir)

log_name = "{current_script_name}_{timestamp}".format(current_script_name=current_script_name, timestamp=batch_time)

logger = pplogger.Logger(name=log_name, log_dir=log_dir, log_format=1, enabled=True).get()
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################

param_list=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9] # ---> KEEP ALL - We want LD buddy information for all LD distances
distance_type = 'ld' # SCRIPT SHOULD ONLY RUN FOR *LD* DISTANCE

############################# PARAM LIST ##########################################

################## *OBS*: specific for "create_ld_buddy_counts()" ##################
#output_dir_base = "/cvar/jhlab/snpsnap/data/ld_buddy_counts/1KG_snpsnap_production_v2/{super_population}".format(super_population=super_population) # e.g /data/ld_buddy_counts/1KG_snpsnap_production_v2/EUR
output_dir_base = "/cvar/jhlab/snpsnap/data/production_v2_chrX_standalone-altQC/ld_buddy_counts/{super_population}".format(super_population=super_population) # e.g /data/ld_buddy_counts/1KG_snpsnap_production_v2/EUR
if not os.path.exists(output_dir_base):
	os.makedirs(output_dir_base)

outfile_ld_buddy = "{base}/ld_buddy_count.tab".format(base=output_dir_base) # e.g /data/ld_buddy_counts/1KG_snpsnap_production_v2/EUR/ld_buddy_count.tab



###################################################################################

### NEW FEB 2015* - production_v2
#input_dir_base = "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2"
input_dir_base = "/cvar/jhlab/snpsnap/data/production_v2_chrX_standalone-altQC/step2"

### production_v1
# input_dir_base = "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v1"
# output_dir_base = "/cvar/jhlab/snpsnap/data/ld_buddy_counts/1KG_snpsnap_production_v1"
# outfile_ld_buddy = output_dir_base + '/' + 'ld_buddy_count.tab' # e.g /data/ld_buddy_counts/1KG_snpsnap_production_v1/ld_buddy_count.tab



############################# FUNCTION CALLS ##########################################

create_ld_buddy_counts()
###################################################################################



elapsed_time = time.time() - start_time_script
logger.info( "%s | TOTAL RUNTIME: %s s (%s min)" % (current_script_name, elapsed_time, elapsed_time/60) )




