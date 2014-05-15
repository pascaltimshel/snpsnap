#!/usr/bin/env python2.7


import os

import time
import datetime


class HelperUtils(object):
	@staticmethod
	def mkdirs(file_path):
		if not os.path.exists(file_path):
			os.makedirs(file_path)

	@staticmethod
	def check_if_writable(file_path):
		if not os.access(file_path, os.W_OK):
			msg="File path: %s is not writable" % file_path
			raise Exception(msg)
		else:
			return os.path.abspath(file_path)
	
	@staticmethod
	def gen_timestamp():
		return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S') # date/time string e.g. 2012-12-15_01:21:05,
