from platforms.platform import *
from jobschedulers.jobscheduler_all import *
from jobschedulers.job import Job
import util
import os
import sys
import re

import configuration_gem5

job_scheduler = get_current_scheduler()

class ParamCPUType(Parameter):
    def __init__(self, cpu_type=None):
        if cpu_type != None:
            self.valid_values = cpu_type.copy()
        else:
            self.valid_values = ['atomic', 'timing', 'inorder', 'detailed']

class ParamNbLocales(Parameter):
    def __init__(self):
        self.valid_values = [1, 2, 4, 8, 16, 32, 64]

class ParamL1Size(Parameter):
    def __init__(self):
        self.valid_values = [0, 32]

class ParamL2Size(Parameter):
    def __init__(self):
        self.valid_values = [0, 4096]

class ParamCompilerOpt(Parameter):
    def __init__(self):
        self.valid_values = ['BO3'] # 'BO0', 'BO1', 'BO2'

class ParamCoresPerL2(Parameter):
    def __init__(self):
        self.valid_values = [64]

class PlatformGem5Chapel(Platform):
    def __init__(self, param_cores=[1, 2, 4, 8, 16], cpu_type=None):
        self.parameters = [
                ParamCores(list=param_cores, max=512),
                ParamNbLocales(),
                ParamCPUType(cpu_type),
                ParamL1Size(),
                ParamL2Size(),
                ParamCompilerOpt(),
                ParamCoresPerL2()
        ]
        super().__init__()

    def check_if_valid(self):
        hostname = util.get_hostname()
        return True

    def check_vector_validity(self, *args, **kwargs):
        cores = self.get_param_value(ParamCores)
        nb_locales = self.get_param_value(ParamNbLocales)
        l1 = self.get_param_value(ParamL1Size)
        l2 = self.get_param_value(ParamL2Size)
        cores_per_l2 = self.get_param_value(ParamCoresPerL2)

        if nb_locales > cores:
            return False

        if nb_locales > 4 and nb_locales != cores:
            return False

        if l1 == 0 and l2 != 0:     # No L2 without L1
            return False

        cpu_type = self.get_param_value(ParamCPUType)

        if cpu_type == 'atomic':    # No cache with atomic
            if cores_per_l2 != 64:
                return False
            if l1 != 0 or l2 != 0:
                return False

        if cpu_type in ['timing', 'inorder', 'detailed']:    # Need L1 with timing
            if l1 == 0:
                return False

        if l2 == 0 and l1 != 0:     # No L2 without L1
            return False

        compiler_opt = self.get_param_value(ParamCompilerOpt)

        if cpu_type == 'detailed':
            if cores > 8:          # Modified to generate graphs, was 32
                return False

        if cpu_type == 'inorder':
            if cores > 8:
                return False

        if cpu_type == 'timing':
            if cores > 64:
                return False

        return True

    def submit_job(self, benchmark, job, instance):
        job.cmd = self.get_upc_run_cmd(benchmark)
        job.allow_grouping = True
        hostname = util.get_hostname()
        if hostname == 'login':
            job.nb_cores = 1.0
        else:
            job.nb_cores = 2.0
        # TODO max_time predictor

    def prepare_run(self, benchmark, task=None):
        self.create_rcS(benchmark)

    def get_compile_cmd(self, benchmark):
        ht = self.get_ht(benchmark)
        compiler_opt = self.get_param_value(ParamCompilerOpt)

        return benchmark.get_compile_cmd(ht)

    def get_upc_run_cmd(self, benchmark):
        ht = self.get_ht(benchmark)

        cpu_type = self.get_param_value(ParamCPUType)

        gem5_conf = configuration_gem5.ConfigGEM5
        gem5_exe = gem5_conf.build_dir + 'gem5.' + gem5_conf.opt_level + '.' + cpu_type
        gem5_conf_py = gem5_conf.source_dir + 'configs/example/fs.py'

        if util.get_hostname() == 'cray':
            gem5_exe = 'aprun ' + gem5_conf.build_dir + 'gem5.' + gem5_conf.opt_level + '.' + cpu_type
            gem5_conf_py = '/mnt/lustre_server/users/gem5/configs/example/fs.py'
        else:
            gem5_exe = gem5_conf.build_dir + 'gem5.' + gem5_conf.opt_level + '.' + cpu_type
            gem5_conf_py = gem5_conf.source_dir + 'configs/example/fs.py'

        linux_image = configuration_gem5.disk_image_path
        output_folder = '.'

        l1_size = self.get_param_value(ParamL1Size)
        l2_size = self.get_param_value(ParamL2Size)
        nb_cores = self.get_param_value(ParamCores)
        cores_per_l2 = self.get_param_value(ParamCoresPerL2)

        cache_config = '--caches --l2cache --l1i_size=%(l1_size)dkB --l1d_size=%(l1_size)dkB --l2_size=%(l2_size)dkB --num-cores-per-l2=%(cores_per_l2)d'% locals()
        if l1_size == 0:
            cache_config = ''

        cmd_run = """LINUX_IMAGE=%(linux_image)s %(gem5_exe)s -d %(output_folder)s %(gem5_conf_py)s --disable_all_listeners %(cache_config)s --cpu-type=%(cpu_type)s -n %(nb_cores)d --mem-size=2048MB --script=./rcS""" % locals()

        return cmd_run

    def create_rcS(self, benchmark):
        exe_name = os.path.basename(self.get_complete_exe_name(benchmark))
        params = benchmark.get_params()
        nb_cores = self.get_param_value(ParamCores)
        nb_locales = self.get_param_value(ParamNbLocales)

        s = """#!/bin/sh
echo rcS
cd /build_dir

ifconfig lo 127.0.0.1
export GASNET_MASTERIP=127.0.0.1
export GASNET_SSH_SERVERS=127.0.0.1
export GASNET_SPAWNFN="L"
export VERBOSEENV=1
export CHPL_LAUNCHCMD_DEBUG=1
export GASNET_ROUTE_OUTPUT=0
mount
mkdir /dev/shm
mount -t tmpfs none /dev/shm

echo
/sbin/m5 resetstats
echo Start %(exe_name)s %(nb_locales)d -v -nl %(nb_locales)d --printModuleInitOrder=true %(params)s
/build_dir/%(exe_name)s %(nb_locales)d -v -nl %(nb_locales)d --printModuleInitOrder=true %(params)s
/sbin/m5 dumpstats
echo

echo M5 exit
m5 exit
""" % locals()
        with open('rcS', 'w') as f:
            f.write(s)

    def get_run_cmd(self, benchmark):
        return job_scheduler.get_run_cmd()

    def precheck_result(self, bench, path):
        return

    @staticmethod
    def get_info_float(l, name, ht):
        if l.startswith(name):
            ht[name] = float(l.split()[1])

    @staticmethod
    def get_info_int(l, name, ht):
        if l.startswith(name):
            ht[name] = int(l.split()[1])

    def fix_issues(self, bench, folder, result):
        path = folder + result + '/'

    def check_result(self, bench, folder, result):
        ht = {}
        ht2 = {}
        path = folder + result + '/'

        data_err = job_scheduler.get_result_data(folder, result, 'result.err')
        data_err_lines = data_err.split('\n')
        filename = path + 'result.err'

        if len(data_err_lines) <  2:
            raise Exception('Empty result.err')

        data_out = job_scheduler.get_result_data(folder, result, 'result.out')
        if data_out.find('because m5_exit instruction encountered') == -1:
            data = job_scheduler.get_result_data(folder, result, 'system.terminal')
            lines = data.split('\n')
            raise Exception('Still running, m5_exit not encountered, last line:' + lines[-2])

        data = job_scheduler.get_result_data(folder, result, 'stats.txt')
        if not data:
            raise Exception('No stats.txt file; simulation still running or aborted')

        #if len(data_err_lines) > 10000:
        #    from itertools import groupby
        #    if os.path.isfile(filename) and not os.path.isfile(filename + '.orig'):
        #        with open(filename + '.orig', 'w') as f:
        #            f.write(data_err)
        #        with open(filename, 'w') as f:
        #            print('Too many lines, fixing ' + filename)
        #            for x, y in groupby(data_err_lines):
        #                len_dup = len(list(y))
        #                if len_dup > 1:
        #                    f.write(x + ' (x '+ str(len_dup) + ')\n')
        #                else:
        #                    f.write(x + '\n')

        for l in data_err_lines:
            if l.find('panic: M5 panic instruction called at pc') != -1:
                raise Exception('M5 panic instruction')
            if l.find('Assertion') != -1:
                raise Exception('Assertion Exception' + l)

        lines = data.split('\n')
        for l in lines:
            self.get_info_float(l, 'host_seconds', ht)
            self.get_info_float(l, 'sim_seconds', ht)
            self.get_info_int(l, 'host_mem_usage', ht)
            self.get_info_int(l, 'host_inst_rate', ht)
            self.get_info_int(l, 'system.physmem.bytesRead', ht)
            self.get_info_int(l, 'system.physmem.bytesWritten', ht)

        data = job_scheduler.get_result_data(folder, result, 'system.terminal')
        data = data.replace('serial8250: too much work for irq4\n\r', '')
        data = data.replace('serial8250: too much work for irq4\r\n', '')
        data = data.replace('serial8250: too much work for irq4\n', '')
        data = data.replace('serial8250: too much work for irq4\r', '')

        data = re.sub('ide3: unexpected interrupt, status=0xff, count=[0-9]+\n\r', '', data)
        data = re.sub('ide3: unexpected interrupt, status=0xff, count=[0-9]+\r\n', '', data)

        ht2['stdout'] = data

        result_ht = bench.check_result(self, folder, result, ht2)
        result_ht.update(ht)

        return result_ht

