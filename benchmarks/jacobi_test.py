from benchmarks.benchmarks import *
from parameters import *
from user_parameters import *

import os
import shutil
import util

class ParamTimeScaler(Parameter):
    def __init__(self):
        self.valid_values = [1.]

    def get_option(self, val):
        return 'time_scaler=' + str(val)

class BenchmarkJacobiTest(Benchmark):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/hardware/chapel_tests/jacobi/upc/'

    def __init__(self, is_chapel=False):
        self.parameters = [ParamTimeScaler()]
        self.needed_files = []
        self.is_chapel = is_chapel
        if is_chapel:
            self.benchmark_path = home_folder + 'projects/hardware/chapel_tests/jacobi/chapel/'
            self.needed_files = ['jacobi_real']
        super().__init__()


    def get_ht(self):
        ht = self.get_ht_based_on_vector()
        return ht

    def check_vector_validity(self, *args, **kwargs):
        return True

    def get_compile_cmd(self, ht):
        cmd = "make -j 4 %(platform_make_parms)s " % ht
        return cmd

    def get_run_cmd(self, ht, cmd_run):
        ht['exe_name'] = self.get_exe_name(ht)
        ht['exe_basename'] = os.path.basename(self.get_exe_name(ht))
        if self.is_chapel:
            return (cmd_run % ht)
        else:
            return (cmd_run % ht)

    def get_path(self):
        return self.benchmark_path

    def get_exe_name(self, ht):
        return self.get_path() + 'jacobi' % ht

    def get_result(self, lines, name):
        for line in lines:
            pos = line.find(name)
            if pos != -1:
                if pos != 0:
                    print(line)
                info = line[pos + len(name):]
                str = info.strip().split(",")[0]
                return float(str.strip('sec '))
        return None

    def get_result_ls(self, line, name, ht, htname):
        pos = line.find(name)
        if pos != -1:
            info = line[pos + len(name):]
            str = info.strip().split(",")[0]
            ht[htname] = float(str.strip('sec '))

    def check_result(self, platform, folder, result, ht):
        data = ht['stdout']
        pos = 0

        result_ht = {}
        pos = data.find('Total time:', pos)
        if pos != -1:
            end_line = data.find('\n', pos)
            line = data[pos:end_line]

            time = self.get_result_ls(line, "Total time: ", result_ht, 'total_time')

        if None in result_ht.values():
            raise Exception('Error')
        return result_ht

    def create_config_files(self):
        return
