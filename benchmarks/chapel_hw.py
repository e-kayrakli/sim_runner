from benchmarks.benchmarks import *
from parameters import *
from user_parameters import *

import os

class ParamTestKernels(Parameter):
    name = "TestKernels"

    def __init__(self, kernels=None):
        if kernels != None:
            self.valid_values = kernels.copy()
        else:
            self.valid_values = ['mm', 'ra', 'vector_add', 'hd', 'is']

class ParamBenchClasses(Parameter):
    name = "BenchClasses"
    possible_values = ['S', 'W' , 'A', 'B', 'C']

    def __init__(self, minClass='S', maxClass='S'):
        ind = self.possible_values.index(minClass)
        ind2 = self.possible_values.index(maxClass) + 1
        self.valid_values = self.possible_values[ind:ind2]

class ParamManualOptimizationLevel(Parameter):
    name = "ManualOptimizationLevel"
    valid_values = ['O0', 'O1', 'O2']

class ParamHWSupport(Parameter):
    name = 'HWSupport'
    valid_values = ['yes', 'no']

class BenchmarkChapelHW(Benchmark):
    benchmark_path = home_folder + 'projects/hardware/simulator/test_alpha/chapel/'
    auto_parameters = [AutoParamTime(), AutoParamDate(), AutoParamHostname(), AutoParamSVNRevision(benchmark_path)]
    needed_files = []

    def __init__(self, minClass='S', maxClass='W', kernels=None):
        self.parameters = [
                ParamTestKernels(kernels),
                ParamBenchClasses(minClass, maxClass),
                ParamManualOptimizationLevel(),
                ParamHWSupport()
                ]
        super().__init__()

    def check_vector_validity(self, *args, **kwargs):
        optLevel = self.get_param_value(ParamManualOptimizationLevel)
        kernel = self.get_param_value(ParamTestKernels)
        benchClass = self.get_param_value(ParamBenchClasses)
        hwSupport = self.get_param_value(ParamHWSupport)

        if len(args) > 0:
            platform = args[0]
            ncores = platform.get_param_value(ParamCores)
            cpu_type = platform.get_param_value('ParamCPUType')

            if kernel == 'mm':
                if benchClass == 'S':
                    if ncores > 32:
                        return False
            if kernel == 'hd':
                if benchClass == 'S':
                    if ncores > 32:
                        return False

        if hwSupport == 'yes':
            if optLevel != 'O0':
                return False

        if kernel == 'vector_add':
            if optLevel not in ['O0', 'O1']:
                return False

        if kernel == 'mm':
            if optLevel not in ['O0', 'O1']:
                return False

        if kernel == 'ra':
            if optLevel not in ['O0']:
                return False

        if kernel == 'hd':
            if optLevel not in ['O0']:
                return False
            if benchClass not in ['S', 'W']:
                return False

        if kernel == 'is':
            if hwSupport == 'yes':
                return False
            if benchClass not in ['S']:
                return False
            if optLevel not in ['O0']:
                return False

        return True

    def get_compile_cmd(self, ht):
        cores = ht['ParamCores']
        ht['sharedHeap'] = 1024 / cores

        ht['chpl'] = 'chpl --static' % ht
        ht['subfolder'] = '%(ParamTestKernels)s' % ht

        if ht['ParamHWSupport'] == 'yes':
            ht['target_name'] = '%(ParamTestKernels)s' % ht
        else:
            ht['target_name'] = '%(ParamTestKernels)s_soft' % ht

        cmd = """make -j 4 WITH_HW_SUPPORT=%(ParamHWSupport)s CLASS=%(ParamBenchClasses)s NP=%(ParamCores)d VARIANT=%(ParamManualOptimizationLevel)s %(target_name)s""" % ht
        return cmd

    def get_params(self):
        bench_class = self.get_param_value('ParamBenchClasses')

        mm_class = {'S': 32, 'W': 64, 'A': 128, 'B': 256}
        ra_class = {'S': 16, 'W': 18, 'A': 20, 'B': 22}
        vector_add_class = {'S': 512*1024, 'W': 2*1024*1024, 'A': 4*1024*1024}

        optLevelN = self.get_param_value('ParamManualOptimizationLevel')[1]
        kernel = self.get_param_value(ParamTestKernels)

        if kernel == 'vector_add':
            vector_add_size = vector_add_class[bench_class]
            params = ' -smanual_optimizations=%(optLevelN)s -sN=%(vector_add_size)d ' % locals()
        elif kernel == 'mm':
            mm_size = mm_class[bench_class]
            params = ' -smanual_optimizations=%(optLevelN)s -sN=%(mm_size)d ' % locals()
        elif kernel == 'ra':
            ra_size = ra_class[bench_class]
            params = ' -smanual_optimizations=%(optLevelN)s -sN=%(ra_size)d ' % locals()
        elif kernel == 'hd':
            mm_size = mm_class[bench_class]
            params = ' -smanual_optimizations=%(optLevelN)s -sN=%(mm_size)d ' % locals()
        elif kernel == 'is':
            mm_class = {'S': 32}  # TODO (place holder)
            mm_size = mm_class[bench_class]
            params = '  ' % locals()
        else:
            raise Exception('Unknown bench')

        return params

    def get_run_cmd(self, ht, cmd_run):
        ht['exe_name'] = os.path.basename(self.get_exe_name(ht))
        ht['exe_basename'] = os.path.basename(self.get_exe_name(ht))

        return cmd_run % ht + params

    def get_path(self):
        return self.benchmark_path

    def get_short_exe_name(self, ht):
        return self.get_exe_name(ht)

    def get_exe_name(self, ht):
        ht['ParamTestKernels_u'] = ht['ParamTestKernels'].upper()
        if ht['ParamHWSupport'] == 'yes':
            return self.get_path() + '%(ParamTestKernels)s_real' % ht
        else:
            return self.get_path() + '%(ParamTestKernels)s_soft_real' % ht

    def get_complete_exe_name(self, ht):
        kernel = self.get_param_value(ParamTestKernels)
        return self.get_exe_name(ht) + '_%(ParamHWSupport)s' % ht

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
        list_total_time_names = ["Time: ", 'Execution time = ', 'Execution Time = ', ' Time in seconds =                   ']
        lines = ht['stdout'].split('\n')
        for e in list_total_time_names:
            if not time:
                time = self.get_result(lines, e)

        if not time:
            raise Exception('No time found')

        result_ht = {}
        result_ht['total_time'] = time

        return result_ht

