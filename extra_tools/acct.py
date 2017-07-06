#!/usr/bin/env python3

from util import *
import subprocess

import datetime
import sys

def main():
    days = int(sys.argv[1])
    data = subprocess.getoutput('qacct -d %(days)d -o' % locals())
    data = data.split('\n')

    total = 0.

    for line in data[2:]:
        l = line.split()
        utime = float(l[2])
        stime = float(l[3])

        total_user = utime + stime
        total = total + total_user


    td = datetime.timedelta(hours=total/60/60)
    print('Cluster total:', str(td))
    print('Cluster cores:', str( total/days/24./60./60.))

    table = [['User', 'CPU/hours', 'Percentage', 'Cluster usage (cores)']]
    table.append( ['---'] * 4 )

    for line in data[2:]:
        l = line.split()
        utime = float(l[2])
        stime = float(l[3])

        total_user = utime + stime
        td = datetime.timedelta(hours=total_user/60/60)

        t = str(td)

        t = ' ' *(40 - len(t)) + t


        table.append( [ l[0], t, str(int(total_user * 100 / total)), str(int(total_user / days / 24. /60./60.)) ] )
    
    format_table(table)



if __name__ == "__main__":
    main()
