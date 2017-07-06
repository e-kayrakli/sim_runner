from platforms.platform import *
from jobschedulers.jobscheduler_all import *
from jobschedulers.job import Job
import util

job_scheduler = get_current_scheduler()

class ParamBerkeleyOptimization(Parameter):
    default_value = 'O_disabled'

    def __init__(self, disable_optimization=False):
        self.valid_values = ['O_enabled']
        if disable_optimization:
            self.valid_values.append('O_disabled')

class ParamBerkeleyTranslatorOptimization(Parameter):
    default_value = 'opt_disabled'
    valid_values = ['opt_enabled', 'opt_disabled']

class PlatformBerkeley(Platform):
    invalid_hostnames = ['cray', 'tile.hpcl.gwu.edu']

    def __init__(self, disable_optimization=False, experimental=False, conduits=[], param_cores=[8,16,32,64,128,256]):
        self.parameters = [
                ParamConduit(conduits),
                ParamCores(list=param_cores, max=512),
                ParamBerkeleyOptimization(disable_optimization)
        ]
        if experimental:
            self.parameters.append( ParamBerkeleyTranslatorOptimization() )
        super().__init__()

    def check_if_valid(self):
        return all(map(lambda h: h != util.get_hostname(), self.invalid_hostnames))

    def submit_job(self, benchmark, job, instance):
        ht = self.get_ht(benchmark)
        nb_cores = ht['ParamCores']
        job.nb_cores = nb_cores

        cmd = self.get_upc_run_cmd(benchmark)
        job.cmd = cmd

        max_time = instance.get_result_max('total_time')
        job.set_max_time(max_time)

    def prepare_run(self, benchmark, task=None):
        ht = self.get_ht(task.instance.benchmark)
        name = task.instance.benchmark.format_vector() + '_' + \
               task.instance.platform.format_vector()
        nb_cores = ht['ParamCores']
        max_time = task.instance.get_result_max('total_time')

    def get_compile_cmd(self, benchmark):
        ht = self.get_ht(benchmark)
        proc = ht["ParamCores"]

        base_memory = 4096
        max_memory = int(base_memory / 8)
        if proc < 8:
            max_memory = int(base_memory / proc)

        ht['ucc'] = "\\\"gcc -O3 \\\"" % locals()
        ht['upcc_nb_threads_opt'] = '-T'
        ht['platform'] = 'berkeley'

        opt = ''
        if ht['ParamBerkeleyOptimization'] == 'O_enabled':
            opt = '-O'

        opt_trans = ''
        if ht.get('ParamBerkeleyTranslatorOptimization') == 'opt_enabled':
            opt_trans = '-opt'

        ParamConduit = ht["ParamConduit"]

        if ParamConduit == 'smp':
            ht["upcc"] = "\\\"upcc -v -network=%(ParamConduit)s -pthreads=%(proc)d -shared-heap=%(max_memory)d %(opt)s %(opt_trans)s \\\"" % locals()
        else:
            ht["upcc"] = "\\\"upcc -v -network=%(ParamConduit)s -shared-heap=%(max_memory)d %(opt)s %(opt_trans)s \\\"" % locals()

        ht['platform_make_parms'] = "-j 4 UPC=%(platform)s BUPC_NETWORK=%(ParamConduit)s THREADS=%(ParamCores)d" % ht
        return benchmark.get_compile_cmd(ht)

    def get_upc_run_cmd(self, benchmark):
        ht = self.get_ht(benchmark)

        proc = ht["ParamCores"]
        max_memory = 384

        if proc < 8:
            max_memory = int(3584 / proc)


        if ht["ParamConduit"] == 'smp':
            cmd_run = """time ./%(exe_basename)s"""
        else:
            cmd_run = 'upcrun  -shared-heap=' + str(max_memory) + 'MB -n %(ParamCores)d %(exe_basename)s'

        cmd = benchmark.get_run_cmd(ht, cmd_run)
        return cmd

    def precheck_result(self, bench, path):
        with open(path + '0004_run.log', 'r') as f:
            data = f.read()

    def check_result(self, bench, folder, result):
        ht = {}
        path = folder + result + '/'

        data = job_scheduler.read_stdout(folder, result)

        ht['stderr'] = ''
        ht['stdout'] = data

        try:
            result_ht = bench.check_result(self, folder, result, ht)
        except Exception as e:
            if ht['stderr'].find('Assertion') != -1:
                print('svn delete --force ' + path)
            raise e

        return result_ht

