#!/usr/bin/env python2.7

# Production V1
# This script was written by Pascal June 18 2014.
# The queue parameter is "??"


#logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)

import sys
import os
import subprocess 

import pdb

import collections
import time
import datetime

import tarfile

#import threading
import multiprocessing

current_script_name = os.path.basename(__file__)
start_time_script = time.time()
batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')

###################################### Param statements ######################################
#param_list=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
#distance_type = 'ld' # choose 'ld' or 'kb'

param_list=[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
distance_type = 'kb' # choose 'ld' or 'kb'
###############################################################################

output_path = '/home/projects/tp/childrens/snpsnap/data/transfer'
if not os.path.exists(output_path):
	print "UPS: output path %s does not exist. Fix it! Exiting..." % output_path
	sys.exit(1)


###################################### Python tarfile version - NOT PARALLEL ######################################
### TESTED AND WORKS!

def make_gz_tar_file(output_filename, source_dir):
	""" This function writes a gzipped tar file (.tar.gz) to output_filename. The archive name is the name of the source_dir """
	# TarFile.add(..., recursive=True,...): Note that by default a directory will be added recursively: every file and folder under it will be included.
	with tarfile.open(output_filename, "w:gz") as tar:
		tar.add(source_dir, arcname=os.path.basename(source_dir))

# tar_filenames = []

# for param in param_list:
# 	start_time = time.time()
# 	source_dir = "/home/projects/tp/childrens/snpsnap/data/step2/1KG_snpsnap_production_v1" + '/' + distance_type + str(param) + '/' + 'stat_gene_density'  ## e.g /step2/1KG_snpsnap_production_v1/ld0.5/stat_gene_density
	
# 	tar_filename = 'stat_gene_density_{type}_{cutoff}.{ext}'.format(type=distance_type, cutoff=param, ext='tar.gz')
# 	tar_filenames.append(tar_filename)

# 	tarfile_output = '{path}/{tarfile}'.format(path=os.path.abspath(output_path), tarfile=tar_filename)

# 	print "processing tar_filename=%s" % tar_filename
# 	print "source_dir=%s" % source_dir

# 	make_gz_tar_file(output_filename=tarfile_output, source_dir=source_dir)
# 	elapsed_time = time.time() - start_time
# 	print "DONE, RUNTIME: %s s (%s min)" % (elapsed_time, elapsed_time/60)

#######################################################################################################################

###################################### SUBPROCCESS - PARALLEL ######################################
tar_filenames = []
processes = collections.defaultdict(dict)

for param in param_list:
	start_time = time.time()

	log_dir = './logs_step4_transfer'
	if not os.path.exists(output_path):
		print "UPS: log_dir %s does not exist. Fix it! Exiting..." % log_dir
		sys.exit(1)
	log_file = '{path}/log_{type}_{cutoff}'.format(path=log_dir, type=distance_type, cutoff=param)

	parrent_dir = "/home/projects/tp/childrens/snpsnap/data/step2/1KG_snpsnap_production_v1" + '/' + distance_type + str(param) ## e.g /step2/1KG_snpsnap_production_v1/ld0.5/
	
	tar_filename = 'stat_gene_density_{type}_{cutoff}.{ext}'.format(type=distance_type, cutoff=param, ext='tar.gz')
	tar_filenames.append(tar_filename)

	tarfile_output = '{path}/{tarfile}'.format(path=os.path.abspath(output_path), tarfile=tar_filename)

	print "processing tar_filename=%s" % tar_filename

	# EXAMPLES
	#tar -jcvf archive_name.tar.bz2 folder_to_compress
	#tar -zcvf ld0.5_collection.tab.tar.gz ld0.5_collection.tab
	
	cmd_tar = "tar -zcvf {archive_name} {folder_to_compress}".format(archive_name=tarfile_output, folder_to_compress='stat_gene_density')
	print "making command: %s" % cmd_tar
	f = open(log_file, mode='a', buffering=1) # buffering: 0 means unbuffered, 1 means line buffered, 
	processes[str(param)]['fh'] = f
	### NOTICE THAT I CHANGE THE CURRENT DIR OF THE SUBPROCCESS:  e.g /step2/1KG_snpsnap_production_v1/ld0.5/
	f.write( '####################################### %s #######################################\n' % batch_time )
	p=subprocess.Popen(cmd_tar, stdout=f, stderr=subprocess.STDOUT, shell=True, cwd=os.path.abspath(parrent_dir)) #bufsize=0 is default
	processes[str(param)]['p'] = p
	processes[str(param)]['pid'] = p.pid


print "I have just submitted the following processes..."
for param in processes.keys():
	#print processes[param]['fh']
	print processes[param]['pid']

print "Now waiting for processes..."
for param in processes.keys():
	p = processes[param]['p']
	print "waiting for pid=%s [param=%s]" % (p.pid, param)
	p.wait()
	elapsed_time = time.time() - start_time
	print "DONE in %s s (%s min)" % (elapsed_time, elapsed_time/60)

elapsed_time = time.time() - start_time_script
print "%s | TOTAL RUNTIME TAR SUBPROCCESSES: %s s (%s min)" % (current_script_name, elapsed_time, elapsed_time/60)

#######################################################################################################################


###################################### NOW DO MD5SUM ######################################
#TODO: this could also be implemented using Python
#TODO: open a file handle and let the subproccess write to that file instead

## Important: the tar_filename should only contain the base name of the file in order for UNIX md5sum to work both on Broad and CBS

#file_md5sum = '{path}/{filename}.{ext}'.format(path=os.path.abspath(output_path), filename='md5sum', ext='md5')
#cmd_md5sum = 'md5sum {files} > {out}'.format( files=" ".join(tar_filenames), out=file_md5sum)

file_md5sum = '{type}_{filename}.{ext}'.format(type=distance_type, filename='md5sum', ext='md5')
cmd_md5sum = 'md5sum {files} > {out}'.format( files=" ".join(tar_filenames), out=file_md5sum)
print "now making subprocess call: %s" % cmd_md5sum
### NOTICE THAT I CHANGE THE CURRENT DIR OF THE SUBPROCCESS
p = subprocess.Popen(cmd_md5sum, shell=True, cwd=os.path.abspath(output_path))
p.wait()

elapsed_time = time.time() - start_time_script
print "%s | TOTAL RUNTIME: %s s (%s min)" % (current_script_name, elapsed_time, elapsed_time/60)


 #tar -xvzf file.tar.gz
 #tar -xvzf comp_stat_gene_density_kb_100.tar.gz
 #tar -xvzf stat_gene_density_kb_100.tar.gz
#for param in param_list:
#	cmd_scp = "time scp -r /home/projects/tp/childrens/snpsnap/data/transfer/stat_gene_density_{distance_type}_{param}.tar.gz ptimshel@copper.broadinstitute.org:/cvar/jhlab/snpsnap/data/transfer/ &".format(distance_type=distance_type, param=param)
#	print cmd_scp

