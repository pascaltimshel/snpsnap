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

import pdb


###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')
log_dir='/cvar/jhlab/snpsnap/snpsnap/logs_step5_tabs_ld_buddy_counts'
logger = pplogger.Logger(name=current_script_name, log_dir=log_dir, log_format=0, enabled=True).get() #
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
###########################################################################################

###################################### CONSTANTS ######################################
start_time_script = time.time()
batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')

############################# PARAM LIST ##########################################
#param_list=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
param_list=[0.1, 0.5, 0.9]
distance_type = 'ld' # choose 'ld' or 'kb'
###################################################################################


input_dir_base = "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v1"
output_dir_base = "/cvar/jhlab/snpsnap/data/ld_buddy_counts/1KG_snpsnap_production_v1"
outfile = output_dir_base + '/' + 'ld_buddy_count.tab' # e.g /data/ld_buddy_counts/1KG_snpsnap_production_v1/ld_buddy_count.tab

processes = collections.defaultdict(dict)

data_frame_list = []
for param in param_list:
	#inpath = input_dir_base + '/' + distance_type + str(param) + '/' + 'stat_gene_density' # e.g /data/step3/1KG_snpsnap_production_v1/ld0.5/stat_gene_density
	# FOR TEST USAGE
	inpath = input_dir_base + '/small_test_' + distance_type + str(param) + '/' + 'stat_gene_density' # e.g /data/step3/1KG_snpsnap_production_v1/ld0.5/stat_gene_density

	tabfiles = glob.glob(inpath+"/*.tab")
	if not len(tabfiles) == 50:
		print "Error: did not find 50 .tab files as expected in path: %s" % inpath
		print "Number of tabfiles found: %s" % len(tabfiles)
		print "Aborting script..."
		sys.exit(1)
	# Sorting on freq bin
	tabfiles.sort(key=lambda x: int(x.split('/')[-1].split('freq')[-1].split('-')[0])) # this step is not strictly needed. Unreadable code

	


	## NEW JUNE 2014
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

# 	header_str = "rsID freq_bin snp_chr snp_position gene_count dist_nearest_gene_snpsnap dist_nearest_gene dist_nearest_gene_located_within loci_upstream loci_downstream ID_nearest_gene_snpsnap ID_nearest_gene ID_nearest_gene_located_within LD_boddies ID_genes_in_matched_locus"
# 	colnames =header_str.split()
# 	df = pd.DataFrame(columns=colnames)
# 	#df = pd.DataFrame(columns=[str(param)]) #
# 	#df = pd.DataFrame() #

# 	for counter, tabfile in enumerate(tabfiles, start=1):
# 		if not os.path.getsize(tabfile) > 0: continue
# 		logger.info( "Reading tabfile #%s/#%s into DataFrame: %s" % (counter, len(tabfiles), os.path.basename(tabfile)) )

# 		df = df.append(pd.read_csv(tabfile, names=colnames, index_col=0, usecols=[13], engine='python')) 


# 	data_frame_list.append(df)

# # concatenate data frames horizontally
# merged = pd.concat(dfs, axis=1, join='outer')
# logger.info( merged )

# merged.to_csv(outfile, sep='\t', header=True, index=True, index_label='snpID')




elapsed_time = time.time() - start_time_script
logger.info( "%s | TOTAL RUNTIME: %s s (%s min)" % (current_script_name, elapsed_time, elapsed_time/60) )






###################################### READING PANDAS DATA FRAME ONE by ONE - FAILED ######################################

# data_frame_list = []
# for param in param_list:
# 	# FOR TEST USAGE
# 	inpath = input_dir_base + '/small_test_' + distance_type + str(param) + '/' + 'stat_gene_density' # e.g /data/step3/1KG_snpsnap_production_v1/ld0.5/stat_gene_density

# 	tabfiles = glob.glob(inpath+"/*.tab")
# 	if not len(tabfiles) == 50:
# 		print "Error: did not find 50 .tab files as expected in path: %s" % inpath
# 		print "Number of tabfiles found: %s" % len(tabfiles)
# 		print "Aborting script..."
# 		sys.exit(1)
# 	# Sorting on freq bin
# 	tabfiles.sort(key=lambda x: int(x.split('/')[-1].split('freq')[-1].split('-')[0])) # this step is not strictly needed. Unreadable code
	
# 	header_str = "rsID freq_bin snp_chr snp_position gene_count dist_nearest_gene_snpsnap dist_nearest_gene dist_nearest_gene_located_within loci_upstream loci_downstream ID_nearest_gene_snpsnap ID_nearest_gene ID_nearest_gene_located_within LD_boddies ID_genes_in_matched_locus"
# 	colnames =header_str.split()
# 	df = pd.DataFrame(columns=colnames)
# 	#df = pd.DataFrame(columns=[str(param)]) #
# 	#df = pd.DataFrame() #

# 	for counter, tabfile in enumerate(tabfiles, start=1):
# 		if not os.path.getsize(tabfile) > 0: continue
# 		logger.info( "Reading tabfile #%s/#%s into DataFrame: %s" % (counter, len(tabfiles), os.path.basename(tabfile)) )
# 		#http://stackoverflow.com/questions/15242746/handling-variable-number-of-columns-with-pandas-python
		
# 		#df = df.append(pd.read_csv(tabfile, names=colnames, delim_whitespace=True, index_col=0, usecols=[13], engine='python')) 
# 		#ValueError: The 'delim_whitespace' option is not supported with the 'python' engine
		
# 		#df = df.append(pd.read_csv(tabfile, names=colnames, index_col=0, usecols=[13], engine='python')) 
# 		#ValueError: Number of passed names did not match number of header fields in the file

# 		df = df.append(pd.read_csv(tabfile, names=colnames, index_col=0, usecols=[13], engine='python')) 
# 		#IndexError: list index out of range


# 		#df = df.append(pd.read_csv(tabfile, names=[str(param)], delim_whitespace=True, index_col=0, usecols=[13])) # appending read CSV. consider not setting names
# 		#df = df.append(pd.read_csv(tabfile, delim_whitespace=True, index_col=0, error_bad_lines=False) ) 
# 		#df = df.append(pd.read_csv(tabfile, delim_whitespace=True) ) 
# 		#df = pd.read_csv(tabfile, delim_whitespace=True, na_values=["", "inf"])
# 		#df = pd.read_csv(tabfile, delim_whitespace=True, header=None, sep='\t')
# 		#print df

# 	data_frame_list.append(df)

# # concatenate data frames horizontally
# merged = pd.concat(dfs, axis=1, join='outer')
# logger.info( merged )

# merged.to_csv(outfile, sep='\t', header=True, index=True, index_label='snpID')

# elapsed_time = time.time() - start_time_script
# logger.info( "%s | TOTAL RUNTIME: %s s (%s min)" % (current_script_name, elapsed_time, elapsed_time/60) )










