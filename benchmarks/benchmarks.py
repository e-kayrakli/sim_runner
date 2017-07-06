from param_vector import *

class Benchmark(ParamVector):
    def check_validity(self, platform):
        return platform.check_vector_validity() and self.check_vector_validity(platform)

    def prepare_run(self):
        return

    def get_compile_cmd(self):
        raise NameError('Compile command not implemented')

    def get_run_cmd(self):
        raise NameError('Compile command not implemented')

    def get_ht(self):
        ht = self.get_ht_based_on_vector()
        ht['extra_parameters'] = 'param_file.txt'
        return ht

    def create_config_files(self):
        return

    def get_complete_exe_name(self, ht):
        return self.get_exe_name(ht)

    def fix_issues(self, bench, folder, result):
        print('Not implemented')

    def get_params(self):
        return ''
