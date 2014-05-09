

file.orig_frq = "/home/projects/tp/data/1000G/data/phase1/CEU_GBR_TSI_unrelated.phase1_release_v3.20101123.snps_indels_svs.genotypes.frq" # size = 1.9 GB
file.processed_frq = "/home/projects/tp/childrens/snpsnap/data/step1/full_no_pthin_rmd/CEU_GBR_TSI_unrelated.phase1_dup_excluded.frq" # size = 452 MB
 # CHR          SNP   A1   A2          MAF  NCHROBS
 #   1   rs58108140    A    G       0.2052      536
 #   1  rs189107123    G    C      0.01306      536
 #   1  rs180734498    T    C       0.1343      536
 #   1  rs144762171    C    G      0.02425      536
 #   1  rs201747181    T   TC      0.01119      536
 #   1  rs151276478    C    T      0.01306      536


file.batch_sizes = "/home/projects/tp/childrens/snpsnap/data/step2/1KG_full_duprm/ld0.5/log/bin_size_distribution.txt"
# bin     size
# 0       50000
# 1       50000
# 2       50000
# 3       50000
# 4       50000
# 5       50000
# 6       50000
# 7       50000


df.orig <- read.table(file=file.orig_frq, colClasses=c(rep("NULL", 4), "numeric", "NULL"), header = TRUE, sep= "")
df.processed <- read.table(file=file.processed_frq, colClasses=c(rep("NULL", 4), "numeric", "NULL"), header = TRUE, sep= "")
df.batch_sizes <- read.table(file=file.batch_sizes, header = TRUE, sep= "")
#orig ---> 305754576 bytes == 291 MB
#processed --> 74068760 bytes = 70 Mb
#object.size(df.processed) 

###################################### Orig ######################################
# HIST for orig
breaks <- c(seq(0,0.5,0.01))
hist.orig <- hist(df.orig[,1], breaks=breaks, plot=F)


# write file
write.table(df, file = "binned_step0.1_orig.csv", sep=',', quote=F, row.names=F)

### making plot
pdf('hist_step0.1_orig.pdf')
hist(df.orig[,1], breaks=breaks)
dev.off()

###################################### Processed ######################################
breaks <- c(seq(0,0.5,0.01))
hist.processed <- hist(df.processed[,1], breaks=breaks, plot=F)

# write file
write.table(df, file = "binned_step0.1_proccessed.csv", sep=',', quote=F, row.names=F)

### making plot
pdf('hist_step0.1_proccessed.pdf')
hist(df.processed[,1], breaks=breaks)
dev.off()



###################################### Making data frame ######################################
breaks <- seq(0,0.5,0.01) # 0,0.01,...,0.49,0.50 ==> length=51
hist.orig <- hist(df.orig[,1], breaks=breaks, plot=F)
hist.processed <- hist(df.processed[,1], breaks=breaks, plot=F)

df <- data.frame(breaks=head(breaks, n=-1), # removing last element 0.50, to make the length of the vector fit in the dataframe
	orig.freq=hist.orig$counts,
	processed.freq=hist.processed$counts,
	#batch_sizes.count=hist.processed$batch_sizes
	df.batch_sizes[,2] # do not need hist call: already count data
	)

# write file
write.table(df, file = "binned_combined_step0.1_proccessed.csv", sep=',', quote=F, row.names=F)



# The percentage of answers that were not correct
#qplot(incorrect_Hist$mids,y=incorrect_Bar_Values, geom="bar", stat="identity", ylim=c(0,1))


