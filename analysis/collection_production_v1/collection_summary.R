rm(list=ls())
library(ggplot2)
library(reshape2)
library(plyr)



setwd('/Users/pascaltimshel/git/snpsnap/analysis/collection')

file.collection = '/Users/pascaltimshel/snpsnap/data/step3/1KG_snpsnap_production_v1/ld0.5/ld0.5_collection.tab_head100'
df.collection = read.delim(file.collection)


#df <- read.table(pipe("cut -f1,5,28 myFile.txt"))

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


