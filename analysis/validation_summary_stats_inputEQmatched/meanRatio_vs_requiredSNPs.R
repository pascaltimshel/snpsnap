rm(list=ls())
library(ggplot2)
library(reshape2)
library(plyr)
library(stringr)
library(grid)

# loading multiplot function
source('../multiplot.R')

wd = '/Users/pascaltimshel/git/snpsnap/analysis/validation_summary_stats_inputEQmatched'
setwd(wd)
path.base = '/Users/pascaltimshel/git/snpsnap/analysis/validation_summary_stats_inputEQmatched'
path.compare = file.path(path.base, 'compare') # path.compare is a subdir in the path.base

## Read into a list of files:
path.datafiles <- path.compare
pat = "SNPsnap_rand100_defaultMatchCrit_n(.*)_excludeInputHLA_compare\\.csv$"
files <- list.files(path = path.datafiles, pattern = pat, full.names = TRUE) #full path
params <- str_match(files, 'SNPsnap_rand100_defaultMatchCrit_n(.*)_excludeInputHLA_compare.csv')[,2] # perl does not work. SAVING REQUIRED NUMBER OF SNPS IN PARAMs   
names(files) <- params
cat(names(files), sep="\n")

list_of_data <- llply(files, read.csv, stringsAsFactors=FALSE, na.strings = NULL) # files are COMMA seperated
x <- list_of_data[[1]]
str(x)

add_col <- function(dfname, dflist){
  df <- dflist[[dfname]]
  #df["param"] <- factor(dfname)
  df["param"] <- as.numeric(dfname) # OBS
  return (df)
}
dflist <- lapply(names(list_of_data), add_col, list_of_data) #adding column
names(dflist) <- names(list_of_data) #copy names
df.combined <- ldply(dflist) # merging, .id=NULL does not work!?
df.combined.clean <- df.combined[,-1] # REMOVING the automatically created index column (.id)
str(df.combined.clean)
df.combined.clean[df.combined.clean[,'origin']=="NA",'origin'] <- c("ratio") ## REPLACING "NA" STRING values in "origin" column with ratio
#df.combined.clean[,'param'] <- as.numeric(as.character(dat3$a)) # http://stackoverflow.com/questions/9480408/convert-factor-to-integer-in-a-data-frame


df.melt <- melt(df.combined.clean, id.vars=c("origin", "param"))
#melt(data, id.vars, measure.vars, variable.name = "variable", value.name = "value")

### Initializing plot list
plots <- list()  # new empty list

##### FREQ
p <- ggplot(subset(df.melt, variable=="mean_freq_bin" & origin=="ratio"), aes(x=param, y=value)) #fill=origin
p <- p + geom_bar(stat="identity", position="dodge")
p <- p + labs(title="Minor Allele Frequency")
p <- p + labs(x='Number of required SNPs', y=expression(paste(mu['input']/mu['matched'],' ','(%)', sep="")))
p <- p + coord_cartesian(ylim=c(100,125))
p <- p + scale_x_continuous(breaks=unique(df.melt[,'param'])) 
p <- p + theme(panel.grid.minor.x=element_blank(), panel.grid.major.x=element_blank()) # Hide all the x-axis gridlines
p <- p + theme(axis.text.x=element_text(size=14, angle=45, vjust=0.5), axis.text.y=element_text(size=14)) # adjust tickmarks size and angle
p <- p + theme(axis.title.x = element_text(size=16), axis.title.y = element_text(size=20))
p
plots[["freq"]] <- p

