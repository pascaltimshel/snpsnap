rm(list=ls())
library(ggplot2)
library(reshape2)
library(plyr)



setwd('/Users/pascaltimshel/git/snpsnap/analysis/collection')

file.collection = '/Users/pascaltimshel/snpsnap/data/step3/ld0.5_collection_headtest.tab'
#file.collection = '/Users/pascaltimshel/snpsnap/data/step3/ld0.5_collection.tab'
df.collection = read.delim(file.collection)

#### OR ####
load('workspace_df_collection.RData')

head(df.collection)
str(df.collection)

summary(df.collection)

?summary

# Draw with black outline, white fill
q <- ggplot(df.collection, aes(x=gene_count))
q <- q + geom_histogram(binwidth=1)
q

q <- ggplot(df.collection, aes(x=freq_bin))
q <- q + geom_histogram(binwidth=1)
q

hist(df.collection$dist_nearest_gene)

?read.csv

