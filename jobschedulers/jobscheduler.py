import sys
import time
import tarfile

from jobschedulers.job import Job

class JobScheduler(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(JobScheduler, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.running_jobs_cache = None
        self.waiting_jobs_cache = None
        self.term_yellow = ''
        self.term_red = ''
        self.term_normal = ''
        self.jobs_to_submit = []
        self.max_cores = 8

    def submit_job(self, job):
        if job.allow_grouping == False or job.nb_cores >= self.max_cores:
            self.immediate_job_submit(job)
            return
        self.jobs_to_submit.append(job)
        self.check_for_job_to_submit()

    def flush_all(self):
        while self.jobs_to_submit:
            self.check_for_job_to_submit(force=True)

    def check_for_job_to_submit(self, force=False):
        total_nb_cores = sum([j.nb_cores for j in self.jobs_to_submit])

        if (total_nb_cores < self.max_cores) and not force:
            return

        to_submit = []
        nb_cores_to_submit = 0

        for j in range(len(self.jobs_to_submit)):
            job = self.jobs_to_submit[j]
            if job.nb_cores + nb_cores_to_submit <= self.max_cores:
                nb_cores_to_submit += job.nb_cores
                to_submit.append(job)

        for job in to_submit:
            self.jobs_to_submit.remove(job)
        self.submit_job_list(to_submit)

    def submit_job_list(self, job_list):
        if not job_list:
            return

        job = Job()

        job.nb_cores = sum([j.nb_cores for j in job_list])
        job.max_time = int(max([j.max_time for j in job_list]) * 1.5)
        job.name = '__'.join([j.name for j in job_list])

        cmd = ''
        for j in job_list:
            cmd += 'echo ' + j.name + '\n'
            cmd += 'cd ' + j.path + '\n'
            cmd += '(\n'
            cmd += '    ' + j.cmd + '\n'
            cmd += ') 2> result.err > result.out &\n'
            cmd += '\n'
        cmd += '\n'
        cmd += 'wait\n'
        cmd += 'echo All job finished\n'

        job.cmd = cmd
        job.allow_grouping = False
        job.path = job_list[0].path
        job.output = 'jobgroup'

        self.immediate_job_submit(job)

    def immediate_job_submit(self, job):
        raise NotImplementedError()

    def get_running_job_ids(self, use_cache=True):
        if use_cache:
            if self.running_jobs_cache != None:
                return self.running_jobs_cache

        jobs = self.get_current_running_job_ids()
        self.running_jobs_cache = jobs

        return jobs

    def get_current_running_job_ids(self):
        raise NotImplementedError

    def get_waiting_job_ids(self, use_cache=True):
        if use_cache:
            if self.waiting_jobs_cache != None:
                return self.waiting_jobs_cache

        jobs = self.get_current_waiting_job_ids()
        self.waiting_jobs_cache = jobs

        return jobs

    def get_current_waiting_job_ids(self):
        raise NotImplementedError

    def wait_nb_task(self, nb=0):
        first = True
        waiting_job_set = self.get_waiting_job_ids(False)
        while waiting_job_set == None or len(waiting_job_set) > nb:
            if first:
                first = False
                print(self.term_yellow + 'Waiting for task to finish' +
                        self.term_normal, end='')
            if waiting_job_set == None:
                print(self.term_red + '.' + self.term_normal, end='')
            else:
                print('.', end='')
            sys.stdout.flush()
            time.sleep(10)
            waiting_job_set = self.get_waiting_job_ids(False)
        if not first:
            print()

    def get_run_cmd(self):
        raise NotImplementedError

    def prepare_run(self, cmd, nb_cores, name, max_time=None):
        raise NotImplementedError

    def get_result_data(self, folder, result, file):
        if result.endswith('.tar'):
            tar = tarfile.open(folder + result)
            f = tar.extractfile(result[:-4] + '/' + file)
        else:
            path = folder + result + '/'
            f = open(path + file, 'rb')

        data = f.read(16*1024*1024)
        data = str(data, encoding='ascii')
        f.close()
        if result.endswith('.tar'):
            tar.close()

        return data

    def read_stdout(self, folder, result):
        path = folder + result + '/'
        data = self.get_result_data(folder, result, '0004_run.log')
        job_id = self.get_job_id_from_submit(data)
        job_stdout_filename = self.get_job_stdout_filename(data)

        running = self.get_running_job_ids()
        if job_id in running:
            raise Exception('Still running ' + path)

        waiting_jobs = self.get_waiting_job_ids()
        if job_id in waiting_jobs:
            raise Exception('Waiting in scheduler queue ' + path)

        return self.get_result_data(folder, result, job_stdout_filename)

    @staticmethod
    def get_job_id_from_submit(data):
        raise NotImplementedError

    @staticmethod
    def get_job_stdout_filename(data):
        raise NotImplementedError
