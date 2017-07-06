from benchmarks.npb_hw import *

from platforms.gem5_chapel import *
import instance
import os
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
    else:
        class ConfigGEM5:
            source_dir = my_home + '/projects/hardware/simulator/gem5/'
            build_dir = my_home + '/projects/hardware/simulator/build_gem5/'
            opt_level = 'opt'

def generate_instances(check_platform=False):
    print("Generating instances...")
    instances = []

    core_list = [1, 2, 4, 8, 16, 32, 64]
    kernels = ['ep']

    instances.extend(
        instance.get_instance_list(
            BenchmarkNPB_HW(minClass='A', maxClass='A', kernels=kernels),
            PlatformGem5Chapel(param_cores=core_list, cpu_type=['atomic']),
            check_platform
            )
        )

    print(len(instances), " instances available.")
    print("")

    return instances

