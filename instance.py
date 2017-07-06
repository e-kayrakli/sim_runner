import copy

from user_parameters import *
from util import *
from task import *
from terminalcontroller import *
from jobschedulers.jobscheduler_all import *
from jobschedulers.job import Job

import os
import math_tools
import traceback

job_scheduler = get_current_scheduler()

def instances_load_results(instances):
    count = 0
    uniq = 0
    for i in instances:
        i.load_results()

        count = count + len(i.results)
        if(len(i.results) > 0):
            uniq = uniq + 1

def instances_check_results(instances):
    term = TerminalController()
    pb = ProgressBar(term, 'Checking results')
    size = len(instances)
    pos = 0.0

    errors = 0
    running = 0
    waiting = 0
    total = 0

    for i in instances:
        pos = pos + 1
        (e, r, w, t) = i.check_results(verbose=pb.simple)
        errors += e
        running += r
        waiting += w
        total += t
        pb.update(pos / size, str(i))

    count = 0
    uniq = 0
    for i in instances:
        if i.results_ht:
            count = count + len(i.results_ht)
            if(len(i.results_ht) > 0):
                uniq = uniq + 1

    print(count, "valid results available.", uniq, 'uniq valid results.',
            int(uniq * 100 / len(instances)), '%')
    if total == 0:
        print("No results")
        return
    print('Errors:', errors, '(', int(errors * 100 / total), '% )    Running:',
            running, '(', int(running * 100 / total), '% )   Waiting:',
            waiting, '(', int(waiting*100/total), '%)   Total:', total)
    print("")

class Instance(object):
    def __init__(self, benchmark, platform, result_dir=None):
        self.benchmark = copy.deepcopy(benchmark)
        self.platform = copy.deepcopy(platform)
        self.results = []
        self.results_ht = []
        self.my_str = None
        if result_dir != None:
            self.result_folder = result_dir
        else:
            self.result_folder = default_result_folder

    def __str__(self):
        if not self.my_str:
            self.my_str = "instance("+ self.platform.get_name() + str(self.platform.vector) + ", " + \
                self.benchmark.get_name() + str(self.benchmark.vector) + ")"
        return self.my_str

    def has_results(self):
        return len(self.results_ht) != 0

    def submit_job(self, path):
        job = Job()
        job.name = self.benchmark.format_vector() + '_' + \
               self.platform.format_vector()
        job.path = path
        self.platform.submit_job(self.benchmark, job, self)
        job_scheduler.submit_job(job)

    def get_run_cmd(self):
        return self.platform.get_run_cmd(self.benchmark)

    def short_str(self):
        return self.platform.get_name() + str(self.platform.vector) + "_" + \
                self.benchmark.get_name() + str(self.benchmark.vector)

    def pretty_print(self):
        return 'instance(\n    ' + self.platform.get_name() + '=' + str(self.platform.get_representation()) +'\n    ' + \
                self.benchmark.get_name() + '=' + str(self.benchmark.get_representation()) + ' )'

    def get_folder_name(self):
        return self.result_folder + \
                self.get_folder_base_name()

    def get_folder_base_name(self):
        return  \
                self.platform.get_name() + '/' + \
                self.platform.format_vector() + '/' + \
                self.benchmark.get_name() + '/' + \
                self.benchmark.format_vector() + '/'

    def get_canonical_name(self):
        return  self.benchmark.get_name() + '_' + \
                self.benchmark.format_vector() + '_' + \
                self.platform.get_name() + '_' + \
                self.platform.format_vector()

    def load_results(self):
        folder = self.get_folder_name()
        result_list = get_dir_list(folder)
        self.results = result_list

    def create_new_task(self, is_compilation=False):
        return Task(self, is_compilation)

    def get_compile_cmd(self):
        return self.platform.get_compile_cmd(self.benchmark)

    def get_path(self):
        return self.benchmark.get_path()

    def get_complete_exe_name(self):
        return self.platform.get_complete_exe_name(self.benchmark)

    def get_exe_name(self):
        return self.platform.get_exe_name(self.benchmark)

    def check_results(self, verbose=True):
        folder = self.get_folder_name()
        errors = 0
        running = 0
        waiting = 0
        total = len(self.results)

        self.still_running = False

        for result in self.results:
            try:
                result_ht = self.platform.check_result(self.benchmark, folder, result)
                result_ht['result'] = result
                self.results_ht.append(result_ht)
            except Exception as e:
                if str(e).find('Still running') != -1:
                    running += 1
                    self.still_running = True
                    if verbose:
                        print(e)
                    #print("rm -rf", folder + result)
                    continue
                if str(e).find('Waiting in scheduler queue') != -1:
                    waiting += 1
                    continue
                errors += 1
                if verbose:
                    print("Error: ", str(self), e.__class__.__name__, e)
                    print("  rm -rf", folder + result)
                    traceback.print_exc(file=sys.stdout)

                #run_cmd("rm -rf " + folder + result)
        return (errors, running, waiting, total)

    def fix_issues(self, verbose=True):
        folder = self.get_folder_name()
        total = len(self.results)

        for result in self.results:
            self.platform.fix_issues(self.benchmark, folder, result)

    def get_result_list(self, key):
        return [v for v in [v.get(key, None) for v in self.results_ht] if v!=None]

    def get_first(self, key):
        return self.results_ht[0].get(key, None)

        if v != None:
            return v

        for d in self.results_ht:
            v = d.get(key, None)
            if v != None:
                return v
        return None

    def get_min(self, key):
        lst = self.get_result_list(key)
        return math_tools.list_min(lst)

    def get_result_max(self, key):
        lst = self.get_result_list(key)
        return math_tools.list_max(lst)

    def get_median(self, key):
        lst = self.get_result_list(key)
        return math_tools.list_median(lst)

    def get_stddev(self, key):
        lst = self.get_result_list(key)
        return math_tools.list_stddev(lst)

def get_instance_list(benchmark, platform, check_platform=True, result_dir=None):
    tasks = []
    if check_platform:
        if not platform.check_if_valid():
            print('Not valid plat')
            return []

    vp = platform.vector
    while vp != None:
        v = benchmark.vector
        while v:
            if benchmark.check_validity(platform):
                tasks.append(Instance(benchmark, platform, result_dir))
            v = benchmark.vector_next_valid(platform)
        vp = platform.vector_next_valid()

    return tasks

