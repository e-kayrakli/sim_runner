import errno
import os
import shutil
import time
import util
from terminalcontroller import *
from user_parameters import *

class Task(object):
    instance = None
    dir_name = None

    def __init__(self, inst, is_compilation=False):
        print("New task for ", inst)
        self.instance = inst
        self.dir_name = self.create_folder(is_compilation)

    def create_folder(self, is_compilation):
        base = self.instance.result_folder + 'compile/'
        if is_compilation:
            base = self.instance.result_folder + 'compile/'
        else:
            base = self.instance.result_folder
        base_name = base + \
                self.instance.get_folder_base_name() + \
                time.strftime("%Y-%m-%d_%H:%M.%S", time.localtime())
        return util.create_unique_folder(base_name) + '/'

    def run_cmd(self, name, command, path=None, log_path=None):
        if not path:
            path = self.dir_name
        ret_val = util.run_cmd_and_log(path, name, command, log_path)

        term = TerminalController()
        if ret_val == 0:
            print(command, term.GREEN, ' = ', str(ret_val),  term.NORMAL)
        else:
            print(term.RED, command, ' = ', str(ret_val),  term.NORMAL)

        return ret_val

    def compile_to_dir(self, dest_dir, remote_host=None):
        os.chdir(self.dir_name)
        self.create_info_files()

        self.run_cmd('0000_make_clean', 'make clean', self.instance.get_path(), log_path=self.dir_name)

        compile_cmd = self.instance.get_compile_cmd()
        if remote_host:
            script_name = '/home/oserres/remote_compile_script.sh'
            with open(script_name, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("\n")
                f.write("cd projects/hardware/simulator\n")
                f.write("source set_env_chapel_1.11.0.sh\n")
                f.write("cd " + self.instance.get_path() +'\n')
                f.write(compile_cmd + '\n')
                f.write('sync\n')
            compile_cmd = 'ssh ' + remote_host + ' ' + script_name
            ret_val = self.run_cmd('0001a_chmod', 'chmod a+x ' + script_name, self.instance.get_path(), log_path=self.dir_name)
            if ret_val != 0:
                print("Task preparation for ", str(self), " FAILED")
                raise Exception('Task preparation FAILED')


        time.sleep(15)
        ret_val = self.run_cmd('0001_make', compile_cmd, self.instance.get_path(), log_path=self.dir_name)
        time.sleep(15)

        if ret_val != 0:
            print("Task preparation for ", str(self), " FAILED")
            raise Exception('Task preparation FAILED')

        exe_name = self.instance.get_exe_name()
        if exe_name:
            complete_exe_path = self.instance.get_complete_exe_name()
            exe_basename = os.path.basename(complete_exe_path)
            # FIXME is script_name correct here? Does it need to be exe_name
            # ret_val = self.run_cmd('0001a_chmod', 'chmod a+x ' + script_name, self.instance.get_path(), log_path=self.dir_name)
            print("move", exe_name, "->", dest_dir + exe_basename)
            shutil.move(exe_name, dest_dir + exe_basename)

        for f in self.instance.benchmark.needed_files:
            srcname = f
            dstname = dest_dir + f
            if os.path.isdir(srcname):
                print("copy_dir", srcname, "->", dstname)
                shutil.copytree(srcname, dstname)
            else:
                print("copy", srcname, "->", dstname)
                shutil.copy2(srcname, dstname)

    def prepare_run(self, do_compilation=True):
        if do_compilation:
            self.compile_to_dir(self.dir_name)

        os.chdir(self.dir_name)
        self.instance.platform.prepare_run(self.instance.benchmark, self)

        os.chdir(self.dir_name)
        self.instance.benchmark.create_config_files()
        self.instance.platform.create_scripts(self.instance.benchmark)

    def create_info_files(self):
        self.instance.benchmark.write_info_file(self.dir_name + 'benchmark.info')
        self.instance.platform.write_info_file(self.dir_name + 'platform.info')

    def query_autoparameters(self):
        with open(self.dir_name + 'auto', 'w') as f:
            for auto_par in self.instance.benchmark.auto_parameters:
                f.write(str(auto_par) + '\n')

    def run(self):
        self.query_autoparameters()
        self.instance.submit_job(self.dir_name)

    def precheck_result(self):
        self.instance.platform.precheck_result(
                self.instance.benchmark, self.dir_name)

    def clean(self):
        exe_name = self.instance.get_exe_name()
        shutil.remove(self.dir_name + exe_basename)

