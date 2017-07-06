#!/usr/bin/env python3

import sys
from util import *

def main():
    pbs_filename = sys.argv[-1]
    jobid = "12345"

    script = open(pbs_filename, 'r').read().split('\n')
    for l in script:
        if l.startswith("#$ -N "):
            job_name = l[6:]

    stdout = job_name + '.o' + jobid
    stderr = job_name + '.po' + jobid


    run_cmd('bash ' + pbs_filename + ' > ' + stdout + ' 2> ' + stderr + ' &')
    print('Your job ' + jobid + ' ("'+job_name+'") has been submitted by fake_qsub.py')

if __name__ == "__main__":
    main()

