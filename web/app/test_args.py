#!/bin/env python

import subprocess

#import shlex
#command_line = ""

#args = shlex.split(command_line)
#print args


# cmd_match = "python {program:s} --user_snps_file {snplist:s} --output_dir {outputdir:s} --distance_type {distance_type} --distance_cutoff {distance_cutoff} match --N_sample_sets {N_sample_sets} --max_freq_deviation {max_freq_deviation} --max_distance_deviation {max_distance_deviation} --max_genes_count_deviation {max_genes_count_deviation} --set_file".format(program=script2call, snplist=file_snplist, outputdir=path_session_output, distance_type=distance_type, distance_cutoff=distance_cutoff, N_sample_sets=N_sample_sets, max_freq_deviation=max_freq_deviation, max_distance_deviation=max_distance_deviation, max_genes_count_deviation=max_genes_count_deviation)

# # program=script2call, 
# snplist=file_snplist, 
# outputdir=path_session_output, 
# distance_type=distance_type, 
# distance_cutoff=distance_cutoff 
# N_sample_sets=N_sample_sets, 
# max_freq_deviation=max_freq_deviation, 
# max_distance_deviation=max_distance_deviation, 
# max_genes_count_deviation=max_genes_count_deviation


cmd = [script2call, 
		'--user_snps_file', file_snplist, 
		'--output_dir', path_session_output,
		'--distance_type', distance_type
		'--distance_cutoff', distance_cutoff
		'match',
		'--N_sample_sets', N_sample_sets
		'--max_freq_deviation', max_freq_deviation
		'--max_distance_deviation', max_distance_deviation
		'--max_genes_count_deviation', max_genes_count_deviation
		'--set_file']

