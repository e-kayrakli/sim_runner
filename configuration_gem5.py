from benchmarks.matrix_multiplication import *
from benchmarks.vector_addition import *
from benchmarks.npb_hw import *
from benchmarks.upcbench_matrix_multiplication_hw import *
from benchmarks.upcbench_heat_multid_hw import *
from benchmarks.upcbench_sobel import *
#from benchmarks.chapel_hw import *
from benchmarks.chapel_hw import *

import instance
import os
from platforms.gem5_alpha_berkeley import *
from platforms.gem5_chapel import *
import util
my_home = os.getenv('HOME')

build_folder = my_home + '/projects/hardware/simulator/build_dir/'
cache_build_folder = my_home + '/projects/hardware/simulator/build_cache/'

if util.get_hostname() == 'cray':
    disk_image_path = my_home + '/work/linux-latest-automated.img'
else:
    disk_image_path = my_home + '/projects/hardware/simulator/gem5/disks/linux-latest-automated.img'
disk_image_mount_folder = my_home + '/mnt_disk_image/'

experimental_compiler = False

if experimental_compiler:
    class ConfigGEM5:
        source_dir = '/home/oserres/projects/hardware/simulator/new_gem5/gem5/'
        build_dir = my_home + '/projects/hardware/simulator/build_gem5_new/'
        opt_level = 'opt'
else:
    if util.get_hostname() == 'cray':
        class ConfigGEM5:
            source_dir = my_home + '/projects/hardware/simulator/gem5/'
            build_dir = my_home + '/work/build_gem5/'
            opt_level = 'opt'
    elif util.get_hostname() == 'login':
        class ConfigGEM5:
            source_dir = my_home + '/projects/hardware/simulator/gem5_phi/'
            build_dir = my_home + '/projects/hardware/simulator/build_gem5_phi/'
            opt_level = 'opt'
    else:
        class ConfigGEM5:
            source_dir = my_home + '/projects/hardware/simulator/gem5/'
            build_dir = my_home + '/projects/hardware/simulator/build_gem5/'
            opt_level = 'opt'

def generate_instances(check_platform=False):
    print("Generating instances...")
    instances = []

    npb_enabled = False
    mat_mult_enabled = False
    heat_benchmark = False
    sobel_benchmark = False

    chapel = True
    experimentals = experimental_compiler

    core_list = [1, 2, 4, 8, 16, 32, 64]
    #kernels = ['is']
    kernels = None

    home = os.getenv('HOME')

    if chapel:
        print('Chapel benchmarks')
        instances.extend(
            instance.get_instance_list(
                BenchmarkChapelHW(minClass='S', maxClass='A'),
                PlatformGem5Chapel(param_cores=core_list, cpu_type=['atomic', 'timing', 'detailed']),
                check_platform,
                result_dir = os.getenv('HOME') + '/projects/results_chapel/'
                )
            )
    else:
        print('Chapel benchmarks are disabled')

    if experimentals:
        core_list = [1, 2, 4, 8, 16]
        instances.extend(
            instance.get_instance_list(
                BenchmarkNPB_HW(minClass='W', maxClass='W', kernels=None),
                PlatformGem5AlphaBerkeley(param_cores=core_list, cpu_type=['atomic', 'timing']),
                check_platform,
                result_dir = os.getenv('HOME') + '/projects/results_exp/'
                )
            )
        return instances

    if npb_enabled:
        print('NPB is enabled')
        instances.extend(
            instance.get_instance_list(
                BenchmarkNPB_HW(minClass='W', maxClass='W', kernels=kernels),
                PlatformGem5AlphaBerkeley(param_cores=core_list, opt_list=['BO3'], cpu_type=['atomic']),
                check_platform
                )
            )
        instances.extend(
            instance.get_instance_list(
                BenchmarkNPB_HW(minClass='W', maxClass='W', kernels=kernels),
                PlatformGem5AlphaBerkeley(param_cores=core_list, cpu_type=None, opt_list=['BO1']),
                check_platform,
                result_dir = home + '/projects/results_paper_2015_05_08/'
                )
            )
    else:
        print('NPB disabled')

    if mat_mult_enabled:
        print('Matrix multiplication is enabled')
        instances.extend(
                instance.get_instance_list(
                    BenchmarkUBMatrixMultiplicationHW(size_list=[256, 512]),
                    PlatformGem5AlphaBerkeley(param_cores=core_list),
                    check_platform
                    )
                )
    else:
        print('Matrix multiplication disabled')

    if heat_benchmark:
        print('Heat is enabled')
        instances.extend(
                instance.get_instance_list(
                    BenchmarkUBHeatMultiDHW(size_list=[64]),
                    PlatformGem5AlphaBerkeley(param_cores=core_list),
                    check_platform
                    )
                )
    else:
        print('Heat disabled')

    if sobel_benchmark:
        print('Sobel is enabled')
        instances.extend(
                instance.get_instance_list(
                    BenchmarkUBSobelHW(),
                    PlatformGem5AlphaBerkeley(param_cores=core_list),
                    check_platform
                    )
                )
    else:
        print('Sobel disabled')

    print(len(instances), " instances available.")
    print("")

    return instances

