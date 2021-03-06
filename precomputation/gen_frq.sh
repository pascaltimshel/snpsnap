#!/usr/bin/env bash
#USAGE: Run this program in background or via cluster:
#	gen_testdata.sh &
#	OR
#	xmsub -de -o gen_frq.log.out -e gen_frq.log.err -r y -q cbs -N gen-freq -l mem=20gb,walltime=604800,flags=sharedmem /home/projects/tp/childrens/snpsnap/git/gen_frq.sh
#OUTPUT: 	all output is writte to ../data/<call_param_name>/<prefix>

## Program outline
#1) process "raw" data using plink with user criteria
	# possibly set pthin to generate test data
#2) check for dublicates in .bim file via call to python script
#3) generate .frq files from processed data via plink

# Make the shell exit with an error when you reference an undefined variable.
# set -u 

## START TIME
T="$(date +%s)" # Get time as a UNIX timestamp (seconds elapsed since Jan 1, 1970 0:00 UTC)

###################################### PARAMETERS ######################################
#@@@@@@@@@@@@@@@@@@ Important switch - if value is < 1 test dataset is created @@@@@@@@@
pthin=0.02 #To keep only a random e.g. 20% of SNPs
#Parameter for --thin must be 0<x<1
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

pmaf=0.01 # Only include SNPs with MAF >= 0.01.
#pmaf=0 # include all SNPs
pgeno=0.1
phwe=0.000001 #10^-6
#phwe=0.001 # default value?

### INPUT dir params
dir_in="/home/projects/tp/data/1000G/data/phase1"
prefix_in="CEU_GBR_TSI_unrelated.phase1_release_v3.20101123.snps_indels_svs.genotypes"
data_in=$dir_in/$prefix_in

dir_out="/home/projects/tp/childrens/snpsnap/data/step1"

### OUTPUT dir params
### Setting call variables
prefix_out="CEU_GBR_TSI_unrelated.phase1" # THIS IS IMPORTANT
if [ -n "$pthin" ]; then # "if set" (string variable is non-empty/non-zero). That is, is pthin given
	# TEST DATA dir
	dir_output="${dir_out}/test_thin${pthin}_rmd" # e.g. /home/projects/tp/childrens/snpsnap/data/step1/test_thin0.05
	call="--bfile $data_in\
	 --thin $pthin\
	 --maf $pmaf\
	 --geno $pgeno\
	 --hwe $phwe\
	 --make-bed\
	 --out ${dir_output}/${prefix_out}\
	 --noweb"
else
	# FULL DATA (	 --thin $pthin REMOVED)
	dir_output="${dir_out}/full_no_pthin_rmd"
	call="--bfile $data_in\
	 --maf $pmaf\
	 --geno $pgeno\
	 --hwe $phwe\
	 --make-bed\
	 --out ${dir_output}/${prefix_out}\
	 --noweb"
fi

if [ -d ${dir_output} ]; then
	echo "Output dir ${dir_output}: alread exists. Please remove it before continuing. Exiting"
	exit 1
	#echo "Removing existing output dir ${dir_output}"
	#rm -r ../data/${dir_output}
fi
mkdir ${dir_output}
#mkdir -p ../data/${dir_output} # no error if existing, make parent directories as needed

# ##################################### Make test file ######################################

# @@@@@@@@@@@@@@@@@@ Prim CALL @@@@@@@@@@@@@@@@@@
# Note the space indentation to seperate arguments
echo "making call to plink"
echo "$call"
plink $call &> ${dir_output}/tmp1.$$.log

# @@@@@@@@@@@@@@@@@@ Remove Dublicates CALL @@@@@@@@@@@@@@@@@@

call_dup="--input ${dir_output}/${prefix_out}.bim" # e.g. --input /home/projects/tp/childrens/snpsnap/data/step1/full_no_pthin/CEU_GBR_TSI_unrelated.phase1.bim
# 
echo "making call to get_duplicates.py"
echo "$call_dup"
/home/projects/tp/childrens/snpsnap/git/get_duplicates.py $call_dup

# @@@@@@@@@@@@@@@@@@ Exclude duplicates CALL @@@@@@@@@@@@@@@@@@
# Notice new out prefix
prefix_out_clean="${prefix_out}_dup_excluded"

