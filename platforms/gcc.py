from platforms.platform import *
import sys
import subprocess
import time

class ParamCCOptimization(Parameter):
    valid_values = ['O0', 'O1', 'O2', 'O3']

class PlatformGCC(Platform):
    def __init__(self):
        self.parameters = [
                ParamCores(max=1),
                ParamCCOptimization()
        ]
        super().__init__()

    def check_if_valid(self):
        if get_hostname() == 'tile.hpcl.gwu.edu':
            return False

        return True

    def submit_job(self, benchmark, job, instance):
        job.nb_cores = 1

        job.cmd = self.get_run_cmd(benchmark)

        max_time = instance.get_result_max('total_time')
        job.set_max_time(max_time)

    def get_compile_cmd(self, benchmark):
        ht = self.get_ht(benchmark)

        ht['ucc'] = "gcc"
        ht['upcc_nb_threads_opt'] = ''
        ht['platform'] = 'berkeley'

        opt = ht["ParamCCOptimization"]

        ht["upcc"] = "\\\"gcc -lm -m64 -march=native -%(opt)s \\\"" % locals()

        return benchmark.get_compile_cmd(ht)

    def get_run_cmd(self, benchmark):
        ht = self.get_ht(benchmark)
        cmd_run = """time ./%(exe_basename)s"""
        return benchmark.get_run_cmd(ht, cmd_run)

    def precheck_result(self, bench, path):
        with open(path + '0004_run.log', 'r') as f:
            data = f.read()

    def check_result(self, bench, folder, result):
        ht = {}
        path = folder + result + '/'

        data = self.get_result_data(folder, result, '0004_run.log')

        ht['stderr'] = ''
        ht['stdout'] = data

        try:
            result_ht = bench.check_result( self, folder, result, ht )
        except Exception as e:
            if ht['stderr'].find('Assertion') != -1:
                print('svn delete --force ' + path)
            raise e

        return result_ht
