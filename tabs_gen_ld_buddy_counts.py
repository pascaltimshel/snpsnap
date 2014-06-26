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


#### TODO:
# 1) Rewrite cat_tabs() into a independent module/script and import it.
# 		---> requires that you parse arguments properly (not global variables)


def cat_tabs():

	processes = collections.defaultdict(dict)

	for param in param_list:
		logger.info( 'cat_tabs: proccessing param=%s' % param)

		################ PLEASE CHECK THESE PATHS - must correspond to the paths in create_ld_buddy_counts() ##########################		
		#inpath_base = input_dir_base + '/small_test_' + distance_type + str(param) # e.g DIR: /data/step3/1KG_snpsnap_production_v1/ld0.5
		inpath_base = input_dir_base + '/' + distance_type + str(param) # e.g DIR: /data/step3/1KG_snpsnap_production_v1/ld0.5
		inpath_stat_gene_density = inpath_base + '/' + 'stat_gene_density' # DIR: e.g /data/step3/1KG_snpsnap_production_v1/ld0.5/stat_gene_density
		outpath_combined_tab = inpath_base + '/' + 'combined.tab' # FILE: e.g /data/step3/1KG_snpsnap_production_v1/ld0.5/combined.tab
		################################################################################################################################		

		################## Checking if file exists ##################
		if os.path.exists(outpath_combined_tab):
			logger.warning ( "outpath_combined_tab exists. Skipping cat'ing new" )
			continue

		#############################################################

		# Writing out header to file. OVERWRITING ANY EXISTING FILE!
		header_str = "rsID freq_bin snp_chr snp_position gene_count dist_nearest_gene_snpsnap dist_nearest_gene dist_nearest_gene_located_within loci_upstream loci_downstream ID_nearest_gene_snpsnap ID_nearest_gene ID_nearest_gene_located_within LD_boddies ID_genes_in_matched_locus"
		header_str_tab_sep = "\t".join(header_str.split())
		with open(outpath_combined_tab, 'w') as f:
			f.write(header_str_tab_sep+'\n')
		#################################################

		tabfiles = glob.glob(inpath_stat_gene_density+"/*.tab")
		if not len(tabfiles) == 50:
			logger.error( "Error: did not find 50 .tab files as expected in path: %s" % inpath_stat_gene_density )
			logger.error( "Number of tabfiles found: %s" % len(tabfiles) )
			logger.error( "Aborting script..." )
			sys.exit(1)
		# Sorting on freq bin
		# It is EXTREMELY important to SORT the tab files before 
		tabfiles.sort(key=lambda x: int(x.split('/')[-1].split('freq')[-1].split('-')[0]))

		############### BE AWARE OF TOO long command line ##############
		#  - command: Argument list too long
		#xargs --show-limits
		#getconf ARG_MAX
		#	--> 131072
		# using xargs?
		#cat filelist | xargs cat >> bigfile.dat
		################################################################

		# creating cat cmd. APPENDING TO FILE containing header.
		cmd_cat = "cat {files} >> {out}".format(files=" ".join(tabfiles), out=outpath_combined_tab)
		#logger.info( "making command: %s" % cmd_cat )
		
		### USE THIS for getting stdout and stderr from cat commando
		#p=subprocess.Popen(cmd_cat, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
		# (stdout, stderr) = p.communicate() # OBS: stderr should be empty because we send stderr to subprocess.STDOUT
		# if stdout:
		# 	logger.info(stdout)
		# if stderr:
		# 	logger.warning('****I did see some stderr!')
		# 	logger.error(stderr)
		
		### USE this to inherrit stdout/stderr from subprocess
		p=subprocess.Popen(cmd_cat, stdout=None, stderr=subprocess.STDOUT, shell=True)
		processes[str(param)]['p'] = p
		processes[str(param)]['pid'] = p.pid

	logger.info( "I have just submitted the following processes..." )
	for param in sorted(processes.keys()):
		logger.info( processes[param]['pid'] )

	logger.info( "Now waiting for processes..." )
	for param in sorted(processes.keys()):
		p = processes[param]['p']
		logger.info( "pid=%s [param=%s]: WAITING..." % (p.pid, param) )
		p.wait()
		elapsed_time = time.time() - start_time_script
		logger.info( "pid=%s [param=%s]: DONE! | elapsed time since start: %s min" % (p.pid, param, elapsed_time/60) )

