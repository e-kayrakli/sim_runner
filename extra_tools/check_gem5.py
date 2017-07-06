#!/usr/bin/env python3

import os
import subprocess
import sys
import time

def main():
    data = run_cmd('ps ax').split('\n')
    data = list(filter(lambda x: x.find('build_gem5') != -1, data))

    for l in data:
        l = l.split()
        pid = l[0]
        t = int(l[3].split(':')[0])
        if t<600:
            continue

        print(l[:4])
        folder = run_cmd('pwdx ' + pid)
        folder = folder.split(' ')[1]
        term = folder + '/system.terminal'
        output = open(term, 'r').read().split('\n')
        if list_has_str(output, 'Fixing recursive fault but reboot is needed!'):
            print('\n'.join(output[-5:]))
            print('Killed')
            run_cmd('kill '+ pid)
            continue

        if list_has_str(output, '[<fffffc00003111e8>] kernel_thread+0x28/0x90'):
            print('\n'.join(output[-10:]))
            print('Killed')
            run_cmd('kill '+ pid)
            continue

        print('\n'.join(output[-10:]))

def list_has_str(lst, s):
    for l in lst:
        if l.find(s) != -1:
            return True
    return False

def run_cmd(cmd):
    (status, data) = subprocess.getstatusoutput(cmd)
    return data

if __name__ == "__main__":
    main()


