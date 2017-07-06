from benchmarks.benchmarks import *
from parameters import *
from user_parameters import *

import os

class ParamUPCOptimization( Parameter ):
    name = "UPCOptimization"
    valid_values = [1, 2]

class ParamMatrixSize( Parameter ):
    name = "MatrixSize"
    valid_values = [512, 1024, 2048]

class BenchmarkRandomAccess( Benchmark ):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/tilera64/tests/random_access/'
    needed_files = []

    def __init__(self):
        self.parameters = [ParamMatrixSize(), ParamUPCOptimization()]
        super().__init__()

    def check_vector_validity(self, *args, **kwargs):
        return True

    def get_compile_cmd(self, ht):
        cmd = "make ARRAY_SIZE=%(ParamMatrixSize)d UPCC=%(upcc)s THREADS=%(ParamCores)d UPC_OPT=%(ParamUPCOptimization)d " % ht
        return cmd

    def get_run_cmd(self, ht, cmd_run):
        ht['exe_name'] = self.get_exe_name(ht)
        ht['exe_basename'] = os.path.basename( self.get_exe_name(ht) )
        return cmd_run % ht

    def get_path(self):
        return self.benchmark_path

    def get_exe_name(self, ht):
        return self.get_path() + 'random_access' % ht

    def get_result(self, lines, name):
        for line in lines:
            pos = line.find(name)
            if pos != -1:
               info = line[pos + len(name):]
               return float(info)
        return None

    def check_result(self, platform, folder, result, ht):
        lines = ht['stdout'].split('\n')
        time = self.get_result(lines, 'Execution Time:')
        if not time:
            print("rm -rf ", folder + result)

        result_ht = {}
        result_ht['total_time'] = time
        return result_ht

