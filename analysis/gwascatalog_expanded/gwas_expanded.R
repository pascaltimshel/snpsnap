rm(list=ls())
library(ggplot2)
library(reshape2)
library(plyr)
library(stringr)

wd <- '/Users/pascaltimshel/git/snpsnap/analysis/gwascatalog_expanded'
setwd(wd)

header_str = "gwas;rating_insufficient;pct_insufficient;N_insufficient;N_input_snps;rating_size;pct_size;median_size;N_sample_sets"
header_cols = unlist(strsplit(header_str, split=';')) #head_cols = unlist(str_split(header_str, perl(';')))

## Read into a list of files:
path.datafiles <- wd
pat = "subprocess_gwastable.*\\.tab$"
files <- list.files(path = path.datafiles, pattern = pat, full.names = TRUE) #full path
params <- str_match(files, 'subprocess_gwastable.(.*).tab')[,2] # perl does not work
names(files) <- params
cat(names(files), sep="\n")

list_of_data <- llply(files, read.delim, col.names=header_cols, stringsAsFactors=FALSE)#row.names = 1 --> NO!
x <- list_of_data[['1000.2.5.5']]

add_col <- function(dfname, dflist){
  df <- dflist[[dfname]]
  df["param"] <- factor(dfname)
  return (df)
}
dflist <- lapply(names(list_of_data), add_col, list_of_data) #adding column
names(dflist) <- names(list_of_data) #copy names
#x <- dflist[[1]]
df <- ldply(dflist) # merging

tmp <- df[df[,'gwas']=='Age-related_macular_degeneration',]
tmp1 <- df[df[,'gwas']=='Alzheimers_disease',]


############### MAKING DATA FRAMEs
dfmelt <- melt(df, id.vars=c('param','gwas'), measure.vars=c('pct_insufficient'))
dfmelt <- melt(df, id.vars=c('param','gwas'), measure.vars=c('pct_size'))

dfmelt <- melt(df, id.vars=c('param','gwas'), measure.vars=c('pct_insufficient','pct_size'))

################### BOX PLOT
#str(dfmelt)
p <- ggplot(dfmelt, aes(x=param, y=value, fill=variable)) + geom_boxplot()
p <- p + geom_jitter() #+ coord_flip()
p

## NOTE TO SELF: use 5.20.20 for 10,000

######################## TEXT PLOT for specific data frame
#dfwork <- dflist[['1000.2.5.5']]
dfwork <- dflist[['1000.5.20.20']]
p <- ggplot(dfwork, aes(x=1, y=pct_insufficient, label=rating_insufficient)) + geom_text()# + geom_jitter()
p


############## Quantiles ######################
get_quantiles <- function(df) {
  #param <- as.character(df[1,'param']) # OBS: not nice code
  #cat(param)
  q1 <- quantile(df[,'pct_insufficient'], c(.20, .40, .60, .80, 1))
  q2 <- quantile(df[,'pct_size'], c(.20, .40, .60, .80, 1))
  #df2return <- data.frame(quantile_val=q, quantile_id=names(q), orig=factor(param)) # orig NOT NEEDED, created automatically
  df2return <- data.frame(q_insuf=q1, q_size=q2, quantile_id=names(q1)) #OBS: q1 and q1 must have same props vector
  return (df2return)
}

df.quantile <- ldply(dflist, get_quantiles) # making df containing quantiles

# OBS: switch y=[q_size; q_insuf]
p <- ggplot(df.quantile, aes(x=.id, y=q_insuf, color=.id, label=quantile_id)) + geom_point() + geom_text()
p <- p + labs(title="Insufficien quantiles", xlab='param')
p  

###
##########################





#################### TEST CODE #################

p <- ggplot(dfmelt, aes(x=param, y=value, fill=variable)) + geom_jitter()
p
p <- p + stat_quantile(quantiles = 0.5) #+ coord_flip()
p

#################### OLD CODE #################


######################## COPY PASTE #####################
### Density plot

p <- ggplot(data = d) + theme_bw() + geom_density(aes(x=x, y = ..density..), color = 'black')
# new code is below
q5 <- quantile(x,.05)
q95 <- quantile(x,.95)
medx <- median(x)
x.dens <- density(x)
df.dens <- data.frame(x = x.dens$x, y = x.dens$y)
p + geom_area(data = subset(df.dens, x >= q5 & x <= q95), aes(x=x,y=y), fill = 'blue') + geom_vline(xintercept = medx)
