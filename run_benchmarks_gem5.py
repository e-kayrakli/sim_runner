#!/usr/bin/env python3

import instance
import configuration_gem5
from run_benchmarks import run_benchmarks
import argparse
import os
import sys
import util
import shutil
from jobschedulers.jobscheduler_all import *

job_scheduler = get_current_scheduler()
if util.get_hostname() == 'login':
    job_scheduler.max_cores = 24
compiled_benchmarks = set()

def parse_arguments():
    parser = argparse.ArgumentParser(description='Load GEM5 results')

    parser.add_argument('-b', '--build-gem5', action='store_true', help='Build gem5')
    parser.add_argument('-c', '--clean-disk-image', action='store_true', help='Clean the disk image (rebuild benchmarks)')
    parser.add_argument('-r', '--resubmit-all', action='store_true', help='Resubmit even running jobs')
    parser.add_argument('-m', '--max-results', default=1, help='Number of results needed per instance', type=int)

    res = parser.parse_args()
    return res

def main():
    args = parse_arguments()
    gem5_environment_check()

    max_results = args.max_results

    if args.build_gem5:
        build_gem5()

    if args.clean_disk_image:
        clean_disk_image()

    instances = configuration_gem5.generate_instances(check_platform=True)
    instance.instances_load_results(instances)
    instance.instances_check_results(instances)
    instances = select_instances(instances, max_result=max_results)

    prepare_disk_image(instances)
    print('')

    skip = not args.resubmit_all
    run_benchmarks(instances, do_compilation=False, max_result=max_results, skip_running=skip)

    print('Flushing jobscheduler')
    job_scheduler.flush_all()

    print("Done.")


def compile_benchmark(inst):
    exe_name = inst.get_complete_exe_name()

    if exe_name in compiled_benchmarks:
        return False
    print(configuration_gem5.build_folder + exe_name)
    if os.path.exists(configuration_gem5.build_folder + os.path.basename(exe_name)):
        return False

    print(' * Compiling benchmarks', str(inst), exe_name)
    if os.path.exists(configuration_gem5.cache_build_folder + os.path.basename(exe_name)):
        p1 = configuration_gem5.cache_build_folder + os.path.basename(exe_name)
        p2 = configuration_gem5.build_folder + os.path.basename(exe_name)
        print('     * Using cache', exe_name)
        shutil.copy(p1, p2)
        return True

    task = inst.create_new_task(True)
    task.compile_to_dir(configuration_gem5.build_folder, remote_host='null0')

    compiled_benchmarks.add(exe_name)

    return True

def clean_disk_image():
    print(' * Cleaning old image')
    util.recursively_remove_dir(configuration_gem5.build_folder)
    os.mkdir(configuration_gem5.build_folder)

def update_gem5_disk_image():
    print(' * Updating GEM5 disk image')

    image_path = configuration_gem5.disk_image_path
    image_folder = configuration_gem5.disk_image_mount_folder
    build_folder = configuration_gem5.build_folder

    cmd = 'mount | grep %(image_folder)s' % locals()
    if util.run_cmd(cmd) == 0:
        raise Exception('Gem5 image already mounted')

    if not os.path.isdir(image_folder):
        os.makedirs(image_folder)

    cmd = 'sudo mount -o loop,offset=32256 %(image_path)s %(image_folder)s' % locals()
    if util.run_cmd(cmd) != 0:
        raise Exception('Unable to mount image')

    cmd = 'sudo cp -r %(build_folder)s %(image_folder)s' % locals()
    if util.run_cmd(cmd) != 0:
        raise Exception('Unable to copy build folder')

    if util.run_cmd('sudo umount %(image_folder)s' % locals()) != 0:
        raise Exception('Unable to umount image')

    os.rmdir(image_folder)

def prepare_disk_image(instances):
    print('Preparing new disk image')

    compiled = False

    for inst in instances:
        try:
            if compile_benchmark(inst):
                compiled = True
        except:
            print('Failure to compile: ', inst)
            sys.exit(1)

    if compiled:
        update_gem5_disk_image()

def build_gem5_scons(source_dir, build_dir, bin, opt_level, targets):
    print('    building: ' + ' '.join(targets))
    os.chdir(source_dir)
    cmd = 'scons -j 7 ' + bin
    if util.run_cmd(cmd) != 0:
        raise Exception('Unable to build atomic ' + cmd)

    for target in targets:
        cmd = 'cp ' + bin + ' ' + build_dir + 'gem5.' + opt_level + '.' + target
        if util.run_cmd(cmd) != 0:
            raise Exception('Copy failure ' + cmd)

def set_hw_rei_control(source_dir, is_control=True):
    with open(source_dir + '/src/arch/alpha/isa/decoder.isa', 'r') as f:
        decoder = f.read().split('\n')

    for i in range(len(decoder)):
        if decoder[i].find('hwrei') != -1:
            if is_control:
                l = '          1: hw_rei({{ xc->hwrei(); }}, IsSerializing, IsSerializeBefore, IsControl);'
            else:
                l = '          1: hw_rei({{ xc->hwrei(); }}, IsSerializing, IsSerializeBefore);'
            decoder[i] = l

    with open(source_dir + '/src/arch/alpha/isa/decoder.isa', 'w') as f:
        f.write('\n'.join(decoder))

def build_gem5():
    build_dir = configuration_gem5.ConfigGEM5.build_dir
    opt_level = configuration_gem5.ConfigGEM5.opt_level
    source_dir = configuration_gem5.ConfigGEM5.source_dir

    bin = 'build/ALPHA/gem5.' + opt_level

    print('* Building GEM5')
    util.recursively_remove_dir(build_dir)
    os.mkdir(build_dir)

    set_hw_rei_control(source_dir, False)
    build_gem5_scons(source_dir, build_dir, bin, opt_level, ['atomic', 'timing', 'detailed'])

    set_hw_rei_control(source_dir, True)
    build_gem5_scons(source_dir, build_dir, bin, opt_level, ['inorder'])

    set_hw_rei_control(source_dir, False)

def gem5_environment_check():
    if not os.getenv('M5_PATH'):
        print('GEM5 Environment error')
        sys.exit(1)

def select_instances(instances, max_result=1):
    return [i for i in instances if len(i.results_ht) < max_result]

if __name__ == "__main__":
    main()

