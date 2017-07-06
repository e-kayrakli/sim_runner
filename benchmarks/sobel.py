from benchmarks.benchmarks import *
from parameters import *
from user_parameters import *

import os

class ParamNBRows( Parameter ):
    name = "NBRows"
    valid_values = [-1, 1, 8]

class ParamUPCOptimization( Parameter ):
    name = "UPCOptimization"
    valid_values = [1, 2, 3, 4, 5, 6, 7, 8]

class ParamImageSize( Parameter ):
    name = "ImageSize"
    valid_values = [512, 1024, 2048]

class BenchmarkSobel( Benchmark ):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/tilera64/tests/sobel/'
    needed_files = ['512.pgm', '1024.pgm', '2048.pgm']

    def __init__(self):
        self.parameters = [ParamImageSize(), ParamUPCOptimization(), ParamNBRows()]
        super().__init__()

    def check_vector_validity(self, *args, **kwargs):
        nb_rows = self.get_param_value( ParamNBRows )
        opt = self.get_param_value( ParamUPCOptimization )

        if opt in [2, 3, 4, 8]:
            if nb_rows != -1:
                return False

        return True

    def get_compile_cmd(self, ht):
        cmd = "make IMAGE_SIZE=%(ParamImageSize)d NB_ROWS=%(ParamNBRows)d UPCC=%(upcc)s THREADS=%(ParamCores)d UPC_OPT=%(ParamUPCOptimization)d " % ht
        return cmd

    def get_run_cmd(self, ht, cmd_run):
        ht['exe_name'] = self.get_exe_name(ht)
        ht['exe_basename'] = os.path.basename( self.get_exe_name(ht) )
        return cmd_run % ht

    def get_path(self):
        return self.benchmark_path

    def get_exe_name(self, ht):
        return self.get_path() + 'sobel' % ht

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
        if not time:
            print("rm -rf ", folder + result)

        result_ht = {}
        result_ht['total_time'] = time
        return result_ht



