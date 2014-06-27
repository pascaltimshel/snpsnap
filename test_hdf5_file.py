#!/usr/bin/env python2.7


import sys
import glob
import os
import datetime
import time
import subprocess 

import pandas as pd

from memory_profiler import profile

hdf5_file = "/cvar/jhlab/snpsnap/data/step3/1KG_snpsnap_production_v1/test_tabs_compile_ld0.5/ld0.5_db.h5"

csv_file = "/cvar/jhlab/snpsnap/snpsnap/tmptmp_store_test.csv"

@profile
def my_func():
	store = pd.HDFStore(hdf5_file, 'r')
	df = store.get('dummy')
	df.to_csv(csv_file, sep='\t', header=True, index=True, index_label='snpID')

	print df.index

if __name__ == '__main__':
    my_func()



