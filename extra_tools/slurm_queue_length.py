#!/usr/bin/env python3

import subprocess
import datetime
from jobschedulers.slurm_time import SlurmTime

def main():
    cmd = 'squeue -h -u $USER --sort=-t,-p -l -o "%L %D"'
    (status, data) = subprocess.getstatusoutput(cmd)

    total_seconds = 0
    for i in data.split('\n'):
        (slurm_time, cores) = i.split(' ')
        st = SlurmTime(slurm_time)
        cpu_seconds = st.getSeconds() * int(cores)
        total_seconds += (cpu_seconds - 15 * 60) / 1.05

    td = datetime.timedelta(total_seconds / 60. / 60 / 24)
    print('Total simulation time : ' + str(td))

    nb_available_cores = 96
    td = datetime.timedelta(total_seconds / 60. / 60 / 24 / nb_available_cores)
    print('Remaining time : ' + str(td))

if __name__ == "__main__":
    main()