def create_ld_buddy_counts():
	df_list = [] # this list will contain data frames
	df_index_list = []
	df_length_list = []
	for param in param_list:
		logger.info( 'create_ld_buddy_counts: proccessing param=%s' % param)
		################ PLEASE CHECK THESE PATHS - must correspond to the paths in cat_tabs() ##########################		
		#inpath_base = input_dir_base + '/small_test_' + distance_type + str(param) # e.g DIR: /data/step3/1KG_snpsnap_production_v1/ld0.5
		inpath_base = input_dir_base + '/' + distance_type + str(param) # e.g DIR: /data/step3/1KG_snpsnap_production_v1/ld0.5
		outpath_combined_tab = inpath_base + '/' + 'combined.tab' # FILE: e.g /data/step3/1KG_snpsnap_production_v1/ld0.5/combined.tab
		################################################################################################################################		

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

		start_time = time.time()
		logger.info( "Reading tabfile into DataFrame: %s" % outpath_combined_tab )
		df = pd.read_csv( outpath_combined_tab, delimiter="\t", header=0, names=['rsID', 'ld_buddy_count_'+str(param)], index_col=0, usecols=[0, 13])
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


	# concatenate data frames horizontally
	merged = pd.concat(df_list, axis=1, join='outer') # ---> row indexes will be unioned and sorted.
	merged.to_csv(outfile_ld_buddy+"_join_outer", sep='\t', header=True, index=True, index_label=None) # index_label=None ==> use index names from df
	logger.info( 'JOIN_OUTER: len of data frame: %s' % len(merged) )

	if merged.isnull().any(axis=0).any(axis=0): # same as merged.isnull().any().any()
		df_null = merged[merged.isnull().any(axis=1)]
		logger.warning( 'JOIN_OUTER isnull(): len of data frame: %s' % len(df_null) )
		logger.warning( df_null )
	else:
		logger.warning( 'JOIN_OUTER: there is NO null values' )


	start_time = time.time()
	logger.info( 'JOIN_INDEX: start concat and writing csv' )
	merged = pd.concat(df_list, axis=1, join_axes=[df_index_list[0]])
	merged.to_csv(outfile_ld_buddy+"_join_index", sep='\t', header=True, index=True, index_label=None) # index_label=None ==> use index names from df
	logger.info( "DONE | elapsed time: %s min" % (elapsed_time/60, ) )
	logger.info( 'JOIN_INDEX: len of data frame: %s' % len(merged) )
	elapsed_time = time.time()-start_time


	#http://stackoverflow.com/questions/14247586/python-pandas-how-to-select-rows-with-one-or-more-nulls-from-a-dataframe-without
	#http://pandas.pydata.org/pandas-docs/dev/gotchas.html

	# checking there are any null/NaN values in the data frame.
	# Note that merged.isnull().any(axis=0) produces a pandas.Series object, which you need to reduce to a bool type (<type 'numpy.bool_'>) by calling .any one more time
	if merged.isnull().any(axis=0).any(axis=0): # same as merged.isnull().any().any()
	#you could potenitally also use: merged.notnull().all()
		df_null = merged[merged.isnull().any(axis=1)]
		logger.warning( 'JOIN_INDEX isnull(): len of data frame: %s' % len(df_null) )
		logger.warning( df_null )
	else:
		logger.warning( 'JOIN_index: there is NO null values' )










###################################### SETUP logging ######################################
current_script_name = os.path.basename(__file__).replace('.py','')
log_dir='/cvar/jhlab/snpsnap/snpsnap/logs_step5_tabs_ld_buddy_counts'
logger = pplogger.Logger(name=current_script_name, log_dir=log_dir, log_format=0, enabled=True).get() #
def handleException(excType, excValue, traceback, logger=logger):
	logger.error("Logging an uncaught exception", exc_info=(excType, excValue, traceback))
#### TURN THIS ON OR OFF: must correspond to enabled='True'/'False'
sys.excepthook = handleException
logger.info( "INSTANTIATION NOTE: placeholder" )
###########################################################################################

###################################### CONSTANTS ######################################
start_time_script = time.time()
batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')

############################# PARAM LIST ##########################################
param_list=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
#param_list=[0.1, 0.5, 0.9]
distance_type = 'ld' # choose 'ld' or 'kb'
###################################################################################


input_dir_base = "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v1"
output_dir_base = "/cvar/jhlab/snpsnap/data/ld_buddy_counts/1KG_snpsnap_production_v1"
outfile_ld_buddy = output_dir_base + '/' + 'ld_buddy_count.tab' # e.g /data/ld_buddy_counts/1KG_snpsnap_production_v1/ld_buddy_count.tab

############################# FUNCTION CALLS ##########################################
cat_tabs()
create_ld_buddy_counts()
###################################################################################



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










