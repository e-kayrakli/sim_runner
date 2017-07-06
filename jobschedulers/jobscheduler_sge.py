import subprocess
from  jobschedulers.jobscheduler import JobScheduler

class JobSchedulerSGE(JobScheduler):
    @staticmethod
    def is_available():
        try:
            return subprocess.call('qstat > /dev/null 2>/dev/null', shell=True) == 0
        except:
            return False

    def get_current_running_job_ids(self):
        qstat_out = subprocess.getoutput('qstat').split('\n')[2:]
        jobs = {int(line.strip(' ').split(' ')[0]) for line in qstat_out}
        return jobs

    def get_current_waiting_job_ids(self):
        qstat_out = subprocess.getoutput('qstat | grep qw').split('\n')[2:]
        jobs = {int(line.strip(' ').split(' ')[0]) for line in qstat_out}
        return jobs


    def prepare_run(self, cmd, nb_cores, name):
        qsub = """#!/bin/bash
#
#$ -N %(name)s
#$ -cwd
#$ -S /bin/bash
#$ -j y
#$ -pe orte %(nb_cores)d
#$ -q large.q
#$ -l excl

export GASNET_BACKTRACE=1
echo `pwd`

%(cmd)s
""" % locals()

        with open('job.qsub', 'w') as f:
            f.write(qsub)

    def get_run_cmd(self):
        return 'qsub job.qsub'

    @staticmethod
    def is_good_scheduler(data):
        try:
            job_id = int(data.split(' ')[2])
            return True
        except:
            return False

    @staticmethod
    def get_job_id_from_submit(data):
        job_id = int(data.split(' ')[2])
        return job_id

    @staticmethod
    def get_job_stdout_filename(data):
        job_id = self.get_job_id_from_submit(data)
        jobname = data.split('"')[1]
        return jobname + '.o' + str(job_id)

