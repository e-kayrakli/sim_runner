from platforms.platform import *
from terminalcontroller import *

import util
import time
import string

term = TerminalController()

class ParamProtocol(Parameter):
    valid_values = ['MOESI_SMP_directory']
    #valid_values = ['MOESI_SMP_dir2']

class ParamL2SetBits(Parameter):
    valid_values = [13]

class ParamRACSetBits(Parameter):
    valid_values = [12]

class ParamDCSetBits(Parameter):
    valid_values = [11]

class ParamNetworkFile(Parameter):
    valid_values = ['NUCA1','NUCA2', 'NUCA3', 'NUCA4', 'NUCA5']

class ParamDelayInterventionLatency(Parameter):
    valid_values = [0, 50, 150, 300, 500, 1000, 5000, 20000, 60000]

class ParamSVThreshold(Parameter):
    valid_values = [0, 6]

class ParamBAThreshold(Parameter):
    valid_values = [0, 25, 50, 75, 100]
    default_value = 100

class ParamNetworkBW(Parameter):
    valid_values = [100, 200, 400, 600, 800, 1000]
    default_value = 1000

class ParamLatencyThreshold(Parameter):
    valid_values = [16, 261]
    default_value = 261

class PlatformSimics(Platform):
    parameters = [
            ParamCores(list=[16]),
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
        self.create_simics_script(task)
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

        if self.get_param_value(ParamProtocol) == 'MOESI_SMP_directory':
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

        return True

    def wait_nb_task(self, nb=0):
        if self.if_hpc_servers():
            self.wait_nb_task_ps(8)
        else:
            self.wait_nb_task_sge(nb)

    def wait_nb_task_ps(self, nb=0):
        first = True

        procs = subprocess.getoutput('ps aux | grep simics-common').split('\n')
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
            procs = subprocess.getoutput('ps aux | grep simics-common').split('\n')
            val = len(procs) -1
        if not first:
            print()

    def wait_nb_task_sge(self, nb=0):
        first = True

        val = len(util.get_running_jobs())
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
            val = len(util.get_running_jobs())
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
#$ -N %(nname)s
#$ -cwd
#$ -S /bin/bash
#$ -j y
""" % ht
        if ht['ParamCores'] == 16:
            qsub = qsub + """ 
#$ -pe smp 2
"""
        elif ht['ParamCores'] == 64:
            qsub = qsub + """ 
#$ -pe smp 8
"""

        qsub = qsub + """ 
#$ -q hpcl.q

source ~/.bashrc

cd $GEMS/simics/home/%(ParamProtocol)s

./simics -echo -verbose -no-log -stall -no-win -x %(path)s/simics.simics
""" % ht

        with open(task.dir_name + 'job.qsub', 'w') as f:
            f.write(qsub)


    def create_simics_script(self, task):
        ht = self.get_ht(task.instance.benchmark)
        # Set the memory at 512 MB per core
        ht['ParamMemorySizeBytes'] = ht['ParamCores'] * 512 * 1024 * 1024
        ht['path'] = task.dir_name[:-1]
        ht['home'] = os.getenv('HOME')
        ht['checkpoint_name'] = task.instance.benchmark.get_checkpointname(task.instance.platform)
        ht['cache_name'] = task.instance.benchmark.get_cachename(task.instance.platform)

        if ht['ParamCores'] == 16:
            data = """
    read-configuration %(home)s/opt/virtutech/simics-3.0.31/checkpoints/serengeti_2G/%(checkpoint_name)s.conf
    """
        elif ht['ParamCores'] == 64:
            data = """
    read-configuration %(home)s/opt/virtutech/simics-3.0.31/checkpoints/serengeti-64p/%(checkpoint_name)s.conf
    """
        data = data + """
ruby0.periodic-stats-file %(path)s/periodic.stats
@sys.path.append("../../../gen-scripts")
@import mfacet

istc-disable
dstc-disable
instruction-fetch-mode instruction-fetch-trace
magic-break-enable
break-hap "Core_Magic_Instruction"
cpu-switch-time 1

@mfacet.run_sim_command('load-module ruby')
ruby0.setparam g_NUM_PROCESSORS %(ParamCores)d
ruby0.setparam g_MEMORY_SIZE_BYTES %(ParamMemorySizeBytes)d
ruby0.setparam g_PROCS_PER_CHIP 1
ruby0.setparam g_NUM_L2_BANKS %(ParamCores)d
ruby0.setparam g_endpoint_bandwidth %(ParamNetworkBW)d

ruby0.setparam DIRECTORY_LATENCY 20
ruby0.setparam DIRECTORY_CACHE_LATENCY 6

ruby0.setparam_str g_PRINT_TOPOLOGY true
ruby0.setparam_str g_NETWORK_TOPOLOGY FILE_SPECIFIED 
ruby0.setparam_str g_CACHE_DESIGN %(ParamNetworkFile)s-%(ParamNetworkBW)d

ruby0.setparam L2_CACHE_NUM_SETS_BITS %(ParamL2SetBits)d
ruby0.setparam RAC_CACHE_NUM_SETS_BITS %(ParamRACSetBits)d
ruby0.setparam DC_CACHE_NUM_SETS_BITS %(ParamDCSetBits)d

ruby0.setparam STREAM_ADDER 1
ruby0.setparam g_CONTRILEN 1
ruby0.setparam DELAYEDINTER_LATENCY %(ParamDelayInterventionLatency)d
ruby0.setparam SV_THRESHOLD %(ParamSVThreshold)d
ruby0.setparam BA_THRESHOLD %(ParamBAThreshold)d
ruby0.setparam LATENCY_THRESHOLD %(ParamLatencyThreshold)d
ruby0.setparam SV_Cnt 16

ruby0.setparam_str g_ISSELFINV true
ruby0.setparam_str g_ISCNTCONSET true
ruby0.setparam_str g_ISADDSV false

@print "Running "
@mfacet.run_sim_command('ruby0.init')
@mfacet.run_sim_command('ruby0.load-caches %(home)s/opt/apokayi_gems/caches/%(cache_name)s')
@mfacet.run_sim_command('ruby0.clear-stats')

ruby0.periodic-stats-interval 50000000
ruby0.periodic-stats-file %(path)s/periodic.stats
"""
        debug = False
        if debug:
            data = data + """
ruby0.debug-verb high
ruby0.debug-filter lseagTSN
ruby0.debug-start-time 1
ruby0.debug-output-file   %(path)s/ruby.debug
"""

        #trace = False
        trace = True
        if trace:
            data = data + """
ruby0.tracer-output-file  %(path)s/trace.gz
"""
        data = data + """
@mfacet.run_sim_command('continue')
@mfacet.run_sim_command('ruby0.dump-stats %(path)s/ruby.stats')
exit
"""
        filename = task.dir_name + 'simics.simics'
        open(filename, 'w').write(data % ht)

    def check_result(self, bench, folder, result):
        ht = {}
        path = folder + result + '/'

        data = self.get_result_data(folder, result, '0004_run.log')
        jobid = None
        for l in data.split('\n'):
            if l.startswith('Your job'):
                jobid = int(l.split(' ')[2])
                jobname = l.split('"')[1]
        if jobid == None:
            #print ( path )
            #run_cmd('rm -rf ' + path)
            raise Exception('Error parsing 0004_run.log')

        running = util.get_running_jobs()
        if jobid in running:
            raise Exception('Still running ' + path)

        output_filename = folder + result + '/' + jobname + '.o' + str(jobid)
        per_filename = folder + result + '/' + 'periodic.stats'
        ruby_filename = folder + result + '/' + 'ruby.stats'
        if not os.path.exists(output_filename):
            #print ( path )
            #run_cmd('rm -rf ' + path)
            raise Exception('Was not run ' + path)
        else:
            if (os.path.exists(per_filename)) and (not os.path.exists(ruby_filename)):
                #print ( path )
                #run_cmd('rm -rf ' + path)
                raise Exception('RUN but killed/died before generating ruby.stats ' + path)

        if not os.path.exists(ruby_filename):
            print ( path )
            run_cmd('rm -rf ' + path)
            raise Exception('Where is ruby.stats ??? ' + path)

        ht['stdout'] = self.get_result_data(folder, result, jobname + '.o' + str(jobid)).split('\n')
        l = self.has_line_starting_with(ht['stdout'], 'Lookup file failed for ')
        if l:
            #run_cmd('rm -rf ' + path)
            raise Exception('Unable to open checkpoint ' + path + ' - ' + l)
        l = self.has_line_starting_with(ht['stdout'], 'Runtime Error at ')
        if l:
            raise Exception('Protocol error ' + path + ' - ' + l)
        l = self.has_line_starting_with(ht['stdout'], 'Error: Could not open network file:')
        if l:
            #run_cmd('rm -rf ' + path)
            raise Exception('Network problem ' + path + ' - ' + l)
        l = self.has_line_starting_with(ht['stdout'], 'The simulation state has been corrupted.')
        if l:
            #run_cmd('rm -rf ' + path)
            raise Exception('Sim corrupted ' + path + ' - ' + l)
        l = self.has_line_starting_with(ht['stdout'], "Error loading module 'ruby'")
        if l:
            #run_cmd('rm -rf ' + path)
            raise Exception('Ruby Load Error ' + path + ' - ' + l)
        l = self.has_line_starting_with(ht['stdout'], "FLEXlm error")
        if l:
            #run_cmd('rm -rf ' + path)
            raise Exception('Simics License ERROR ' + path + ' - ' + l)

        ht['stats'] = self.get_result_data(folder, result, 'ruby.stats').split('\n')

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
