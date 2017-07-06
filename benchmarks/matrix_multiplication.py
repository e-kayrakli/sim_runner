from benchmarks.benchmarks import Benchmark

from parameters import *
from user_parameters import *

import os

class ParamMatrixSize(Parameter):
    name = "MatrixSize"
    valid_values = [64, 128, 256]

class ParamMatrixOpt(Parameter):
    name = "ManualOpt"
    valid_values = ['MO_SOFT1', 'MO_SOFT2', 'MO_SOFT3', 'MO_SOFT4', 'MO_SOFT5', 'MO_HW1', 'MO_HW2']

class BenchmarkMatrixMultiplication(Benchmark):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/hardware/simulator/test_alpha/matrix_multiplication/'
    needed_files = []

    def __init__(self):
        self.parameters = [
                ParamMatrixSize(),
                ParamMatrixOpt()
                ]
        super().__init__()

    def get_compile_cmd(self, ht):
        cmd = "make -j 4 MATRIX_SIZE=%(ParamMatrixSize)d THREADS=%(ParamCores)d UPC_STATIC=%(ParamStatic)d MANUAL_OPT=%(ParamMatrixOpt)s " % ht
        return cmd

    def check_validity(self, platform):
        if platform.get_param_value('ParamBerkeleyThreadsStatic') != 'Static':
            return False

        return True

    def get_run_cmd(self, ht, cmd_run):
        ht['exe_name'] = self.get_exe_name(ht)
        ht['exe_basename'] = os.path.basename(self.get_exe_name(ht))
        return cmd_run % ht

    def get_path(self):
        return self.benchmark_path

    def get_short_exe_name(self, ht):
        return 'matrix_multiplication' % ht

    def get_exe_name(self, ht):
        return self.get_path() + self.get_short_exe_name(ht)

    def get_complete_exe_name(self, ht):
        return 'matrix_multiplication_%(ParamMatrixSize)d__%(ParamCores)d_%(ParamBerkeleyThreadsStatic)s_%(ParamMatrixOpt)s' % ht

    def get_result(self, lines, name, base=10):
        for line in lines:
            pos = line.find(name)
            if pos != -1:
               info = line[pos + len(name):]
               return int(info, base)
        return None

    def check_result(self, platform, folder, result, ht):
        result_ht = {}

        lines = ht['stdout'].split('\n')
        time = self.get_result(lines, 'cycles: ')

        if not time:
            raise Exception('Invalid time')

        result_ht['cycles'] = time

        return result_ht