call_excl="--bfile ${dir_output}/${prefix_out}\
	 --exclude ${dir_output}/duplicates.txt\
	 --make-bed\
	 --out ${dir_output}/${prefix_out_clean}\
	 --noweb"
plink $call_excl &> ${dir_output}/tmp2.$$.log

# @@@@@@@@@@@@@@@@@@ FREQ CALL @@@@@@@@@@@@@@@@@@
#path_parrent=$(dirname `pwd`)

call_stat="--bfile ${dir_output}/${prefix_out_clean}\
 --out ${dir_output}/${prefix_out_clean}\
 --freq\
 --noweb"

#call_stat="--bfile `pwd`/results/${dir_output}/${prefix_out}\
# --out ./results/${dir_output}/${prefix_out}\
# --freq\
# --noweb"

echo "making call to plink"
echo "$call_stat"
# #output in two different files: plink 2> error.log 1> output.lol
# #output into same file (all equivalent): 
	#plink &> combined.log (special syntax)
	#plink >& combined.log (special syntax)
	#plink > combined.log 2>&1
plink $call_stat &> ${dir_output}/tmp3.$$.log

###################################### CLEAING and PRINT RUNTIME ######################################
T="$(($(date +%s)-T))" ## END TIME

script_name=`basename $0`
t_seconds=${T}
t_min=$((T/60))
t_hours=$((T/3600))
echo "`date`
$script_name with PID$$ completed
RUNTIME
$t_seconds s
$t_min min
$t_hours h" | tee ${dir_output}/tmp.runtime.$$.log


## Cleaning tmp log file
#rm tmp1.$$.log
#rm tmp2.$$.log


###################################### OLD STUFF ######################################
#call="--bfile $mydata --thin $pthin --maf $pmaf --make-bed --out ${dir_output}/CEU_GBR_TSI_unrelated.phase1.testset --noweb"

# DOES NOT WORK:
#plink $call > /dev/null & ## sending output to bit-bucket (trash)

# ### OUTPUT dir params
# path_parrent=$(dirname `pwd`)

# if [ -n "$pthin" ]; then # "if set" (string variable is non-empty/non-zero). That is, is pthin given
# 	# TEST DATA dir
# 	dir_output="test_thin${pthin}_MAF=0"
# else
# 	dir_output="full_no_pthin" 
# fi

# prefix_out="CEU_GBR_TSI_unrelated.phase1"
# dir_output_full=$path_parrent/data/${dir_output} ## IMPORTANT PATH

# if [ -d ${dir_output}_full ]; then
# 	echo "Removing existing output dir ${dir_output}"
# 	rm -r ${dir_output}_full
# fi
# mkdir -p ${dir_output}_full # no error if existing, make parent directories as needed


###################################### MIX NOTES ######################################

#plink --bfile /home/projects9/tp/childrens/snpsnap/data/all_no_pthin_ok/CEU_GBR_TSI_unrelated.phase1 --out ../data/all_no_pthin_ok/CEU_GBR_TSI_unrelated.phase1 --freq --noweb


###################################### NOTES ######################################
# echo plink --bfile $mydata --thin 0.2

# Remove a subset of SNPs
# --> write snps with freq < 1 % to file and exclude them
# plink --file data --exclude mysnps.txt


# plink --bfile mydata --maf 0.05 --geno 0.05 --write-snplist
# which generates a file
#      plink.snplist
# This file is simply a list of included SNP names, i.e. the same SNPs that a --recode or --make-bed statement would have produced in the corresponding MAP or BIM files

# Info on http://pngu.mgh.harvard.edu/~purcell/plink/data.shtml#bed
# The --make-bed option does the same as --recode but creates binary files;

# Output root file name (i.e. different to "plink") by using the --out option
# --out mydata2


#################### BED files ######################################
# plink.bed      ( binary file, genotype information )
# plink.fam      ( first six columns of mydata.ped ) 
# plink.bim      ( extended MAP file: two extra cols = allele names)


#load a binary file, just use --bfile instead of --file
#	plink --bfile mydata

# When creating a binary ped file, the MAF and missingness filters are set to include everybody and all SNPs. 
# If you want to change these, use --maf, --geno, etc, to manually specify these options: for example,
# 	plink --file mydata --make-bed --maf 0.02 --geno 0.1


################## Filtering/Tresshld ##############
# http://pngu.mgh.harvard.edu/~purcell/plink/thresh.shtml#maf



