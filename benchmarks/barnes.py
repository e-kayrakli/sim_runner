from benchmarks.benchmarks import *
from parameters import *
from user_parameters import *

import os

class ParamBarnesSize( Parameter ):
    valid_values = [1024, 16*1024]
    dir_format = '%.5d'

class BenchmarkBarnes( Benchmark ):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/hpcl/tools/run_benchmark/dummy/'
    needed_files = []

    def __init__(self):
        self.parameters = [ParamBarnesSize()]
        super().__init__()

    def get_checkpointname(self, platform):
        ht = platform.get_ht(self)
        trans = {512: '512', 1024: '1k', 16*1024: '16k', 64*1024: '64k'}
        return 'barnes-' + trans[ht['ParamBarnesSize']] + '_' + str(ht['ParamCores']) + 'p_warm2'

    def get_cachename(self, platform):
        ht = platform.get_ht(self)
        return  'barnes-%(ParamCores)dp-2M_caches.gz' % ht

    def get_ht(self, platform):
        ht = self.get_ht_based_on_vector()
        ht.update( platform.get_ht_based_on_vector() )
        trans = {512: '512', 1024: '1k', 16*1024: '16k', 64*1024: '64k'}
        ht['barnessize'] = trans[ht['ParamBarnesSize']]
        ht['trace'] = 'barnes_%(barnessize)s_MOESI_SMP_dir2_%(ParamCores)dp.trace' % ht
        return ht

    def check_validity(self, platform):
        size = self.get_param_value( ParamBarnesSize )
        platform_name = platform.get_name()

        if platform_name == 'GemsTrace':
            if size == 1024:
                return False

        return True

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
        return self.get_path() + 'barnes' % ht

    def check_result(self, platform, folder, result, ht):
        return None

