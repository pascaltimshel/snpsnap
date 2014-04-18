#!/usr/bin/env python2.7

import os
import subprocess

## Pascal added
import argparse
import re
from datetime import *

# More Pascal add
import time # use for sleep and more

# print __package__   #None
# print __file__  #/net/home/home/projects9/tp/childrens/snpsnap/git/queue.py
# print __module__    #queue
# print __name__  #queue

class QueueJob:
    QJ_job_counter = 0
    QJ_job_fails = 0
    QJ_time_stamp = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H.%M.%S') # date/time string e.g. 2012-12-15_01:21:05, # or do ShellUtils.gen_timestamp()
    #QJ_err_log_name = 'QueueJob_error_log_' + QJ_time_stamp + '.txt'
    #QJ_jobs_log_name = 'QueueJob_jobs_log_' + QJ_time_stamp + '.txt'
    def __init__(self, cmd, logdir, queue, walltime, mem, flags, logname, script_name='unknown_name'):
        QueueJob.QJ_job_counter += 1 # Counter the number of jobs
        self.job_number = QueueJob.QJ_job_counter
        self.id = -1
        self.is_running = False
        self.status = ""
        self.qcmd = "xmsub -de -o %s/%s.out -e %s/%s.err -r y -q %s -l mem=%s,walltime=%s,flags=%s"%(logdir, logname, logdir, logname,queue, mem, walltime,flags) 
        self.logdir = logdir
        self.cmd = cmd
        self.call = self.qcmd + " " + self.cmd
        self.attempts = 0

        self.err_log = 'QueueJob_' + script_name + '_error_log_' + QueueJob.QJ_time_stamp + '.txt'
        self.jobs_log = 'QueueJob_' + script_name + '_jobs_log_' + QueueJob.QJ_time_stamp + '.txt'

    def run(self):
        max_calls = 15
        sleep_time = 20 # pause time before making a new call.
        #TODO make sleep_time increse for each attempt.
        emsg = "" # placeholder for error massage from CalledProcessError exception
        print "#################### JOB NUMBER %d ####################" % self.job_number
        while self.attempts < max_calls:
            self.attempts += 1
            try:
                print "ATTEMPT #%d/%d Jobsubmission call\n%s" % (self.attempts, max_calls, self.call)
                out = subprocess.check_output(self.call, shell=True)
            except subprocess.CalledProcessError as e:
                print "ATTEMPT #%d/%d *** Error submitting job ***" % (self.attempts, max_calls)
                print "ATTEMPT #%d/%d *** Error massage ***\n%s" % (self.attempts, max_calls, e)
                print "ATTEMPT #%d/%d *** Sleeping for %d seconds before re-submitting job ***" % (self.attempts, max_calls, sleep_time)
                emsg = e
                time.sleep(sleep_time)
                #self.attempts += 1
            else:
                self.id = out.strip()
                print "ATTEMPT #%d/%d JOB SUCCESFULLY SUBMITTED!" % (self.attempts, max_calls)
                print "ATTEMPT #%d/%d JOBID IS %s" % (self.attempts, max_calls, self.id)
                jobs_log_path = "%s/%s" % (self.logdir, self.jobs_log)
                with open(jobs_log_path, 'a') as QJ_jobs_log:
                    QJ_jobs_log.write( '%s\n' % self.id )
                # return if no exceptions are cought
                return
        # These lines are only executed if attempts <= max_calls
        QueueJob.QJ_job_fails += 1
        err_log_path = "%s/%s" % (self.logdir, self.err_log)
        print "ATTEMPT #%d/%d *** Maximum number of attempts reached ****" % (self.attempts, max_calls)
        print "ATTEMPT #%d/%d *** Reporting this in logfile ***\n%s" % (self.attempts, max_calls, err_log_path) # CHECK
        with open(err_log_path, 'a') as QJ_err_log:
            QJ_err_log.write( 'JOB FAIL #%d   Last error message is\n' % QueueJob.QJ_job_fails )
            QJ_err_log.write( '%s \n\n' % emsg )

            
    # def run(self):
    #     max_calls = 15
    #     sleep_time = 20 # pause time before making a new call.
    #     try:
    #         print "ATTEMPT #%d/%d Jobsubmission call: %s" % (self.attempts, max_calls, self.call)
    #         out = subprocess.check_output(self.call, shell=True)
    #     except subprocess.CalledProcessError as e:
    #         print "ATTEMPT #%d/%d Error submitting job: %s" % (self.attempts, max_calls, self.call)

    #         if self.attempts <= max_calls:
    #             print "ATTEMPT #%d/%d Sleeping for %d seconds before re-submitting job" % (self.attempts, max_calls, sleep_time)
    #             time.sleep(sleep_time)
    #             self.attempts += 1
    #             self.run()
    #         else:
    #             print "ATTEMPT #%d/%d Maximum number of attempts reached"
    #     else:
    #         self.id = out.strip()
    #         print self.id

        
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


