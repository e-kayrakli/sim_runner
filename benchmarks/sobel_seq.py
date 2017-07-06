from benchmarks.benchmarks import *
from parameters import *
from benchmarks.sobel import ParamImageSize
from user_parameters import *

import os

class BenchmarkSobelSeq( Benchmark ):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/tilera64/tests/sobel_seq/'
    needed_files = ['512.pgm', '1024.pgm', '2048.pgm']

    def __init__(self):
        self.parameters = [ParamImageSize()]
        super().__init__()

    def check_vector_validity(self, *args, **kwargs):
        return True

    def get_compile_cmd(self, ht):
        cmd = "make IMAGE_SIZE=%(ParamImageSize)d UPCC=%(upcc)s " % ht
        return cmd

    def get_run_cmd(self, ht, cmd_run):
        ht['exe_name'] = self.get_exe_name(ht)
        ht['exe_basename'] = os.path.basename( self.get_exe_name(ht) )
        cmd = cmd_run % ht
        return cmd.replace('--run', '--here --run').replace('hello', 'sobel')

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



