from benchmarks.benchmarks import *
from parameters import *
from user_parameters import *

import os

class ParamPrecision( Parameter ):
    valid_values = [ 'single', 'double' ]

    def get_option(self, val):
        return 'SSCA_DOUBLE=' + str(self.valid_values.index(val))

class ParamScale( Parameter ):
    def __init__(self, maxScale=5):
        self.valid_values = [x for x in range(3, maxScale+1)]

class ParamFFT( Parameter ):
    def __init__(self, with_fftw=True):
        self.valid_values = ['FFT-UPC']
        if with_fftw:
            self.valid_values.append('FFTW')

    def get_option(self, val):
        return 'FFTW=' + str(self.valid_values.index(val))

class BenchmarkSSCA3( Benchmark ):
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname()]
    benchmark_path = home_folder + 'projects/ssca3/src/'
    needed_files = ['param_file.txt', 'letter/']

    def __init__(self, maxScale=4, withFFTW=False):
        self.parameters = [ParamPrecision(), ParamScale(maxScale), ParamFFT(withFFTW)]
        super().__init__()

    def get_ht(self):
        ht = self.get_ht_based_on_vector()
        ht['extra_parameters'] = 'param_file.txt'
        return ht

    def check_vector_validity(self, *args, **kwargs):
        return True

    def get_compile_cmd(self, ht):
        cmd = "make UPC=%(platform)s UPCC=%(upcc)s CC=%(upcc)s THREADS=%(ParamCores)d SSCA_SCALE=%(ParamScale)d %(ParamPrecision_option)s %(ParamFFT_option)s UPCC=%(upcc)s" % ht
        return cmd

    def get_run_cmd(self, ht, cmd_run):
        ht['exe_name'] = self.get_exe_name(ht)
        ht['exe_basename'] = os.path.basename( self.get_exe_name(ht) )
        return cmd_run % ht

    def get_path(self):
        return self.benchmark_path

    def get_exe_name(self, ht):
        return self.get_path() + 'ssca3' % ht

    def get_result(self, lines, name):
        for line in lines:
            pos = line.find(name)
            if pos != -1:
               info = line[pos + len(name):]
               str = info.strip().split(",")[0]
               return float(str.strip('sec '))
        return None

    def check_result(self, platform, folder, result, ht):
        time = None
        list_total_time_names = ["SSCA#3_total Time:"]
        lines = ht['stdout'].split('\n')
        for e in list_total_time_names:
            if not time:
                time = self.get_result(lines, e)

        if not time:
            raise Exception('No time found')

        result_ht = {}
        result_ht['total_time'] = time
        return result_ht

