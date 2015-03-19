#!/bin/env python

# Import modules for CGI handling 
import cgi, cgitb
import json

import time
import datetime

import sys
import os


# Create instance of FieldStorage 
form = cgi.FieldStorage() 

snpsnap_version = "dummy"
super_population = form.getvalue('super_population', '')
distance_type = form.getvalue('distance_type', '')
distance_cutoff = form.getvalue('distance_cutoff', '')

path_web_logs = '/local/data/web_logs'
file_download_stats = "{base}/stats_downloads.{ext}".format(base=path_web_logs, ext='csv')


file_download = "/cvar/jhlab/snpsnap/data/step3/1KG_snpsnap_production_v2/{super_population}/{distance_type}{distance_cutoff}/{distance_type}{distance_cutoff}_collection.{ext}".format(super_population=super_population, distance_type=distance_type, distance_cutoff=distance_cutoff, ext="tab")
#e.g /cvar/jhlab/snpsnap/data/step3/1KG_snpsnap_production_v2/EUR/ld0.5/ld0.5_collection.tab


batch_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S')

### Default return values
collection_download_info_dict = {
	"super_population":"NA",
	"distance_type":"NA",
	"distance_cutoff":"NA",
	"file_size":"NA"
}

try:
	### Get file size
	file_size_mb = os.path.getsize(file_download)/(1024*1024.0)
	file_size_gb = os.path.getsize(file_download)/(1024*1024.0*1024.0)

	file_size_mb_fmt = "{size:.1f} MB".format(size=file_size_mb)
	file_size_gb_fmt = "{size:.1f} GB".format(size=file_size_gb)


	collection_download_info_dict = {
		"super_population":super_population,
		"distance_type":distance_type,
		"distance_cutoff":distance_cutoff,
		"file_size":file_size_gb_fmt
	}


	### Write to "stats file" - *IN APPED MODE*
	with open(file_download_stats, 'a') as f:
		f.write( "{},{},{},{},{},{}\n".format(batch_time, super_population, distance_type, distance_cutoff, file_size_gb_fmt, file_download) )


	### DUMPING dict of dict as json string
	json2parse = json.dumps(collection_download_info_dict)

	### RETURNING json string to ajax calls
	print "Content-Type: application/json" # for raw text use: "Content-Type: text/plain"
	print ""
	print json2parse


except Exception as e: # e.g IOError
	print "Content-Type: application/json"
	print ""
	
	collection_download_info_dict.update({"exception":str(e)}) # OBS: updating the dict with the expection!

	json2parse = json.dumps(collection_download_info_dict)
	print json2parse



