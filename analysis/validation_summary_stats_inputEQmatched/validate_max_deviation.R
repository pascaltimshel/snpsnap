rm(list=ls())
library(ggplot2)
library(reshape2)
library(plyr)

setwd('/Users/pascaltimshel/git/snpsnap/analysis/validation_summary_stats_inputEQmatched')
path.base = '/Users/pascaltimshel/snpsnap/validation_new'
#analysis_name = 'SNPsnap_rand500_Match2_10_10_10_n500_excludeInputHLA' ### SWICH
analysis_name = 'SNPsnap_rand500_defaultMatchCrit_n500_excludeInputHLA' ### SWICH
path.analysis = file.path(path.base, analysis_name)

file.annotation.input = file.path(path.analysis, 'input_snps_annotated.tab')
file.annotation.matched = file.path(path.analysis, 'matched_snps_annotated.tab')

### Reading data
df.input = read.delim(file.annotation.input)
df.matched = read.delim(file.annotation.matched)

### Allowable deviations
max_freq_deviation=5
max_genes_count_deviation=50
max_distance_deviation=50
max_ld_buddy_count_deviation=50

delta_genes_count_deviation = max_genes_count_deviation/100*c(-1, 1)

### Extracting sample SNP
sample_snpID = c('14:69873335') # gene_count=1
#sample_snpID = c('8:48128910') # gene_count=24
sample_snpID_gene_count = df.input[df.input[,'snpID']=='8:48128910',]$gene_count
df.sample.snp <- subset(df.matched, input_snp==sample_snpID, select=c(snpID, gene_count)) 
#df.sample.snp <- df.matched[df.matched[,'input_snp'] %in% sample_snpID,]
#x <- ddply(df.sample.snp, ) # DID NOT FINISH THIS
range(df.sample.snp$gene_count)

t <- findInterval(df.sample.snp[,'gene_count'], sample_snpID_gene_count*(1+delta_genes_count_deviation) )

# Could just use the findInterval function:
#   
#   findInterval(x, c(15,20) ) == 1
# 
# findInterval returns a numeric vector indicating which bin(s) the  
# argument vector element(s) fall(s) into. Items below the lower bound  
# get a zero which means if the result is used as an index the there  
# will be no item chosen for that value. Items above the maximal  
# boundary get a value of n+1 where n is the number of bins. (Very useful function.)

######### INPUT summary 
### OLD APPROACH
#df.snpcomparison.input <- df.input
#df.snpcomparison.input[,'origin'] <- as.factor('input_df')
df.snpcomparison.input <- ddply(df.input, c("snpID"), summarise,
                                  origin = as.factor('input_df'),
                                  mean_freq_bin = mean(freq_bin),
                                  mean_gene_count = mean(gene_count),
                                  mean_dist_nearest_gene_snpsnap = mean(dist_nearest_gene_snpsnap),
                                  mean_friends_ld05 = mean(friends_ld05),
                                  median_gene_count = median(gene_count)
)

######### MATCHED summary
df.snpcomparison.matched <- ddply(df.matched, c("input_snp"), summarise,
                         origin = as.factor('matched_df'),
                         mean_freq_bin = mean(freq_bin),
                         mean_gene_count = mean(gene_count),
                         mean_dist_nearest_gene_snpsnap = mean(dist_nearest_gene_snpsnap),
                         mean_friends_ld05 = mean(friends_ld05),
                         median_gene_count = median(gene_count)
)

names(df.snpcomparison.matched)[names(df.snpcomparison.matched) == 'input_snp'] <- 'snpID' # RENAMING COLUM
df.snpcomparison <- rbind.fill(df.snpcomparison.input, df.snpcomparison.matched) # could also use rbind, but rbind.fill works with unequal number of columns

df.snpcomparison.melt <- melt(df.snpcomparison, id.vars=c("snpID", "origin"), measure.vars=c("mean_gene_count", "median_gene_count"))

x <- df.snpcomparison.melt[df.snpcomparison.melt$origin=='input_df', "value"]
y <- df.snpcomparison.melt[df.snpcomparison.melt$origin=='matched_df', "value"]
tmp <- data.frame(input_df=x,matched_df=y)

plot(x,y)
abline(0,1)
#ggplot(df.snpcomparison.melt, )


