from benchmarks.benchmarks import *
from parameters import *
from user_parameters import *

import os

class ParamRaytrace(Parameter):
    valid_values = ['teapot', 'car']

class BenchmarkRaytrace(Benchmark):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/hpcl/tools/run_benchmark/dummy/'
    needed_files = []

    def __init__(self):
        self.parameters = [ParamRaytrace()]
        super().__init__()

    def get_checkpointname(self, platform):
        ht = platform.get_ht(self)
        if ht['ParamCores'] == 16:
            check = 'raytrace_%(ParamCores)dp_warm2' % ht
        else:
            check = 'raytrace-%(ParamRaytrace)s_%(ParamCores)dp_warm2' % ht
        return check

    def get_cachename(self, platform):
        ht = platform.get_ht(self)
        return 'raytrace-%(ParamCores)dp-2M_caches.gz' % ht

    def get_ht(self, platform):
        ht = self.get_ht_based_on_vector()
        ht.update( platform.get_ht_based_on_vector() )
        ht['trace'] = 'raytrace_%(ParamRaytrace)s_MOESI_SMP_dir2_%(ParamCores)dp.trace' % ht
        return ht

    def check_vector_validity(self, *args, **kwargs):
        return True

    def get_compile_cmd(self, ht):
        cmd = "ls" % ht
        return cmd

    def get_run_cmd(self, ht, cmd_run):
        ht['exe_name'] = self.get_exe_name(ht)
        return cmd_run % ht

    def get_path(self):
        return self.benchmark_path

    def get_exe_name(self, ht):
        return None

    def check_result(self, platform, folder, result, ht):
        return None

