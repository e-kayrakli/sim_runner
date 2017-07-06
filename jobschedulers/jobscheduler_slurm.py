import subprocess
import util
from jobschedulers.jobscheduler import JobScheduler
from jobschedulers.slurm_time import SlurmTime
from jobschedulers.job import Job

class JobSchedulerSlurm(JobScheduler):
    @staticmethod
    def is_available():
        try:
            return subprocess.call('sinfo > /dev/null 2>/dev/null', shell=True) == 0
        except:
            return False

    def get_current_running_job_ids(self):
        squeue_out = subprocess.getoutput('squeue --noheader --format=%i --user=$USER --states=R')
        jobs = {int(line.strip(' ')) for line in squeue_out.split('\n') if line}
        return jobs

    def get_current_waiting_job_ids(self):
        squeue_out = subprocess.getoutput('squeue --noheader --format=%i --user=$USER --states=PD')
        jobs = {int(line.strip(' ')) for line in squeue_out.split('\n') if line}
        return jobs

    def immediate_job_submit(self, job):
        if util.get_hostname() == 'cray':
            if job.max_time > 4 * 24 * 3600:
                job.max_time = 4 * 24 * 3600
        elif util.get_hostname() == 'login':
            if job.max_time > 1 * 24 * 3600:
                job.max_time = 20 * 24 * 3600
        st = SlurmTime(job.max_time)
        st_str = str(st)

        if util.get_hostname() == 'cray':
            partition = 'hpcl'
        elif util.get_hostname() == 'login':
            partition = 'day'
        else:
            partition = 'all'
            #partition = 'lyra'

        job_name = job.name
        job_name = job_name.replace('_0', '_').replace('_0', '_').replace('_0', '_').replace('_0', '_')

        job_nb_cores = job.nb_cores
        job_cmd = job.cmd
        output = job.output
        if not output:
            output = 'result'

        submission_script = """#!/bin/bash

#SBATCH --job-name="%(job_name)s"
#SBATCH --partition=%(partition)s
#SBATCH --ntasks=%(job_nb_cores)d
#SBATCH --time=%(st_str)s

#SBATCH --output=%(output)s.out
#SBATCH --error=%(output)s.err

export GASNET_BACKTRACE=1
export XT_SYMMETRIC_HEAP_SIZE=512M

%(job_cmd)s
""" % locals()

        jsfilename = job.jsfilename

        with open(job.path + jsfilename, 'w') as f:
            f.write(submission_script)

        command = 'sbatch ' + jsfilename
        ret_val = util.run_cmd_and_log(job.path, job.jsout, command)

    def prepare_run(self, cmd, nb_cores, name, max_time=None):
        job = Job(name, cmd, nb_cores, max_time)
        self.immediate_job_submit(job)

    def get_run_cmd(self):
        # TODO fix us jsfilename
        return 'sbatch job.qsub'

    @staticmethod
    def is_good_scheduler(data):
        header = 'Submitted batch job '
        if not data.startswith(header):
            return False
        return True

    @staticmethod
    def get_job_id_from_submit(data):
        header = 'Submitted batch job '
        if not data.startswith(header):
            return None

        job_id = int(data[len(header):])
        return job_id

    @staticmethod
    def get_job_stdout_filename(data):
        return 'result.out'

