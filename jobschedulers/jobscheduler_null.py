import subprocess
import util
from jobschedulers.jobscheduler import JobScheduler
from jobschedulers.slurm_time import SlurmTime
from jobschedulers.job import Job

from . import jobscheduler_sge
from . import jobscheduler_slurm

def get_all_schedulers_testable():
    return [jobscheduler_slurm.JobSchedulerSlurm, jobscheduler_sge.JobSchedulerSGE]

class JobSchedulerNULL(JobScheduler):
    @staticmethod
    def is_available():
        return True

    def get_current_running_job_ids(self):
        return {}

    def get_current_waiting_job_ids(self):
        return {}

    def immediate_job_submit(self, job):
        st = SlurmTime(job.max_time)
        st_str = str(st)

        job_name = job.name
        job_nb_cores = job.nb_cores
        job_cmd = job.cmd
        output = job.output
        if not output:
            output = 'result'

        submission_script = """#!/bin/bash

# job-name="%(job_name)s"
# ntasks=%(job_nb_cores)d
# time=%(st_str)s

#SBATCH --output=%(output)s.out
#SBATCH --error=%(output)s.err

export GASNET_BACKTRACE=1

%(job_cmd)s > %(output)s.out 2> %(output)s.err
""" % locals()

        with open(job.path + 'job.sh', 'w') as f:
            f.write(submission_script)

        command = self.get_run_cmd()
        ret_val = util.run_cmd_and_log(job.path, '0004_run', command)

    def prepare_run(self, cmd, nb_cores, name, max_time=None):
        job = Job(name, cmd, nb_cores, max_time)
        self.immediate_job_submit(job)

    def get_run_cmd(self):
        return 'bash ./job.sh'

    @staticmethod
    def is_good_scheduler(data):
        return True

    @staticmethod
    def get_job_id_from_submit(data):
        return None

    @staticmethod
    def get_job_stdout_filename(data):
        return 'result.out'

