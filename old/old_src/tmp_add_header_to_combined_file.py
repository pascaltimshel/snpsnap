#!/usr/bin/env python2.7

import sys
import glob
import os
import time

# "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/ld0.9/combined.tab",
# "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/kb300/combined.tab",
# "/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/ld0.5/combined.tab",

files2edit = ["/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/kb1000/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/ld0.3/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/kb400/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/ld0.2/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/kb600/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/kb800/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/ld0.7/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/kb200/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/kb500/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/kb700/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/ld0.1/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/ld0.8/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/kb100/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/kb900/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/ld0.6/combined.tab",
"/cvar/jhlab/snpsnap/data/step2/1KG_snpsnap_production_v2/EUR/ld0.4/combined.tab"]

header_str = "rsID freq_bin snp_maf snp_chr snp_position gene_count dist_nearest_gene_snpsnap dist_nearest_gene_snpsnap_protein_coding dist_nearest_gene dist_nearest_gene_located_within loci_upstream loci_downstream ID_nearest_gene_snpsnap ID_nearest_gene_snpsnap_protein_coding ID_nearest_gene ID_nearest_gene_located_within HGNC_nearest_gene_snpsnap HGNC_nearest_gene_snpsnap_protein_coding LD_boddies flag_snp_within_gene flag_snp_within_gene_protein_coding ID_genes_in_matched_locus"
header_str_tab_sep = "\t".join(header_str.split())

for file2edit in files2edit:
	print "processing {}".format(file2edit)
	old_file = os.path.dirname(file2edit) + "/old_combined.tab"
	#os.rename(src, dst)
	os.rename(file2edit, old_file) # now there should be no file called "/combined.tab"

	#new_file = os.path.dirname(file2edit) + "/combined.tab"

	with open(file2edit, 'w') as f:
		f.write(header_str_tab_sep+'\n')
		with open(old_file, 'r') as f_old:
			for line in f_old:
				f.write(line)
