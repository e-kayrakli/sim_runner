from platforms.platform import *
from jobschedulers.jobscheduler_all import *
from jobschedulers.job import Job
import copy
import os
import re
import sys
import util

import configuration_gem5

job_scheduler = get_current_scheduler()

class ParamCPUType(Parameter):
    def __init__(self, cpu_type=None):
        if cpu_type != None:
            self.valid_values = cpu_type.copy()
        else:
            self.valid_values = ['atomic', 'timing', 'detailed'] # 'inorder',

class ParamL1Size(Parameter):
    def __init__(self):
        self.valid_values = [0, 32]

class ParamL2Size(Parameter):
    def __init__(self):
        self.valid_values = [0, 4096]

class ParamBerkeleyOpt(Parameter):
    def __init__(self, opt_list=None):
        if opt_list == None:
            self.valid_values = ['BO0', 'BO1', 'BO2', 'BO3']
        else:
            self.valid_values = copy.deepcopy(opt_list)

class ParamGCCOpt(Parameter):
    def __init__(self):
        self.valid_values = ['O3']

class ParamBerkeleyThreadsStatic(Parameter):
    def __init__(self, alsoDynamic=False):
        if alsoDynamic:
            self.valid_values = ['Static', 'Dyna']
        else:
            self.valid_values = ['Static']

class ParamCoresPerL2(Parameter):
    def __init__(self):
        #self.valid_values = [8, 64]
        self.valid_values = [64]
        self.default_value = 64

class PlatformGem5AlphaBerkeley(Platform):
    def __init__(self, param_cores=[1, 2, 4, 8, 16], cpu_type=None, opt_list=None):
        self.parameters = [
                ParamCores(list=param_cores, max=512),
                ParamCPUType(cpu_type),
                ParamL1Size(),
                ParamL2Size(),
                ParamBerkeleyThreadsStatic(),
                ParamBerkeleyOpt(opt_list),
                ParamGCCOpt(),
                ParamCoresPerL2()
        ]
        super().__init__()

    def check_if_valid(self):
        hostname = util.get_hostname()
        return True

    def check_vector_validity(self, *args, **kwargs):
        cores = self.get_param_value(ParamCores)
        l1 = self.get_param_value(ParamL1Size)
        l2 = self.get_param_value(ParamL2Size)
        cores_per_l2 = self.get_param_value(ParamCoresPerL2)

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

        berkeley_opt = self.get_param_value(ParamBerkeleyOpt)
        if berkeley_opt not in ['BO1', 'BO3']:
            return False

        if berkeley_opt == 'BO3':
            if l1 == 128:
                return False

        if cpu_type == 'detailed':
            if cores > 16:
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
        job.nb_cores = 2.5
        # TODO max_time predictor

    def prepare_run(self, benchmark, task=None):
        self.create_rcS(benchmark)

    def get_compile_cmd(self, benchmark):
        ht = self.get_ht(benchmark)

        if self.get_param_value(ParamBerkeleyThreadsStatic) == 'Static':
            ht['ParamStatic'] = 1
        else:
            ht['ParamStatic'] = 0

        berkeley_opt = self.get_param_value(ParamBerkeleyOpt)
        ht['ExtraBerkeleyOpt'] = ''
        if berkeley_opt == 'BO2':
            ht['ExtraBerkeleyOpt'] = '-O'

        if berkeley_opt == 'BO3':
            ht['ExtraBerkeleyOpt'] = '-O -opt'

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

        cmd_run = """LINUX_IMAGE=%(linux_image)s %(gem5_exe)s -d %(output_folder)s %(gem5_conf_py)s --disable_all_listeners %(cache_config)s --cpu-type=%(cpu_type)s -n %(nb_cores)d --mem-size=1024MB --script=./rcS""" % locals()

        return cmd_run

    def create_rcS(self, benchmark):
        exe_name = os.path.basename(self.get_complete_exe_name(benchmark))
        params = benchmark.get_params()
        s = """#!/bin/sh
echo rcS
cd /build_dir

/sbin/m5 resetstats

/build_dir/%(exe_name)s %(params)s

/sbin/m5 dumpstats

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
            return ht[name]
        return None

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
            #raise Exception('Still running, m5_exit not encountered, last line:' + lines[-2])

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

        lines_pgas = [l for l in lines if l.startswith('system.cpu')]
        lines_pgas = [l for l in lines_pgas if l.find('pgas') != -1]

        for l in lines:
            self.get_info_float(l, 'host_seconds', ht)
            self.get_info_float(l, 'sim_seconds', ht)
            self.get_info_int(l, 'host_mem_usage', ht)
            self.get_info_int(l, 'host_inst_rate', ht)
            self.get_info_int(l, 'system.physmem.bytesRead', ht)
            self.get_info_int(l, 'system.physmem.bytesWritten', ht)
        cores = self.get_param_value(ParamCores)
        lds_lst = []
        sts_lst = []
        for l in lines_pgas:
            for i in range(cores):
                lds = self.get_info_int(l, 'system.cpu' + str(i) + '.num_pgas_loads', ht)
                if lds != None:
                    lds_lst.append(lds)
                sts = self.get_info_int(l, 'system.cpu' + str(i) + '.num_pgas_stores', ht)
                if sts != None:
                    sts_lst.append(sts)

        if len(lds_lst):
            ht['system.cpu.num_pgas_loads'] = sum(lds_lst) / len(lds_lst)
        else:
            for l in lines_pgas:
                self.get_info_int(l, 'system.cpu.num_pgas_loads', ht)
        if len(sts_lst):
            ht['system.cpu.num_pgas_stores'] = sum(sts_lst) / len(sts_lst)
        else:
            for l in lines_pgas:
                self.get_info_int(l, 'system.cpu.num_pgas_stores', ht)

        #if 'system.cpu.num_pgas_stores' not in ht:
        #    raise Exception('No PGAS infos')

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

