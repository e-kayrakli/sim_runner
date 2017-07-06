from platforms.platform import *
from terminalcontroller import *
from jobschedulers.jobscheduler_all import *
import util

job_scheduler = get_current_scheduler()

class PlatformChapel(Platform):
    def __init__(self, param_cores=[8,16,32,64,128,256]):
        self.parameters = [
                ParamCores(list=param_cores, max=1024),
        ]
        super().__init__()

    def check_if_valid(self):
        return util.get_hostname() in ['cray', 'bulldozer-server']

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
        name = task.instance.get_canonical_name()
        name = task.instance.benchmark.format_vector() + '_' + \
               task.instance.platform.format_vector()
        cmd = self.get_upc_run_cmd(benchmark)
        nb_cores = ht['ParamCores']
        max_time = task.instance.get_result_max('total_time')

    def get_compile_cmd(self, benchmark):
        ht = self.get_ht(benchmark)
        proc = ht["ParamCores"]
        #opt = '-' + ht['ParamOptimization']

        #ht["upcc"] = "\\\"cc -## -h upc %(opt)s \\\"" % locals()
        #ht['ucc'] = "cc"
        #ht['upcc_nb_threads_opt'] = '-X'

        ht['platform'] = 'cray'
        ht['platform_make_parms'] = "UPC=%(platform)s THREADS=%(ParamCores)d" % ht

        return benchmark.get_compile_cmd(ht)

    def get_upc_run_cmd(self, benchmark):
        ht = self.get_ht(benchmark)
        if util.get_hostname() in ['cray']:
            cmd_run = "aprun -n %(ParamCores)d -m 1325M %(exe_basename)s"
        else:
            cmd_run = "./%(exe_basename)s --numThreadsPerLocale=%(ParamCores)d"
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

