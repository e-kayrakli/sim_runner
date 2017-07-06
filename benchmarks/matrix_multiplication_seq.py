from benchmarks.benchmarks import *

from parameters import *
from benchmarks.matrix_multiplication import ParamMatrixSize
from user_parameters import *

import os

class BenchmarkMatrixMultiplicationSeq( Benchmark ):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/tilera64/tests/matrix_mult_2_seq/'
    needed_files = []

    def __init__(self):
        self.parameters = [ParamMatrixSize()]
        super().__init__()

    def get_compile_cmd(self, ht):
        cmd = "make MATRIX_SIZE=%(ParamMatrixSize)d CC=%(upcc)s " % ht
        return cmd

    def get_run_cmd(self, ht, cmd_run):
        ht['exe_name'] = self.get_exe_name(ht)
        ht['exe_basename'] = os.path.basename( self.get_exe_name(ht) )
        return cmd_run % ht

    def get_path(self):
        return self.benchmark_path

    def get_exe_name(self, ht):
        return self.get_path() + 'matrix_mult' % ht

    def get_result(self, lines, name):
        for line in lines:
            pos = line.find(name)
            if pos != -1:
               info = line[pos + len(name):]
               return float(info)
        return None

    def check_result(self, platform, folder, result, ht):
        lines = ht['stdout'].split('\n')
        time = self.get_result(lines, ' time=')

        result_ht = {}
        result_ht['total_time'] = time
        return result_ht

