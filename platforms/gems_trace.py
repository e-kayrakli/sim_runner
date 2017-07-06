from platforms.platform import *
from platforms.simics import *

import util
import time
import string

class PlatformGemsTrace(Platform):
    parameters = [
            ParamCores(list=[16, 64]),
            ParamProtocol(),
            ParamL2SetBits(),
            ParamRACSetBits(),
            ParamDCSetBits(),
            ParamNetworkFile(),
            ParamDelayInterventionLatency(),
            ParamSVThreshold(),
            ParamBAThreshold(),
            ParamNetworkBW(),
            ParamLatencyThreshold(),
        ]

    def prepare_run(self, benchmark, task=None):
        self.create_tester_config(task)
        self.create_sge_script(task)

    def check_if_valid(self):
        if util.get_hostname() == 'pyramid2.hpcl.gwu.edu':
            return True
        if util.get_hostname() == 'lyra.hpcl.gwu.edu':
            return True
        if self.if_hpc_servers():
            return True
        return False

    def if_hpc_servers(self):
        if util.get_hostname() == 'hpcserver1':
            return True
        if util.get_hostname() == 'hpcserver2':
            return True
        return False


    def check_vector_validity(self, *args, **kwargs):
        if self.get_param_value(ParamProtocol) == 'MOESI_SMP_dir2':
            if self.get_param_value(ParamDelayInterventionLatency) != 0 :
                return False
            if self.get_param_value(ParamSVThreshold) != 0:
                return False
            if self.get_param_value(ParamBAThreshold) != 0:
                return False
            if self.get_param_value(ParamNetworkBW) != 1000:
                return False
            if self.get_param_value(ParamLatencyThreshold) != 261:
                return False

        if self.get_param_value(ParamProtocol) == 'MOESI_SMP_APO3':
            if self.get_param_value(ParamDelayInterventionLatency) == 0 :
                return False
            if self.get_param_value(ParamSVThreshold) == 0:
                return False
            if self.get_param_value(ParamBAThreshold) != 100:
                return False
            if self.get_param_value(ParamNetworkBW) != 1000:
                return False
            if self.get_param_value(ParamLatencyThreshold) != 261:
                return False

        if self.get_param_value(ParamProtocol) == 'MOESI_SMP_APO4':
            if self.get_param_value(ParamDelayInterventionLatency) == 0 :
                return False
            if self.get_param_value(ParamSVThreshold) == 0:
                return False
            if self.get_param_value(ParamBAThreshold) != 100:
                return False
            if self.get_param_value(ParamNetworkBW) != 1000:
                return False
            if self.get_param_value(ParamLatencyThreshold) != 16:
                return False

        return True

    def get_qstat_out(self):
        qstat_out = subprocess.getoutput('qstat | wc -l').strip('\n').strip(' ')
        if qstat_out.find("fork: Resource temporarily unavailable No Permission. qstat: cannot connect to server sdb") != -1:
            return None
        try:
            val = int(qstat_out)
        except:
            val = None
        return val

    def wait_nb_task(self, nb=0):
        if self.if_hpc_servers():
            self.wait_nb_task_ps(8)
        else:
            self.wait_nb_task_sge(nb)

    def wait_nb_task_sge(self, nb=0):
        first = True

        val = self.get_qstat_out()
        while val == None or val > nb:
            if first:
                first = False
                print (term.YELLOW + 'Waiting for task to finish' + term.NORMAL, end='')
            if val == None:
                print(term.RED + '.' + term.NORMAL, end='')
            else:
                print('.', end='')
            sys.stdout.flush()
            time.sleep(10)
            val = self.get_qstat_out()
        if not first:
            print()

    def wait_nb_task_ps(self, nb=0):
        first = True

        procs = subprocess.getoutput('ps aux | grep tester.exec').split('\n')
        val = len(procs) -1
        while val == None or val > nb:
            if first:
                first = False
                print (term.YELLOW + 'Waiting for task to finish' + term.NORMAL, end='')
            if val == None:
                print(term.RED + '.' + term.NORMAL, end='')
            else:
                print('.', end='')
            sys.stdout.flush()
            time.sleep(10)
            procs = subprocess.getoutput('ps aux | grep tester.exec').split('\n')
            val = len(procs) -1
        if not first:
            print()

    def get_compile_cmd(self, benchmark):
        ht = self.get_ht(benchmark)
        return benchmark.get_compile_cmd(ht)

    def get_run_cmd(self, benchmark):
        ht = self.get_ht(benchmark)
        if self.if_hpc_servers():
            cmd_run = "~/projects/hpcl/tools/run_benchmark/fake_qsub.py job.qsub"
        else:
            cmd_run = "qsub -q hpcl.q job.qsub"
        return benchmark.get_run_cmd(ht, cmd_run)

    def create_scripts(self, benchmark):
        return

    def create_sge_script(self, task):
        ht = self.get_ht(task.instance.benchmark)
        ht['path'] = task.dir_name[:-1]
        ht['nname'] = task.instance.get_canonical_name()

        qsub = """#!/bin/bash
#
#$ -N T%(nname)s
#$ -cwd
#$ -S /bin/bash
#$ -j y
#$ -pe smp 8
#$ -q hpcl.q

source ~/.bashrc

cd $GEMS/ruby/

./amd64-linux/generated/%(ParamProtocol)s/bin/tester.exec -f %(path)s/tester.config -p %(ParamCores)d -a 1 -z $GEMS/ruby/trace_files/%(ParamCores)d_processors/%(trace)s > %(path)s/results
""" % ht
# -s 1
        with open(task.dir_name + 'job.qsub', 'w') as f:
            f.write(qsub)


    def create_tester_config(self, task):
        ht = self.get_ht(task.instance.benchmark)
        # Set the memory at 512 MB per core
        ht['ParamMemorySizeBytes'] = ht['ParamCores'] * 512 * 1024 * 1024
        ht['path'] = task.dir_name[:-1]
        ht['home'] = os.getenv('HOME')

        data = """
g_SIMICS: false
DATA_BLOCK: true
RANDOMIZATION: false
g_SYNTHETIC_DRIVER: false
g_DETERMINISTIC_DRIVER: false
g_DEADLOCK_THRESHOLD: 500000
//g_SpecifiedGenerator: DetermSeriesGETSGenerator
//g_SpecifiedGenerator: DetermGETXGenerator
//g_SpecifiedGenerator: DetermInvGenerator

PROTOCOL_DEBUG_TRACE: true

g_CACHE_DESIGN: %(ParamNetworkFile)s-%(ParamNetworkBW)d

L1_CACHE_ASSOC: 4
L1_CACHE_NUM_SETS_BITS: 8
L2_CACHE_ASSOC: 4
L2_CACHE_NUM_SETS_BITS: %(ParamL2SetBits)d
RAC_CACHE_ASSOC: 4
RAC_CACHE_NUM_SETS_BITS: %(ParamRACSetBits)d
g_endpoint_bandwidth: %(ParamNetworkBW)d

g_MEMORY_SIZE_BYTES: %(ParamMemorySizeBytes)d

DIRECTORY_CACHE_LATENCY: 6

SV_THRESHOLD: %(ParamSVThreshold)d
SV_Cnt: 16
DELAYEDINTER_LATENCY: %(ParamDelayInterventionLatency)d

BA_THRESHOLD: %(ParamBAThreshold)d
LATENCY_THRESHOLD: %(ParamLatencyThreshold)d

g_ISUPDATE: true
g_ISSELFINV: true
g_ISPROFILE: false
STREAM_ADDER: 1
g_ISCNTCONSET: true
g_ISADDSV: false
g_CONTRISI: false
g_CONTRILEN: 2

// XACT MEMORY
XACT_LENGTH: 2000
XACT_SIZE:   1000
ABORT_RETRY_TIME: 400
XACT_ISOLATION_CHECK: true

L2CACHE_TRANSITIONS_PER_RUBY_CYCLE: 1000
DIRECTORY_TRANSITIONS_PER_RUBY_CYCLE: 1000
RECYCLE_LATENCY: 1
L2CACHE_TRANSITIONS_PER_RUBY_CYCLE: 1000
DIRECTORY_TRANSITIONS_PER_RUBY_CYCLE: 1000
"""
        filename = task.dir_name + 'tester.config'
        open(filename, 'w').write(data % ht)

    def check_result(self, bench, folder, result):
        ht = {}
        path = folder + result + '/'

        data = self.get_result_data(folder, result, '0004_run.log')
        jobid = int(data.split(' ')[2])
        jobname = data.split('"')[1]

        running = util.get_running_jobs()
        if jobid in running:
            raise Exception('Still running ' + path)

        ht['stdout'] = self.get_result_data(folder, result, jobname + '.o' + str(jobid)).split('\n')
        l = self.has_line_starting_with(ht['stdout'], 'Fatal Error:')
        if l:
            raise Exception('Fatal Error:' + path + ' - ' + l)
        l = self.has_line(ht['stdout'], 'Killed')
        if l:
            raise Exception('Killed, might be a memory issue!' + path + ' - ' + l)

        ht['stats'] = self.get_result_data(folder, result, 'results').split('\n')
        result_ht = bench.check_result( self, folder, result, ht )

        if result_ht == None:
            result_ht = {}
        result_ht['cycles'] = self.extract_result(ht['stats'], 'Ruby_cycles: ')
        result_ht['hours'] = self.extract_result_f(ht['stats'], 'Elapsed_time_in_hours:')
        result_ht['coherence_misses'] = self.calc_coherence_misses(ht['stats'])

        return result_ht

    def has_line_starting_with(self, lines, data):
        for l in lines:
            if l.startswith(data):
                return l
        return None

    def has_line(self, lines, data):
        for l in lines:
            if data in l:
                return l
        return None

    def calc_coherence_misses(self, lines):
        results = 0
        for line in lines:
            if line.startswith('Fwd'):
                a = line.strip()
                b = a.split(' ')
                results = results + int(b[2])
        return results

    def extract_result_f(self, lines, name):
        for line in lines:
            if line.startswith(name):
                x = line[len(name):]
                return float(x)
        return None

    def extract_result(self, lines, name):
        for line in lines:
            if line.startswith(name):
                x = line[len(name):]
                return int(x)
        return None
