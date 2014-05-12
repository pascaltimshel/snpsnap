#! /usr/bin/python

import glob

path = "/home/projects/depict/data/gwascatalog/140201/"

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

files = glob.glob("%s*.txt"%path)
for filename in files:

	snps = read_snps(filename)

	pheno = filename.split("/")[-1].replace(".txt","")
	print("%s: %s"%(pheno,len(snps)))

	# du overtager her ..
	# mangler at mappe fra rsID til position..
#dir_in="/home/projects/tp/data/1000G/data/phase1"
#prefix_in="CEU_GBR_TSI_unrelated.phase1_release_v3.20101123.snps_indels_svs.genotypes