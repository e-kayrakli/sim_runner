from platforms.platform import *
import sys
import subprocess
import time

class ParamCCOptimization(Parameter):
    valid_values = ['O0', 'O1', 'O2', 'O3']

class PlatformTileCC(Platform):
    def __init__(self):
        self.parameters = [
                ParamCores(max=1),
                ParamCCOptimization()
        ]
        super().__init__()

    def check_if_valid(self):
        return get_hostname() == 'tile.hpcl.gwu.edu'

    def get_compile_cmd(self, benchmark):
        ht = self.get_ht(benchmark)

        proc = ht["ParamCores"]
        max_memory = (4096 - 128) / proc
        ht['ucc'] = "tile-cc"
        ht['upcc_nb_threads_opt'] = ''
        ht['platform'] = 'berkeley'

        opt = ht["ParamCCOptimization"]

        ht["upcc"] = "\\\"tile-cc -lm -%(opt)s \\\"" % locals()

        return benchmark.get_compile_cmd(ht)

    def get_run_cmd(self, benchmark):
        ht = self.get_ht(benchmark)
        cmd_run = """time tile-monitor --pci --batch-mode --verbose --upload %(exe_basename)s hello --run -* ./hello -*"""
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
            print("rm -rf " + path)
            raise Exception('Tile lock')

        if data.find("""Cannot upload""") != -1:
            print("rm -rf " + path)
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
