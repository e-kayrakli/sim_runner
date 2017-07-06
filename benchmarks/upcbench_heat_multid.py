from benchmarks.benchmarks import Benchmark
from parameters import *
from user_parameters import *

import os

class ParamHeatMultiDSize(Parameter):
    name = "HeatMultiDSize"

    def __init__(self, lst=None):
        if lst != None:
            self.valid_values = lst.copy()
        else:
            self.valid_values = [256, 512, 1024, 2048]

class ParamHeatMultiDOpt(Parameter):
    name = "ManualOpt"
    valid_values = ['MO_SOFT1']

class BenchmarkUBHeatMultiD(Benchmark):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/upc_benchmarks/heat_multid/'
    needed_files = []

    def __init__(self, size_list=[512]):
        if not self.parameters:
            self.parameters = [
                    ParamHeatMultiDSize(size_list),
                    ParamHeatMultiDOpt()
                    ]
        super().__init__()

    def check_validity(self, platform):
        return True

    def get_compile_cmd(self, ht):
        ht['upcc'] = 'upcc_hw.py -Wc,-%(ParamGCCOpt)s -network=smp -T=%(ParamCores)d -pthreads=%(ParamCores)d -shared-heap=128MB %(ExtraBerkeleyOpt)s' % ht
        cmd = "make -j 4 MATRIX_SIZE=%(ParamHeatMultiDSize)d THREADS=%(ParamCores)d MANUAL_OPT=%(ParamHeatMultiDOpt)s " % ht
        return cmd

    def get_run_cmd(self, ht, cmd_run):
        ht['exe_name'] = os.path.basename(self.get_exe_name)
        ht['exe_basename'] = os.path.basename(self.get_exe_name(ht))
        return cmd_run % ht

    def get_path(self):
        return self.benchmark_path

    def get_short_exe_name(self, ht):
        return 'heat_multid.%(ParamCores)d.%(ParamHeatMultiDSize)d.%(ParamHeatMultiDOpt)s' % ht

    def get_exe_name(self, ht):
        return self.get_path() + self.get_short_exe_name(ht)

    def get_complete_exe_name(self, ht):
        return self.get_short_exe_name(ht)

    def get_result_hex(self, lines, name):
        for line in lines:
            pos = line.find(name)
            if pos != -1:
               info = line[pos + len(name):]
               return int(info, 16)
        return None

    def get_result(self, lines, name):
        for line in lines:
            pos = line.find(name)
            if pos != -1:
               info = line[pos + len(name):]
               return float(info)
        return None

    def check_result(self, platform, folder, result, ht):
        result_ht = {}

        lines = ht['stdout'].split('\n')
        time = self.get_result(lines, 'Time: ')

        if time == None:
            raise Exception('Invalid time ' + str(time))

        result_ht['total_time'] = time

        return result_ht

