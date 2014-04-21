#!/usr/bin/env python2.7

import sys
import os
import argparse
import collections

import pdb

# original data, job submission
#xmsub -de -o get_dup.out -e get_dup.err -r y -q cbs -N get_dup -l mem=20gb,walltime=604800,flags=sharedmem /home/projects/tp/childrens/snpsnap/git/get_duplicates.py --input /home/projects/tp/data/1000G/data/phase1/CEU_GBR_TSI_unrelated.phase1_release_v3.20101123.snps_indels_svs.genotypes.bim


#def makehash():
#	return collections.defaultdict(makehash) 

def get_duplicates(inputfile, outputdir):
	snps_seen = {}
	outputfile = outputdir+"/duplicates.txt"
	dup = collections.defaultdict(list)
	with open(outputfile, 'w') as outfile:
		with open(inputfile, 'r') as infile:
		
		# .bim file == 'extended' MAP file - each line of the MAP file describes a single marker
		
	 	# c1=chromosome (1-22, X, Y or 0 if unplaced)
	    # c2=rs# or snp identifier
	    # c3=Genetic distance (morgans)
	    # c4=Base-pair position (bp units)
	    # c5=allele names (extra col in .bim file comared to MAP)
	    # c6=allele names (extra col in .bim file comared to MAP)
		# 1       rs202029170     0       247916  C       CAGG
		# 1       rs200079338     0       249275  GT      G
		# 1       rs115018998     0       249276  C       T
		# 1       rs72502741      0       251627  A       AC
		# 1       rs199745078     0       255923  GTC     G
		# 1       rs182870673     0       362905  G       T

			lines = infile.readlines()
			for line in lines:
				cols = line.strip().split()
				rsID = cols[1]
				pos = cols[3]
				if not rsID in snps_seen:
					snps_seen[rsID] = pos
				else:
					# pdb.set_trace()
					#if len(snps_seen[rsID]) == 1: # if first time we see duplicate
					if len(dup[rsID]) == 0: # if first time we see duplicate
						dup[rsID].extend([snps_seen[rsID], pos]) # save previous seen rs position and duplicate position
					else:
						dup[rsID].append(pos)
		print "Writting to file: %s" % outputfile
		print "rsID\tCount\tPositions"
		for rs, pos in dup.items():
			print "%s\t%s\t%s" % (rs, len(pos), ";".join(pos))
			# Now write to file
			outfile.write(rs+"\n")


#print "************************************"
#print "%s dublicate in .bim file" % cols[1]
#print "Dublicates are at position: %s and %s" %	(snps_seen[cols[1]], cols[3])
#print "Retaining entry with lowest chromosomal position: %s" % keep


#Parse Arguments
arg_parser = argparse.ArgumentParser("Finds duplicates in genotype data and write them to filename 'duplicates.txt' in the input dir")
arg_parser.add_argument("--input", help="input .bim file", required=True)
# e.g. /home/projects/tp/childrens/snpsnap/data/step1/full_no_pthin/CEU_GBR_TSI_unrelated.phase1.bim
args = arg_parser.parse_args()

inputfile = args.input
outputdir = os.path.dirname(inputfile)

get_duplicates(inputfile, outputdir)
