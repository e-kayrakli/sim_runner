from benchmarks.benchmarks import Benchmark

from parameters import *
from user_parameters import *

import os

class ParamVectorSize(Parameter):
    name = "VectorSize"
    valid_values = [4096, 16384, 65536, 262144]

class ParamVectorOpt(Parameter):
    name = "ManualOpt"
    valid_values = ['MO_SOFT1', 'MO_SOFT2', 'MO_SOFT3', 'MO_HW1', 'MO_HW2']

class BenchmarkVectorAddition(Benchmark):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/hardware/simulator/test_alpha/vector_addition/'
    needed_files = []

    def __init__(self):
        self.parameters = [
                ParamVectorSize(),
                ParamVectorOpt()
                ]
        super().__init__()

    def get_compile_cmd(self, ht):
        cmd = "make -j 4 VECTOR_SIZE=%(ParamVectorSize)d THREADS=%(ParamCores)d UPC_STATIC=%(ParamStatic)d MANUAL_OPT=%(ParamVectorOpt)s " % ht
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
        return 'vector_addition' % ht

    def get_exe_name(self, ht):
        return self.get_path() + self.get_short_exe_name(ht)

    def get_complete_exe_name(self, ht):
        return 'vector_addition_%(ParamVectorSize)d__%(ParamCores)d_%(ParamBerkeleyThreadsStatic)s_%(ParamVectorOpt)s' % ht

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
        crc = self.get_result(lines, 'Vector result CRC = ', 16)

        if not time:
            raise Exception('Invalid time')

        result_ht['cycles'] = time
        result_ht['crc'] = crc

        return result_ht