### GENE COUNT
p <- ggplot(subset(df.melt, variable=="mean_gene_count" & origin=="ratio"), aes(x=param, y=value)) #fill=origin
p <- p + geom_bar(stat="identity", position="dodge")
p <- p + labs(title="Gene Density")
p <- p + labs(x='Number of required SNPs', y=expression(paste(mu['input']/mu['matched'],' ','(%)', sep="")))
p <- p + coord_cartesian(ylim=c(100,125))
p <- p + scale_x_continuous(breaks=unique(df.melt[,'param'])) 
p <- p + theme(panel.grid.minor.x=element_blank(), panel.grid.major.x=element_blank()) # Hide all the x-axis gridlines
p <- p + theme(axis.text.x=element_text(size=14, angle=45, vjust=0.5), axis.text.y=element_text(size=14)) # adjust tickmarks size and angle
p <- p + theme(axis.title.x = element_text(size=16), axis.title.y = element_text(size=20))
p
plots[["gene_count"]] <- p

### DIST
p <- ggplot(subset(df.melt, variable=="mean_dist_nearest_gene_snpsnap" & origin=="ratio"), aes(x=param, y=value)) #fill=origin
p <- p + geom_bar(stat="identity", position="dodge")
p <- p + labs(title="Distance to Nearest Gene")
p <- p + labs(x='Number of required SNPs', y=expression(paste(mu['input']/mu['matched'],' ','(%)', sep="")))
p <- p + coord_cartesian(ylim=c(100,125))
p <- p + scale_x_continuous(breaks=unique(df.melt[,'param'])) 
p <- p + theme(panel.grid.minor.x=element_blank(), panel.grid.major.x=element_blank()) # Hide all the x-axis gridlines
p <- p + theme(axis.text.x=element_text(size=14, angle=45, vjust=0.5), axis.text.y=element_text(size=14)) # adjust tickmarks size and angle
p <- p + theme(axis.title.x = element_text(size=16), axis.title.y = element_text(size=20))
p
plots[["dist"]] <- p

### LD BUDDY
p <- ggplot(subset(df.melt, variable=="mean_friends_ld05" & origin=="ratio"), aes(x=param, y=value)) #fill=origin
p <- p + geom_bar(stat="identity", position="dodge")
p <- p + labs(title="LD Buddy Count")
p <- p + labs(x='Number of required SNPs', y=expression(paste(mu['input']/mu['matched'],' ','(%)', sep="")))
p <- p + coord_cartesian(ylim=c(100,125))
p <- p + scale_x_continuous(breaks=unique(df.melt[,'param'])) 
p <- p + theme(panel.grid.minor.x=element_blank(), panel.grid.major.x=element_blank()) # Hide all the x-axis gridlines
p <- p + theme(axis.text.x=element_text(size=14, angle=45, vjust=0.5), axis.text.y=element_text(size=14)) # adjust tickmarks size and angle
p <- p + theme(axis.title.x = element_text(size=16), axis.title.y = element_text(size=20))
p
plots[["ld_buddy"]] <- p


multiplot(plotlist = plots, cols=2)


####################### BLABLA ###################################
#c(seq(from = 10, to = 200, by = 10), seq(from = 52, to = 58, by = 2))
#c(seq(from = 10, to = 200, by = 10), rep("", 4))

######### things to try:
## A theme with white background and black gridlines.
#p + theme_bw()

## this worked
#named_vec_breaks <- unique(df.melt[,'param'])
#names(named_vec_breaks) <- unique(df.melt[,'param'])
#names(named_vec_breaks)
#p <- p + scale_x_continuous(breaks=named_vec_breaks)


################## LOTS OF BS - converting NA factor levels ####################
#df.combined.clean[,'origin'] <- factor(df.combined.clean[,'origin'], exclude=NULL) # set NA as an extra level, and not a missing value
#levels(df.combined.clean[,'origin'])

#levels(df.combined.clean[,'origin'])[levels(df.combined.clean[,'origin'])=="NA"] <- "ratio" ## REPLACING NA values in "origin" column with ratio

#is.na(levels(df.combined.clean[,'origin'])[df.combined.clean[,'origin']])

#df.combined.clean[df.combined.clean[,"origin"]==NA,"origin"] <- "ratio"
#df.combined.clean[is.na(df.combined.clean[,"origin"]),"origin"] <- "ratio" # DID NOT WORK! # REPLACING NA values in "origin" column with ratio
