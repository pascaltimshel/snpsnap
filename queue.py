#!/usr/bin/env python2.7

import os
import subprocess

## Pascal added
import argparse
import re
from datetime import *


class QueueJob:

    def __init__(self, cmd, logdir, queue, walltime, mem, flags, logname):
        self.id = -1
        self.is_running = False
        self.status = ""
        self.qcmd = "xmsub -de -o %s/%s.out -e %s/%s.err -r y -q %s -l mem=%s,walltime=%s,flags=%s"%(logdir, logname, logdir, logname,queue, mem, walltime,flags) 
        self.cmd = cmd
        
    def run(self):
        print self.qcmd + " " + self.cmd
        out = subprocess.check_output(self.qcmd + " " + self.cmd,shell=True)
        self.id = out.strip()
        print self.id

        
    def check_status(self):
        out = subprocess.check_output("checkjob %s" % self.id, shell=True)
        pattern = re.compile("^State:\W(\w*)",flags=re.MULTILINE)
        match = pattern.search(out)
        if match: 
            self.status = match.group(1)
            if self.status == "Running":
                self.is_running = True
            elif self.status == "Completed":
                self.is_running = False
        else:
            print out

class ArgparseAdditionalUtils:
    @classmethod
    def verify_file_path_exists_return_abs(cls, file_path):
        if not os.path.exists(file_path):
            msg="File path: %s is invalid"%file_path
            raise argparse.ArgumentTypeError(msg)
        else:
            return os.path.abspath(file_path)
        
    @classmethod
    def check_if_writable(cls, file_path):
        if not os.access(file_path, os.W_OK):
            msg="File path: %s is not writable"%file_path
            raise argparse.ArgumentTypeError(msg)
        else:
            return os.path.abspath(file_path)
        
class ShellUtils:
    @classmethod
    def mkdirs(cls, file_path):
        if not os.path.exists(file_path):
            os.makedirs(file_path)

    @classmethod
    def gen_timestamp(cls):
        return datetime.now().strftime("%d_%m_%y_%H_%M_%S")


