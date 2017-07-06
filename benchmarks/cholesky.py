from benchmarks.benchmarks import *
from parameters import *
from user_parameters import *

import os

class ParamCholeskyTK( Parameter ):
    valid_values = [29]
    dir_format = '%.3d'

class BenchmarkCholesky( Benchmark ):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/hpcl/tools/run_benchmark/dummy/'
    needed_files = []

    def __init__(self):
        self.parameters = [ParamCholeskyTK()]
        super().__init__()

    def get_checkpointname(self, platform):
        ht = platform.get_ht(self)
        cache = self.get_cache_size(ht)
        return 'cholesky-tk' + str(ht['ParamCholeskyTK']) + '-' + cache + '_' + str(ht['ParamCores']) + 'p_warm2'

    def get_cachename(self, platform):
        ht = platform.get_ht(self)
        return 'cholesky-%(ParamCores)dp-2M_caches.gz' % ht

    def get_cache_size(self, ht):
        cache_size = 2 ** ht['ParamL2SetBits'] * 256
        trans = {512*1024: '512K', 1024*1024: '1M', 2*1024*1024: '2M'}
        return trans[cache_size]

    def get_ht(self, platform):
        ht = self.get_ht_based_on_vector()
        ht.update( platform.get_ht_based_on_vector() )
        ht['trace'] = 'cholesky_%(ParamCholeskyTK)s_MOESI_SMP_dir2_%(ParamCores)dp.trace' % ht
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

