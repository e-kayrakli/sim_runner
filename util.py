#!/usr/bin/env python3

import datetime
import os
import shutil
import subprocess
import sys
import zlib
from collections import namedtuple

def chdir_wrap(dir_name, no_run=False):
    if not no_run:
        os.chdir(dir_name)

def run_cmd_and_log(dir_name, name, command, log_path=None):
    if not log_path:
        log_path = dir_name

    chdir_wrap(dir_name)
    file_append(log_path + 'log', name + '\n')
    file_append(log_path + 'log', command + '\n')
    ret_val = run_cmd(command + " &> " + log_path + name + '.log')
    file_append(log_path + 'log', 'Exit code: ' + str(ret_val) + '\n\n')
    return ret_val

def recursively_remove_dir(dir_name):
    if os.path.isdir(dir_name):
        shutil.rmtree(dir_name)

def get_dir_list(dir_name):
    try:
        lst = os.listdir(dir_name)
    except:
        return []
    lst = [elem for elem in lst if elem != ".svn" and elem != "c_version"]
    return lst

def create_unique_folder(basename):
    count = 1
    while True:
        name = get_unique_dir_name(basename)
        count = count + 1
        if count > 25:
            raise NameError('Unable to create a directory ' + name)
        no_error = True
        try:
            os.makedirs(name)
        except os.error as e:
            no_error = False
            if e.errno != errno.EEXIST:
                raise
        if no_error:
            break
    return name

def file_append(filename, data):
    with open(filename, 'a') as f:
        f.write(data)

def get_unique_dir_name(basename):
    i = 1
    if not os.path.isdir(basename):
        return basename

    while os.path.isdir(basename + "_" + str(i)):
        i = i + 1

    return basename + "_" + str(i)

def get_unique_file_name(basename):
    i = 1
    if not os.path.isfile(basename):
        return basename

    while os.path.isfile(basename + "_" + str(i)):
        i = i + 1

    return basename + "_" + str(i)

def run_cmd(cmd_line, no_run = False, print_cmd = True):
    fullcommand = "bash -c \"" +  cmd_line + "\""
    if print_cmd:
        print(fullcommand)
    if not no_run:
        return os.system(fullcommand)
    return None

def get_nb_cpus():
    nb = subprocess.getoutput('cat /proc/cpuinfo | grep processor | wc -l')
    # TODO: Some error checking here
    return int(nb)

def get_arch():
    return subprocess.getoutput('uname -m')

def remove_suffix(var, suffix):
    if var.endswith(suffix):
        var = var[:-len(suffix)]
    return var

def get_hostname():
    hostname = os.uname()[1]
    return remove_suffix(hostname, '.localdomain')

def get_svn_revision(path='.'):
    (status, cur_svn_rev) = subprocess.getstatusoutput('svnversion ' + path)
    if status == 0:
        return cur_svn_rev
    else:
        return "unknow"

def get_monitor_pid():
    (status, data) = subprocess.getstatusoutput('ps ax | grep tile-monitor | grep -v grep')
    if data.strip(' ').split(' ')[0]:
        return int(data.strip(' ').split(' ')[0])
    else:
        return 0

def compute_file_crc32(filename, noCreationDate=True):
    try:
        file = open(filename, 'rb')
    except:
        return None

    data = file.read()
    if noCreationDate:
        lst = data.split(b'\n')
        lst = [e for e in lst if e.find(b'CreationDate') == -1]
        data = b'\n'.join(lst)

    crc32 = zlib.crc32(data)

    file.close()
    return "%08x" % (crc32)

def pad_align(s, align=20, extra=3):
    l = len(s)
    p = align - l % align + extra
    pad = ' ' * p
    return s + pad

def format_table(table, sep=' | ', file=sys.stdout):
    nb_cols = len(table[0])
    col_sizes = [0] * nb_cols
    for line in table:
        for i in range(0, nb_cols):
            cs = col_sizes[i]
            ds = len(line[i])

            if ds > cs:
                col_sizes[i] = ds

    for line in table:
        for i in range(0, nb_cols - 1):
            ds = len(line[i])
            print(line[i], end='', file=file)
            print(' ' * (col_sizes[i] - ds), end='', file=file)
            print(sep, end='', file=file)
        print(line[nb_cols - 1], file=file)

_ntuple_diskusage = namedtuple('usage', 'total used free')

def disk_usage(path):
    """Return disk usage statistics about the given path.

    Returned valus is a named tuple with attributes 'total', 'used' and
    'free', which are the amount of total, used and free space, in bytes.
    """
    st = os.statvfs(path)
    free = st.f_bavail * st.f_frsize
    total = st.f_blocks * st.f_frsize
    used = (st.f_blocks - st.f_bfree) * st.f_frsize
    return _ntuple_diskusage(total, used, free)

def test():
    print("Nb CPUs :        ", get_nb_cpus())
    print("Arch :           ", get_arch())
    print("Hostname :       ", get_hostname())
    print("SVN revision :   ", get_svn_revision())
    print("CRC32('util.py'):", compute_file_crc32('util.py'))
    print("CRC32('whateve'):", compute_file_crc32('whateve'))
    print(disk_usage('/'))

def get_log_time():
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d_%H:%M:%S')
    return now_str

if __name__ == "__main__":
    test()

