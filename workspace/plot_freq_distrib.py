#!/usr/bin/env python
#import numpy as np
#import pylab as P

#import math



path_data = "/home/projects/tp/data/hapmap3/phase2"
file_data = "hapmap_CEU_r23a.frq"

print "here is a tester"

# Funciton to read in summary statiscs and bin SNPs into MAF percentiles
def get_snps_by_freq(infilename):
	snps_by_freq = {} 
	for bin in range(0,len(range(0,50,freq_bin_size)),1):
		snps_by_freq[bin] = []
	infile = open(infilename,'r')
	lines = infile.readlines()[1:]
	random.seed()
	random.shuffle(lines)
	for line in lines:
		words = line.strip().split()
	
		# Only consider SNPs with non-zero frequency
		if float(words[4]) > 0 and float(words[4]) < 1:
			bin = get_freq_bin(float(words[4]))

			# Add to correct bin if still space
			if len(snps_by_freq[bin]) < max_snps_per_bin:
				snps_by_freq[bin].append(words[1])
		infile.close()
	return snps_by_freq

