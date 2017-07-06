from benchmarks.benchmarks import Benchmark
from benchmarks.upcbench_heat_multid import *
from parameters import *
from user_parameters import *

import os

class ParamHWSupport(Parameter):
    name = 'PGASHWSupport'
    valid_values = ['yes', 'no']

class BenchmarkUBHeatMultiDHW(BenchmarkUBHeatMultiD):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/upc_benchmarks/heat_multid/'
    needed_files = []

    def __init__(self, size_list=None):
        self.parameters = [
                ParamHeatMultiDSize(size_list),
                ParamHeatMultiDOpt(),
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
        cmd = "make -j 4  UPCC=\\\"%(upcc)s\\\" MATRIX_SIZE=%(ParamHeatMultiDSize)d THREADS=%(ParamCores)d MANUAL_OPT=%(ParamHeatMultiDOpt)s " % ht
        return cmd

    def get_complete_exe_name(self, ht):
        return self.get_exe_name(ht) + '_%(ParamBerkeleyOpt)s.%(ParamHWSupport)s' % ht

