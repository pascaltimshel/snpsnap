#!/usr/bin/env bash

lds2run=(0.1 0.2 0.3 0.4 0.6 0.7 0.8 0.9) # USE THIS - used 04/17/2014
#lds2run=(0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9)
#lds2run=()
# or {0..10..2}

for p_ld in ${lds2run[@]}
do
	cmd="./plink_matched_SNPs.py --output_dir_path /home/projects/tp/childrens/snpsnap/data/step2/1KG_full_queue_duprm --distance_type ld --distance_cutoff $p_ld"
	#echo $cmd
	#${!$cmd}
	eval $cmd &
	#$cmd
done


######## Experiment for testing importance of gene vs. transcription start #########

# lds2run=(0.1 0.5 0.9)
# for p_ld in ${lds2run[@]}
# do
# 	cmd="./plink_matched_SNPs.py --output_dir_path /home/projects/tp/childrens/snpsnap/data/step2/1KG_full_exp --distance_type ld --distance_cutoff $p_ld"
# 	eval $cmd &
# done
