#!/usr/bin/env python2.7


import sys
import glob
import os
import datetime
import time
import subprocess 


#import memory_profiler
from memory_profiler import profile

### Usage:
#1) ./test_memory_profile_example.py [or python test_memory_profile_example.py]
	# Use this import statement 'from memory_profiler import profile'
	# NB using 'import memory_profile' and thus having '@memory_profiler.profile' will not be compatible with running #2) usage
	# NB using 'import memory_profile' I am unsure if 'mprof run <script>' will work
#2) python -m memory_profiler test_memory_profile_example.py
	# Using this call you do not need the import statement
	# Memory profiling will be written to STDOUT
	# Note that you will get a warning stateing that memory_profile will be slow because 'psutil' is not imported.
		# however the 'psutil' module does not exist on Broad!


#3) mprof run test_memory_profile_example.py
	# THIS DOES NOT WORK ON BROAD
		# --> -bash: mprof: command not found
	# this would write a file to be plotted


@profile
def my_func():
    a = [1] * (10 ** 6)
    b = [2] * (2 * 10 ** 7)
    del b
    return a

if __name__ == '__main__':
    my_func()



