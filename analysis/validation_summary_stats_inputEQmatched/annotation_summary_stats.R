rm(list=ls())
library(ggplot2)
library(reshape2)
library(plyr)

setwd('/Users/pascaltimshel/git/snpsnap/analysis/validation_summary_stats_inputEQmatched')
#path.base = '/Users/pascaltimshel/snpsnap/validation_new'
path.base = '/Users/pascaltimshel/snpsnap/validation_07-08-2014'

#analysis_name = 'SNPsnap_rand100_defaultMatchCrit_n50_excludeInputHLA' ### SWICH
analysis_name = 'SNPsnap_rand100_defaultMatchCrit_n100_excludeInputHLA' ### SWICH
#analysis_name = 'SNPsnap_rand100_defaultMatchCrit_n500_excludeInputHLA' ### SWICH
#analysis_name = 'SNPsnap_rand100_defaultMatchCrit_n1000_excludeInputHLA' ### SWICH
#analysis_name = 'SNPsnap_rand100_defaultMatchCrit_n2500_excludeInputHLA' ### SWICH
#analysis_name = 'SNPsnap_rand100_defaultMatchCrit_n5000_excludeInputHLA' ### SWICH
#analysis_name = 'SNPsnap_rand100_defaultMatchCrit_n7500_excludeInputHLA' ### SWICH ~ 2787 s
#analysis_name = 'SNPsnap_rand100_defaultMatchCrit_n10000_excludeInputHLA' ### SWICH ~3000 s 

#analysis_name = 'SNPsnap_rand100_Match5_10_10_10_n1000_excludeInputHLA' ### SWITCH - different
path.analysis = file.path(path.base, analysis_name)

file.annotation.input = file.path(path.analysis, 'input_snps_annotated.tab')
file.annotation.matched = file.path(path.analysis, 'matched_snps_annotated.tab')

df.input = read.delim(file.annotation.input)
df.matched = read.delim(file.annotation.matched)
df.matched[,'set'] <- as.factor(df.matched[,'set']) # convert to factor
str(df.matched)


################################# Summarizing data #####################################
#freq_bin  gene_count  dist_nearest_gene_snpsnap friends_ld05

######### INPUT summary
df.stat.input <- summarise(df.input,
                         set=as.factor('input'), 
                         origin=as.factor('input'),
                         N = nrow(df.input),
                         mean_freq_bin = mean(freq_bin),
                         mean_gene_count = mean(gene_count),
                         mean_dist_nearest_gene_snpsnap = mean(dist_nearest_gene_snpsnap),
                         mean_friends_ld05 = mean(friends_ld05),
                         min_friends_ld05 = min(friends_ld05),
                         max_friends_ld05 = max(friends_ld05),
                         median_gene_count = median(gene_count)
)

# Start the clock!
ptm <- proc.time()

######### MATCHED summary
df.stat.matched <- ddply(df.matched, c("set"), summarise,
               origin=as.factor('matched'),
               N = length(set),
               mean_freq_bin = mean(freq_bin),
               mean_gene_count = mean(gene_count),
               mean_dist_nearest_gene_snpsnap = mean(dist_nearest_gene_snpsnap),
               mean_friends_ld05 = mean(friends_ld05),
               min_friends_ld05 = min(friends_ld05),
               max_friends_ld05 = max(friends_ld05),
               median_gene_count = median(gene_count)
               )

# Stop the clock
proc.time() - ptm

########### combining data
df.stat <- rbind(df.stat.input, df.stat.matched)

####### write STAT to csv file
csv.filename <- paste(analysis_name, "_stat.csv", sep="")
write.csv(df.stat, file=csv.filename, row.names=FALSE)

########### taking mean of all sets
df.compare <- ddply(df.stat, .(origin), summarise,
                    mean_freq_bin=mean(mean_freq_bin),
                    mean_gene_count=mean(mean_gene_count),	
                    mean_dist_nearest_gene_snpsnap=mean(mean_dist_nearest_gene_snpsnap),	
                    mean_friends_ld05=mean(mean_friends_ld05)
                    )
### taking ratio
df.ratio <- df.compare[1,-1]/df.compare[2,-1]*100
df.compare <- rbind.fill(df.compare, df.ratio)

####### write COMPARE to csv file
csv.filename <- paste(analysis_name, "_compare.csv", sep="")
write.csv(df.compare, file=csv.filename, row.names=FALSE)



