from benchmarks.benchmarks import *
from parameters import *
from user_parameters import *

import os

class ParamNPBTests(Parameter):
    name = "NPBTests"
    valid_values = ['is', 'ep', 'cg', 'mg', 'ft']

    def __init__(self, kernel_list=None):
        if kernel_list != None:
            self.valid_values = kernel_list

class ParamNPBClasses( Parameter ):
    name = "NPBClasses"
    possible_values = ['S', 'W', 'A', 'B', 'C', 'D', 'E']

    def __init__(self, minClass='S', maxClass='C'):
        ind = self.possible_values.index(minClass)
        ind2 = self.possible_values.index(maxClass) + 1
        self.valid_values = self.possible_values[ind:ind2]

class ParamUPCManualOptimizationLevel(Parameter):
    name = "UPCManualOptimizationLevel"
    valid_values = ['O0', 'O1', 'O1static', 'O3', 'O3static']

class BenchmarkNPB(Benchmark):
    benchmark_path = home_folder + 'projects/npb-upc/'
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname(), AutoParamSVNRevision(benchmark_path)]
    needed_files = []

    def __init__(self, minClass='S', maxClass='C', kernel_list=None):
        self.parameters = [
                ParamNPBTests(kernel_list),
                ParamNPBClasses(minClass, maxClass),
                ParamUPCManualOptimizationLevel()
            ]
        super().__init__()

    def check_vector_validity(self, *args, **kwargs):
        optLevel = self.get_param_value(ParamUPCManualOptimizationLevel)
        npbTest = self.get_param_value(ParamNPBTests)
        npbClass = self.get_param_value(ParamNPBClasses)

        if len(args) > 0:
            platform = args[0]
            ncores = platform.get_param_value(ParamCores)

            ft_max_procs = {'S': 64, 'W': 32, 'A': 128, 'B': 256, 'C': 512, 'D': 1024, 'E': 2048}
            if npbTest == 'ft':
                if ft_max_procs[npbClass] < ncores:
                    return False

            ft_min_procs = {'D': 128, 'E': 1024}
            ft_min = ft_min_procs.get(npbClass, None)
            if ft_min != None:
                if ncores < ft_min:
                    return False

        if optLevel == 'O1static':
            if not npbTest in ['ft', 'is']:
                return False
        if optLevel == 'O3static':
            if npbTest != 'cg':
                return False
        if npbTest == 'ep':
            if optLevel != 'O0':
                return False
        if npbTest in ['ft', 'is']:
            if optLevel == 'O3':
                return False

        return True

    def get_compile_cmd(self, ht):
        cmd = "make -j 4 %(ParamNPBTests)s UPCC=%(upcc)s CLASS=%(ParamNPBClasses)s NP=%(ParamCores)d NB_PROCS=%(ParamCores)d UPCTHREADS=%(ParamCores)d VARIANT=%(ParamUPCManualOptimizationLevel)s HOST_CC=gcc UCC=%(ucc)s UPCC_STAT_THREADS=%(upcc_nb_threads_opt)s " % ht
        return cmd

    def get_run_cmd(self, ht, cmd_run):
        ht['exe_name'] = self.get_exe_name(ht)
        ht['exe_basename'] = os.path.basename(self.get_exe_name(ht))
        return cmd_run % ht

    def get_path(self):
        return self.benchmark_path

    def get_exe_name(self, ht):
        ht['ParamNPBTests_u'] = ht['ParamNPBTests'].upper()
        return self.get_path() + '%(ParamNPBTests_u)s/%(ParamNPBTests)s.%(ParamNPBClasses)s.%(ParamUPCManualOptimizationLevel)s.%(ParamCores)d' % ht

    def get_result(self, lines, name):
        for line in lines:
            if line.find(name) != - 1:
               info = line[len(name):]
               str = info.strip().split(",")[0]
               return float(str.strip('sec '))
        return None

    def check_result(self, platform, folder, result, ht):
        if ht['stdout'].find('UNSUCCESSFUL') != -1:
            raise Exception('Unsuccessful run ' + folder)

        for line in ht['stdout'].split('\n'):
            if line.find('ERROR') != -1:
                raise Exception('Error :' + line)

        time = None
        list_total_time_names = ["        total time:", "          total  = ", "      total time: ", "Total time:", " Time in seconds = ", "Execution Time:"]
        lines = ht['stdout'].split('\n')
        for e in list_total_time_names:
            if not time:
                time = self.get_result(lines, e)

        if not time:
            raise Exception('No time found')

        result_ht = {}
        result_ht['total_time'] = time

        return result_ht

