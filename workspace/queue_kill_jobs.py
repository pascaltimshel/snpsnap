#!/usr/bin/env python2.7

# Possibly use
# coding: utf-8

import os
import subprocess
import argparse
import sys
import re

def check_jobs():
	pass
	# show current running time

def calc_time_of_jobs():
	pass

def kill_jobs(infile):
	pattern = re.compile('^[0-9]$')
	try:
	    with open(infile, 'r') as f:
	    	jobs2kill = []
	    	lines = f.readlines()
	    	for line in lines:
	    		jobID = line.strip()
	    		if not pattern.match(jobID):
	    			print 'ERROR: %s is not valid job ID. Exiting gracefully' % str(jobID)
	    			sys.exit(1)  # any nonzero value is considered "abnormal termination" by shells 
    			else:
    				jobs2kill.append(jobID)
	except IOError as e: # you do not need "e" if you re-raise the error
	    print "IOError: Possibly the file does not exist, exiting gracefully"
	    raise # reraise the current exception 
	    # or use sys.exit(1)?


#Parse Arguments
arg_parser = argparse.ArgumentParser(description="Kill all job IDs listed in a file")
arg_parser.add_argument("--file", help="file with list of job IDs", required=True)
args = arg_parser.parse_args()

kill_jobs(args.file)


###################################### MIX NOTES ######################################



# def kill_jobs(infile):
# 	pattern = re.compile('^[0-9]$')
# 	try:
# 	    with open(infile, 'r') as f:
# 	    	lines = f.readlines()
# 	    	for line in lines:
# 	    		jobID = line.strip()
# 	    		if not pattern.match(jobID):
# 	    			try:
# 	    				raise('not valid job ID')
# 	    			except Exception as e: # catching all exceptions
# 	    				print '%s. Exiting gracefully'
# 	    				sys.exit(1) # any nonzero value is considered "abnormal termination" by shells 
# 	except IOError as e:
# 	    print "IOError: Possibly the file does not exist, exiting gracefully"
# 	    raise # or sys-exit?









# try:
#     f = open('foo.txt')
# except IOError:
#     print('error')
# else:
#     with f:
#         print f.readlines()

# try:
#     fsock = open("/notthere")
# except IOError:
#     print "The file does not exist, exiting gracefully"
#     raise
# print "This line will always print"


