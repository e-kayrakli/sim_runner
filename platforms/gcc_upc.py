from platforms.platform import *

from util import get_hostname
import sys
import subprocess
import time

class PlatformGCCUPC(Platform):
    def __init__(self):
        self.parameters = [
                ParamCores(max=16),
        ]
        super().__init__()

    def check_if_valid(self):
        return True

    def get_compile_cmd(self, benchmark):
        ht = self.get_ht(benchmark)

        proc = ht["ParamCores"]

        ht['ucc'] = "\\\"gcc -O3 \\\"" % locals()
        ht['upcc_nb_threads_opt'] = '-T'
        ht['platform'] = 'gccupc'

        ht["upcc"] = "\\\"upc \\\"" % locals()

        return benchmark.get_compile_cmd(ht)

    def get_run_cmd(self, benchmark):
        ht = self.get_ht(benchmark)
        cmd_run = """time ./%(exe_basename)s -n %(ParamCores)d %(extra_parameters)s """
        return benchmark.get_run_cmd(ht, cmd_run)

    def precheck_result(self, bench, path):
        with open(path + '0004_run.log', 'r') as f:
            data = f.read()

    def check_result(self, bench, folder, result):
        ht = {}
        path = folder + result + '/'

        data = self.get_result_data(folder, result, '0004_run.log')

        ht['stderr'] = ''
        ht['stdout'] = data

        try:
            result_ht = bench.check_result( self, folder, result, ht )
        except Exception as e:
            if ht['stderr'].find('Assertion') != -1:
                print('svn delete --force ' + path)
            raise e

        return result_ht

