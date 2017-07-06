#!/usr/bin/env python3

import configuration

import instance
import util

import argparse
import cProfile
import datetime
import math_tools
import os
import os.path
import pstats
import util
import sys

from jobschedulers.jobscheduler_all import *
from jobschedulers.job import Job

from gnuplot_lib import *
from grapher import *

job_scheduler = get_current_scheduler()

def parse_arguments():
    parser = argparse.ArgumentParser(description='Load GEM5 results')

    parser.add_argument('-g', '--graphs', action='store_true', help='Generate graphs')
    parser.add_argument('-m', '--missings', action='store_true', help='Only display instances with no results')

    res = parser.parse_args()
    return res


def reduce_sum_all(key, instances):
    sum = 0
    for i in instances:
        for l in i.results_ht:
            v = l.get(key, 0)
            if v:
                sum += v
    return sum

def get_cpu_time(instances):
    sum = 0
    for i in instances:
        for l in i.results_ht:
            v = l.get('total_time', 0)
            if v:
                sum += v * get_nb_cores(i)
    return sum

def get_nb_cores(instance):
    if instance.platform.get_name() == 'Berkeley':
        return instance.platform.vector[1]
    else:
        return instance.platform.vector[0]

def print_table(instances, key, max_nb_results=None, function=lambda x: x, unit='', sort_key_fct=None):
    print('')
    print('Table for ', key)
    table = [['-- Instance name --', '-- Nbr --', '-- Median --', '-- Results --', '-- Stddev --', '-']]

    missing = 0

    if sort_key_fct:
        instances = sorted(instances, key=sort_key_fct)

    for i in instances:
        line = []

        results = [function(x[key]) for x in i.results_ht if key in x]
        results = [x for x in results if x != None]

        if max_nb_results:
            if len(results) >= max_nb_results:
                continue

        if max_nb_results:
            missing += max((max_nb_results - len(results)), 0)
        else:
            missing += max((3 - len(results)), 0)

        line.append(str(i))
        line.append(str(len(results)))
        if len(i.results_ht) > 0 and i.get_median(key) != None:
            line.append('{:>8}'.format('% 02.2f' % round(math_tools.list_median(results), 2)))
            line.append(str([round(x , 3) for x in results]))
            line.append('{:>10}'.format('% 02.2f' % round(math_tools.list_stddev(results), 2)))
        else:
            line.append('')
            line.append('')
            line.append('')
        line.append(unit)
        table.append(line)

    util.format_table(table)
    print('Nb lines', len(table) - 1)
    print('Missing results ', missing)

instances_ht = {}
def init_instance_ht(instances):
    for i in instances:
        instances_ht[str(i)] = i

def find_instance_str(instances, s):
    return instances_ht.get(s, None)

total_time_ht = {}

def clean_results(instances):
    to_remove = []

    for i in instances:
        o1 = find_instance_str(instances, str(i).replace('O0', 'O1'))
        if o1 == None:
            to_remove.append(i)
            continue

        t1 = i.get_median('total_time')
        t2 = o1.get_median('total_time')

        if t1 == None or t2 == None:
            to_remove.append(o1)
            to_remove.append(i)
            continue

        if t2 > t1:
            to_remove.append(o1)
            to_remove.append(i)

    for i in to_remove:
        print(' ->', i)
        nb_cores = i.platform.vector[1]
        s1 = ', ' + str(nb_cores) + ','
        for v in range(10):
            nb_cores *= 2
            s2 = ', ' + str(nb_cores) + ','

            o1 = find_instance_str(instances, str(i).replace(s1, s2))
            if o1:
                print('xxx' , o1)
                to_remove.append(o1)

    for i in to_remove:
        if i in instances:
            instances.remove(i)

    return instances

def main():
    args = parse_arguments()

    check_plat = True
    if util.get_hostname() == 'server1':
        check_plat = False

    instances = configuration.generate_instances(check_platform=check_plat)

    for i in instances:
        print(i)

    if len(instances)==0:
        print("No instances available")
        return

    instance.instances_load_results(instances)
    instance.instances_check_results(instances)

    print_table(instances, 'total_time')
    print_table(instances, 'checksum')

    init_instance_ht(instances)
    instances = clean_results(instances)

    td = datetime.timedelta(reduce_sum_all('total_time', instances) / 60 / 60 / 24)
    print('Total simulation time : ' + str(td))

    if not args.graphs:
        return False

    bench = 'mm'
    for size in [512, 1024]:
        try:
            do_graph_mm(instances, 'total_time', bench, size)
        except Exception as e:
            print(e)
            print('Unable to create graph:', bench, size)


def get_grapher_mm(bench, size):
    grapher = Grapher()
    grapher.title = bench.upper() + ' - Size ' + str(size)
    grapher.gnuplot.terminal = GNUPlotTerminalEPS()
    grapher.gnuplot.terminal.terminal = 'postscript enhanced eps color lw 2 "Helvetica" 16 size 10,7'
    grapher.derive_x_function = lambda i: i.platform.vector[1]
    grapher.derive_curve_function = lambda i: '-'.join([str(x) for x in i.benchmark.vector[1:]])
    grapher.derive_extra_function = lambda i: ''
    grapher.gnuplot.removeTemporaryFiles = False
    grapher.curves_name = {
            'Model-HW': 'Model-HW',
            'O0': 'No Manual Opts',
            'O1': 'Manual Privatization',
            'O1static-no': 'Manual Privatization, static',
            'O3-no': 'Privatized+Prefetching',
            'O3static-no': 'Privatized+Prefetching, static'
            }
    return grapher

def do_graph_mm(instances, metric, bench, size, extra_data=None, auto_axis=True):
    def get_select(benchname, size):
        def select(instance):
            if instance.benchmark.vector[0] != size:
                return False
            return True
        return select

    grapher = get_grapher_mm(bench, size)
    grapher.selection_function = get_select(bench, size)
    grapher.name = 'time_' + metric + '_' + bench.lower() + str(size)

    def compute_v(ht, c, x):
        v1 = ht.get(str(c) + '_' + str(x) + '_')
        return v1

    grapher.gnuplot.ylabel = 'Time (s)'
    grapher.compute_value = compute_v
    grapher.gnuplot.key = 'default'
    grapher.do_graph(instances, label=metric, reduce_fct=lambda i, k: i.get_median(k), extra_data=extra_data)

    grapher = get_grapher_mm(bench, size)
    grapher.name = 'speedup_' + metric + '_' + bench.lower() + str(size)
    grapher.selection_function = get_select(bench, size)
    grapher.gnuplot.ylabel = 'Performance Normalized to Code Without Manual Optimizations'
    grapher.graph_function = graph
    def compute_v(ht, c, x):
        c2 = 'MO_SOFT1'
        v1 = ht.get(c2 + '_' + str(x) + '_')
        v2 = ht.get(c + '_' + str(x) + '_')
        if not v1 or not v2:
            return None
        return v1/v2

    grapher.compute_value = compute_v

    grapher.do_graph(instances, label=metric, reduce_fct=lambda i, k: i.get_median(k), extra_data=extra_data)

if __name__ == "__main__":
    is_profiling = False
    if not is_profiling:
        main()
    else:
        cProfile.run('main()', 'load_results.profile')
        p = pstats.Stats('load_results.profile')
        p.print_stats()
        p.sort_stats('cumtime').print_stats(15)
        p.sort_stats('tottime').print_stats(15)

