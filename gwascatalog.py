#!/usr/bin/env python2.7

import glob
import collections
import time
import os

# # Thu Jan 30 15:17:54 CET 2014
# # SNPs found (21): rs10768122, rs10876864, rs11203203, rs1393350, rs1417210, rs1464510, rs16872571, rs2111485, rs2236313, rs229527, rs2456973, rs3757247, rs3814231, rs4409785, rs4766578, rs4822024, rs4908760, rs638893, rs706779, rs8192917, rs853308
# # SNPs not found (8): rs1129038, rs11966200, rs3806156, rs59374417, rs6904029, rs7758128, rs9468925, rs9926296
# snps    chr     locus_start     locus_stop      nearest_genes   genes_in_locus
# rs10768122      11      35241228        35374043        ENSG00000110436 ENSG00000026508 ENSG00000110436

def read_snps(filename):
	with open(filename,"r") as f:
		snps = []
		for line in f.readlines()[1:]:
			if "SNPs" in line and "rs" in line:
				parts = line.strip().split(": ")	
				snps += parts[1].split(", ")
			else: 
				break
	return snps


def read_bim(filename):
	mapper_rsID_2_chrposID = {}
	mapper_chrposID_2_rsID = {}
	duplicates_rsID = collections.defaultdict(int)
	duplicates_chrposID = collections.defaultdict(int)
	print "START: reading .bim file %s" % filename
	start_time = time.time()
	with open(filename, 'r') as f:
		lines = f.readlines()
		for line in lines:
			cols = line.strip().split()
			(chr_no, rsID, pos) = (cols[0], cols[1], cols[3])
			chrposID = chr_no +':'+ pos
			
			# if not chrposID in mapper_chrposID_2_rsID:
			# 	mapper_chrposID_2_rsID[chrposID] = rsID
			# else:
			# 	duplicates_chrposID[chrposID] += 1
			# if not duplicates_chrposID[chrposID]:
			# 	if not rsID in mapper_rsID_2_chrposID:
			# 		mapper_rsID_2_chrposID[rsID] = chrposID
			# 	else:
			# 		duplicates_rsID[rsID] += 1
			if not rsID in mapper_rsID_2_chrposID:
				mapper_rsID_2_chrposID[rsID] = chrposID
			else:
				duplicates_rsID[rsID] += 1
		for (k,v) in duplicates_rsID.items():
			print "{rsID}\t{count}".format(rsID=k, count=v)
		elapsed_time = time.time() - start_time
		print "END: read .bim file in %s s (%s min)" % ( elapsed_time, elapsed_time/60 )
		return mapper_rsID_2_chrposID


def main():
	mapper_rsID_2_chrposID = read_bim(file_bim)

	file_log = path_output+'/not_mapped.log'
	if os.path.exists(file_log):
		os.remove(file_log)

	files = glob.glob("%s/*.txt"%path_catalog)
	for (counter, filename) in enumerate(files, start=1):
		print "processing file #%d/#%d: %s" % (counter, len(files), filename )
		snps = read_snps(filename)

		pheno = filename.split("/")[-1].replace(".txt","")
		print "%s, found %s SNPs in phenotype file" % ( pheno,len(snps) )

		chrposIDs = []
		snps_not_mapped = []
		for snp in snps:
			if mapper_rsID_2_chrposID.get(snp):
				chrposIDs.append(mapper_rsID_2_chrposID.get(snp))
			else:
				snps_not_mapped.append(snp)
		print "could map %d out of %d SNPs with rsID to chrposID" % ( len(chrposIDs), len(snps) )
		with open(path_output+"/"+pheno+'.txt', 'w') as f_out:
			f_out.write("\n".join(chrposIDs))

		if snps_not_mapped: # only if non-empty
			with open(file_log, 'a') as f_log:
				f_log.write( "\n".join([pheno+':\t'+elem for elem in snps_not_mapped]) + '\n' ) #[s + mystring for s in mylist]




#END: read .bim file in 27.6576800346 s (0.460961333911 min)
#208  416 6115 not_mapped.log

# BIGbim
#END: read .bim file in 107.690361023 s (1.79483935038 min)
#160  320 4684 not_mapped_BIGbim.log

## Constants

#path = "/home/projects/depict/data/gwascatalog/140201/"
path_catalog = "/home/projects/tp/childrens/snpsnap/data/gwas/gwascatalog_140201"
#file_bim = "/home/projects/tp/data/1000G/data/phase1/CEU_GBR_TSI_unrelated.phase1_release_v3.20101123.snps_indels_svs.genotypes.bim" #1.1G
file_bim = "/home/projects/tp/childrens/snpsnap/data/step1/full_no_pthin_rmd/CEU_GBR_TSI_unrelated.phase1_dup_excluded.bim" #263M

path_output = "/home/projects/tp/childrens/snpsnap/data/gwas/gwascatalog_140201_lists"

#### .bim file:
     # chromosome (1-22, X, Y or 0 if unplaced)
     # rs# or snp identifier
     # Genetic distance (morgans)
     # Base-pair position (bp units)
# 1       rs58108140      0       10583   A       G
# 1       rs189107123     0       10611   G       C
# 1       rs180734498     0       13302   T       C
# 1       rs144762171     0       13327   C       G
# 1       rs201747181     0       13957   T       TC
# 1       rs151276478     0       13980   C       T
# 1       rs140337953     0       30923   G       T


if __name__ == '__main__':
	main()
