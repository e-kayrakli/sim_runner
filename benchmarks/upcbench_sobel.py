from benchmarks.benchmarks import Benchmark
from parameters import *
from user_parameters import *

import os

class ParamSobelSize(Parameter):
    name = "SobelSize"

    def __init__(self, lst=None):
        if lst != None:
            self.valid_values = lst.copy()
        else:
            self.valid_values = [4096]

class ParamSobelOpt(Parameter):
    name = "ManualOpt"
    valid_values = ['MO_SOFT1', 'MO_SOFT2', 'MO_SOFT3']
    valid_values = ['MO_SOFT3', 'MO_SOFT4']

class BenchmarkUBSobel(Benchmark):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/upc_benchmarks/sobel/'
    needed_files = []

    def __init__(self, size_list=[512]):
        if not self.parameters:
            self.parameters = [
                    ParamSobelSize(size_list),
                    ParamSobelOpt()
                    ]
        super().__init__()

    def check_validity(self, platform):
        return True

    def get_compile_cmd(self, ht):
        ht['upcc'] = 'upcc_hw.py -Wc,-%(ParamGCCOpt)s -network=smp -T=%(ParamCores)d -pthreads=%(ParamCores)d -shared-heap=128MB %(ExtraBerkeleyOpt)s' % ht
        cmd = "make -j 4 MATRIX_SIZE=%(ParamSobelSize)d THREADS=%(ParamCores)d MANUAL_OPT=%(ParamSobelOpt)s " % ht
        return cmd

    def get_run_cmd(self, ht, cmd_run):
        ht['exe_name'] = os.path.basename(self.get_exe_name)
        ht['exe_basename'] = os.path.basename(self.get_exe_name(ht))
        return cmd_run % ht

    def get_path(self):
        return self.benchmark_path

    def get_short_exe_name(self, ht):
        return 'sobel.%(ParamCores)d.%(ParamSobelSize)d.%(ParamSobelOpt)s' % ht

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

from benchmarks.benchmarks import Benchmark
from benchmarks.upcbench_sobel import *
from parameters import *
from user_parameters import *

import os

class ParamHWSupport(Parameter):
    name = 'PGASHWSupport'
    valid_values = ['yes', 'no']

class BenchmarkUBSobelHW(BenchmarkUBSobel):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/upc_benchmarks/sobel/'
    needed_files = []

    def __init__(self, size_list=None):
        self.parameters = [
                ParamSobelSize(size_list),
                ParamSobelOpt(),
                ParamHWSupport()
                ]

        super().__init__()

    def check_validity(self, platform):
        hwSupport = self.get_param_value(ParamHWSupport)
        return True

    def get_compile_cmd(self, ht):
        hwSupport = self.get_param_value(ParamHWSupport)
        if hwSupport == 'yes':
            ht['upcc'] = 'upcc_hw.py' % ht
        else:
            ht['upcc'] = 'upcc' % ht
        cmd = "make -j 4  UPCC=\\\"%(upcc)s\\\" MATRIX_SIZE=%(ParamSobelSize)d THREADS=%(ParamCores)d MANUAL_OPT=%(ParamSobelOpt)s " % ht
        return cmd

    def get_complete_exe_name(self, ht):
        return self.get_exe_name(ht) + '_%(ParamBerkeleyOpt)s.%(ParamHWSupport)s' % ht

