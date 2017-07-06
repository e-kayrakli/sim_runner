from platforms.platform import *
import sys
import subprocess
import time

mpirun_path = '/opt/Tile64-2.1.0/src/tools/opera-mpi/mpi/mpirun'

class ParamBerkeleyOptimization(Parameter):
    default_value = 'O_disabled'

    def __init__(self, disable_optimization=False):
        self.valid_values = ['O_enabled']
        if disable_optimization:
            self.valid_values.append('O_disabled')

class ParamBerkeleyTranslatorOptimization(Parameter):
    default_value = 'opt_disabled'
    valid_values = ['opt_enabled', 'opt_disabled']

class PlatformBerkeleyTile(Platform):
    def __init__(self, disable_optimization=False, experimental=True, core_list=None):
        self.parameters = [
                ParamConduit(),
                ParamCores(max=48, list=core_list),
                ParamBerkeleyOptimization(disable_optimization)
        ]
        if experimental:
            self.parameters.append( ParamBerkeleyTranslatorOptimization() )
        super().__init__()

    def check_if_valid(self):
        return get_hostname() == 'tile.hpcl.gwu.edu'

    def get_compile_cmd(self, benchmark):
        ht = self.get_ht(benchmark)

        proc = ht["ParamCores"]
        max_memory = (2048 + 1024 + 512 + 256) / proc

        ht['ucc'] = "\\\"tile-cc -O3 \\\"" % locals()
        ht['upcc_nb_threads_opt'] = '-T'
        ht['platform'] = 'berkeley'

        opt = ''
        if ht['ParamBerkeleyOptimization'] == 'O_enabled':
            opt = '-O'

        opt_trans = ''
        if ht.get('ParamBerkeleyTranslatorOptimization') == 'opt_enabled':
            opt_trans = '-opt'

        if ht["ParamConduit"] == 'smp':
            ht["upcc"] = "\\\"upcc -v -network=smp -pthreads=%(proc)d -shared-heap=%(max_memory)d %(opt)s %(opt_trans)s \\\"" % locals()
        else:
            ht["upcc"] = "\\\"upcc -v -network=mpi -shared-heap=%(max_memory)d %(opt)s %(opt_trans)s \\\"" % locals()

        return benchmark.get_compile_cmd(ht)

    def get_run_cmd(self, benchmark):
        ht = self.get_ht(benchmark)
        if ht["ParamConduit"] == 'smp':
            cmd_run = """time tile-monitor --pci --batch-mode --verbose --env UPC_FORCETOUCH=YES --here --run -* ./%(exe_basename)s -*"""
        else:
            cmd_run = mpirun_path + " -np %(ParamCores)d %(exe_basename)s"
        return benchmark.get_run_cmd(ht, cmd_run)

    def precheck_result(self, bench, path):
        with open(path + '0004_run.log', 'r') as f:
            data = f.read()

        if data.find("""[monitor] ERROR: The file '/dev/tilepci0/lock' is currently locked!""") != -1:
            if get_monitor_pid() == 0:
                return 0
            else:
                while True:
                    time.sleep(15)
                    pid = get_monitor_pid()
                    if pid == 0:
                        return
                    else:
                        print("*** Killing monitor: %(pid)d" % locals() )
                        subprocess.getoutput(" kill -9 %(pid)d" % locals() )

        if data.find("""ERROR: The 'tilepci' driver is not listed in '/proc/devices'""") != -1:
            print('Tile: No driver')
            sys.exit(0)

    def check_result(self, bench, folder, result):
        ht = {}
        path = folder + result + '/'

        data = self.get_result_data(folder, result, '0004_run.log')

        if data.find("""[monitor] ERROR: The file '/dev/tilepci0/lock' is currently locked!""") != -1:
            raise Exception('Tile lock')

        if data.find("""Cannot upload""") != -1:
            raise Exception('Upload error')

        ht['stderr'] = ''
        ht['stdout'] = data

        try:
            result_ht = bench.check_result( self, folder, result, ht )
        except Exception as e:
            if ht['stderr'].find('Assertion') != -1:
                print('svn delete --force ' + path)
            raise e

        return result_ht

