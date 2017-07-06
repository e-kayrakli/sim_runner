from param_vector import *
from parameters import *
from jobschedulers.jobscheduler_all import *
from util import *

job_scheduler = get_current_scheduler()

class ParamConduit(Parameter):
    name = "conduit"
    valid_values = ['smp', 'mpi', 'ibv']

    def __init__(self, conduits=[]):
        if conduits:
            self.valid_values = list(conduits)

class Platform(ParamVector):
    def wait_nb_task(self, nb=0):
        job_scheduler.wait_nb_task(nb)

    def get_run_cmd(self, benchmark):
        return job_scheduler.get_run_cmd()

    def check_if_valid(self):
        return False

    def get_ht(self, benchmark):
        ht = benchmark.get_ht()
        ht.update(self.get_ht_based_on_vector())
        return ht

    def get_exe_name(self, benchmark):
        ht = self.get_ht(benchmark)
        return benchmark.get_exe_name(ht)

    def get_complete_exe_name(self, benchmark):
        ht = self.get_ht(benchmark)
        return benchmark.get_complete_exe_name(ht)

    def get_compile_cmd(self, benchmark):
        raise NameError("Not implemented")

    def create_scripts(self, benchmark):
        return

    def precheck_result(self, bench, path):
        return

    def prepare_run(self, benchmark, task=None):
        return
