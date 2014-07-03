rm(list=ls())
library(ggplot2)
library(reshape2)
library(plyr)

# loading multiplot function
source('../multiplot.R')

# Columns in COLLECTION - validated 07/02/2014
#1=snpID
#2=freq_bin
#3=gene_count
#4=dist_nearest_gene_snpsnap
#5=dist_nearest_gene
#6=dist_nearest_gene_located_within
#7=loci_upstream
#8=loci_downstream
#9=ID_nearest_gene_snpsnap
#10=ID_nearest_gene
#11=ID_nearest_gene_located_within
#12=ID_genes_in_matched_locus
#13=friends_ld01
#....
#21=friends_ld09



setwd('/Users/pascaltimshel/git/snpsnap/analysis/collection_production_v1')
#file.collection = '/Users/pascaltimshel/snpsnap/data/step3/1KG_snpsnap_production_v1/ld0.5/ld0.5_collection.tab_head100'
file.collection = '/Users/pascaltimshel/snpsnap/data/step3/1KG_snpsnap_production_v1/ld0.5/ld0.5_collection.tab'

## READING whole file
#df.collection = read.delim(file.collection)

### READING certain columns using pipe()
#2=freq_bin
#3=gene_count
#4=dist_nearest_gene_snpsnap
df.collection <- read.delim(pipe(paste("cut -f2,3,4,17", file.collection))) # paste has sep=" " by default
# CONSIDER: colClasses=c("NULL", NA, NA)

### Sumary stuff
head(df.collection)
str(df.collection)
#summary(df.collection)

############################ BINNING DATA ######################

hist.dist_nearest_gene_snpsnap <- hist(df.collection[,'dist_nearest_gene_snpsnap'], breaks=100, plot=T)
#range gene_dist = 5371433
#breaks = 100
# ---> binwidth = 5371433/100 ~= 55000

############################# PLOTS ##############################
### Initializing plot list
plots <- list()  # new empty list

### FREQ
p <- ggplot(df.collection, aes(x=freq_bin))
p <- p + geom_histogram(binwidth=1) # range=49
p <- p + labs(x='Minor Allele Frequency', y='Count')
p
plots[["freq"]] <- p

### GENE COUNT
p <- ggplot(df.collection, aes(x=gene_count))
p <- p + geom_histogram(binwidth=1) # range=174
p <- p + labs(x='Gene Density', y='Count')
p
plots[["gene_count"]] <- p


### GENE DIST - OBS: be careful about the binwidth
p <- ggplot(df.collection, aes(x=dist_nearest_gene_snpsnap))
p <- p + geom_histogram(binwidth=55000) # range=5371433
p <- p + labs(x='Distance to Nearest Gene', y='Count')
p
plots[["dist_nearest_gene_snpsnap"]] <- p

### LD BUDDY COUNT
p <- ggplot(df.collection, aes(x=friends_ld05))
p <- p + geom_histogram(binwidth=10) #range=3646
p <- p + labs(x='LD buddies', y='Count')
p
plots[["friends_ld05"]] <- p


#layout <- matrix(c(1, 1, 2, 3, 4, 5), nrow = 2, byrow = TRUE)
#multiplot(plotlist = plots, layout = layout)
multiplot(plotlist = plots, cols=2)
