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
    parser.add_argument('-p', '--profile', action='store_true', help='Profile the execution')
    parser.add_argument('-t', '--process-traces', action='store_true', help='Show information about traces')

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

def print_table(instances, key, max_nb_results=None, function=lambda x: x, unit='', sort_key_fct=None, wanted_nb_results=1, file=sys.stdout):
    print('', file=file)
    print('Table for ', key, file=file)
    table = [['-- Instance name --', '-- Nbr --', '-- Median --', '-- Results --', '-- Stddev --', '-']]

    missing = 0
    missing_wanted = 0

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
            missing += max((wanted_nb_results - len(results)), 0)
        missing_wanted += max((1 - len(results)), 0)

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

    util.format_table(table, file=file)
    print('Nb lines', len(table) - 1, file=file)
    print('Missing results ', missing, ' -- ', missing_wanted, file=file)

def post_process_trace(i, r):
    path = i.get_folder_name() + r + '/'

    split = 0
    while os.path.isfile(path + 'trace_0.txt.gz_split_%03d.gz' % split):
        if not os.path.isfile(path + 'trace_0.txt.gz_split_%03d.gz_result.out' % split):
            print('Processing split ', split)

            job = Job()
            job.name = "QPost" + str(i) + 'split' + str(split)
            job.path = path
            job.output = 'trace_0.txt.gz_split_%03d.gz_result' % split
            job.jsfilename = 'job_accesses_stats_quick_%03d' % split
            job.jsout = '0101_accesses_stats_quick_%03d' % split

            trace = path + 'trace_0.txt.gz_split_%03d.gz' % split

            job.nb_cores = 8
            command = '/home/oserres/projects/hardware/trace_simulator/parse_trace.py ' + trace + ' --exclude_categories LCAUIG'
            job.cmd = command
            job_scheduler.submit_job(job)
            job_scheduler.flush_all()

        split = split + 1

    if split != 0:
        return

    if not os.path.isfile(path + 'accesses_stats_quick2.out'):
        print('Post-Processing: ' + path)
        job = Job()
        job.name = "Q2Post" + str(i)
        job.path = path
        job.output = 'accesses_stats_quick2'
        job.jsfilename = 'job_accesses_stats_quick2'
        job.jsout = '0101_accesses_stats_quick2'

        job.nb_cores = 8
        command = '/home/oserres/projects/hardware/trace_simulator/parse_trace.py ' + path + 'trace_0.txt.gz --exclude_categories LCAUIG'
        job.cmd = command
        job_scheduler.submit_job(job)
        job_scheduler.flush_all()
        #ret_val = util.run_cmd_and_log(path, 'accesses_stats', command)
    else:
        print('Skipped ', path)

def check_post_process_trace(i, r):
    path = i.get_folder_name() + r + '/'

    split = 0
    nb_ok = 0
    while os.path.isfile(path + 'trace_0.txt.gz_split_%03d.gz' % split):
        out_file_name = path + 'trace_0.txt.gz_split_%03d.gz_result.out' % split
        if os.path.isfile(out_file_name):
            print('  Checking split ', split)
            d = open(out_file_name, 'r').read()
            if d.find('Address incrementation P:') != -1:
                print('    Ok')
                nb_ok += 1
            else:
                print('    Failed ', path)
                os.remove(out_file_name)
                err_file_name = path + 'trace_0.txt.gz_split_%03d.gz_result.err' % split
                os.remove(err_file_name)
                job_file_name = path + 'job_accesses_stats_quick_%03d' % split
                os.remove(job_file_name)
                job_file_name = path + '0101_accesses_stats_quick_%03d.log' % split
                os.remove(job_file_name)

        split = split + 1

    if split == nb_ok:
        if not os.path.isfile(path + 'access_summary'):
            print('Should post process')
            cmd = '~/projects/hardware/trace_simulator/merge_trace_results.py *_result.out &>access_summary'
            os.chdir(path)
            ret_val = util.run_cmd(cmd)

    if split != 0:
        return

    out_file_name = path + 'accesses_stats_quick2.out'
    if os.path.isfile(out_file_name):
        print('  Checking Post-Processing: ' + path)

        d = open(out_file_name, 'r').read()
        if d.find('Address incrementation P:') != -1:
            print('    Ok')
        else:
            print('    Failed', path)
            os.remove(out_file_name)
            err_file_name = path + 'accesses_stats_quick2.err'
            os.remove(err_file_name)
            job_file_name = path + 'job_accesses_stats_quick2'
            os.remove(job_file_name)
            job_file_name = path + '0101_accesses_stats_quick2.log'
            os.remove(job_file_name)
    else:
        print('Error ', path)

def check_post_process_traces(instances):
    cnt = 0

    for i in instances:
        for l in i.results_ht:
            if l.get('nb_accesses', None) != None:
                continue
            print(l)
            r = l['result']
            path = i.get_folder_name() + r + '/'

            check_post_process_trace(i, r)

def post_process_traces(instances):
    cnt = 0

    for i in instances:
        for l in i.results_ht:
            if l['nb_accesses'] != None:
                continue
            print(l)
            r = l['result']
            path = i.get_folder_name() + r + '/'

            post_process_trace(i, r)


def transfer_key_from_trace(instances, key):
    for i in instances:
        i_s = str(i)
        if i_s.startswith('instance(BerkeleyTrace'):
            i_s2 = i_s.replace('BerkeleyTrace', 'Berkeley')
            for i2 in instances:
                if str(i2) == i_s2:
                    lst = [x[key] for x in i.results_ht if key in x]
                    if lst != []:
                        nb_accesses = max(lst)
                        for r in i2.results_ht:
                            r[key] = nb_accesses

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

def predict_time(instances, i,  tip_ns=2.2, tis_ns=2.4, ta_ns=1.3):
    tip = tip_ns / 1000. / 1000. / 1000.
    tis = tis_ns / 1000. / 1000. / 1000.
    ta = ta_ns / 1000. / 1000. / 1000.

    o1 = find_instance_str(instances, str(i).replace('O0', 'O1'))
    if not o1:
        return None

    t0 = total_time_ht.get(i, None)
    if t0 == None:
        t0 = i.get_median('total_time')
        total_time_ht[i] = t0

    t1 = total_time_ht.get(o1, None)
    if t1 == None:
        t1 = o1.get_median('total_time')
        total_time_ht[o1] = t1

    if t0 == None or t1 == None:
        return None

    if t0 < t1:
        return None

    nip0 = i.get_first('nb_incr_p')
    nip1 = o1.get_first('nb_incr_p')

    nis0 = i.get_first('nb_incr_s')
    nis1 = o1.get_first('nb_incr_s')

    na_0 = i.get_first('nb_accesses')
    na_1 = o1.get_first('nb_accesses')

    ba_0 = i.get_first('barriers_time') / 1000 / 1000/ 1000.
    ba_1 = o1.get_first('barriers_time') / 1000 / 1000/ 1000.

    #t_opt = t0 - ba_0 + ba_1 - (nip0 - nip1) * tip - (nis0 - nis1) * tis - (na_0 - na_1) * ta
    t_opt = t0 - abs(nip0 - nip1) * tip - abs(nis0 - nis1) * tis - abs(na_0 - na_1) * ta

    print(nip0-nip1, nis0 - nis1, na_0 - na_1)
    print(t0, t1, t_opt)

    if t_opt > t0:
        print('**************************************')
    print()

    return t_opt

def evaluate_opt(instances, instances_O0, tip_ns=2.4, tis_ns=2.7, ta_ns=1.5, display=False):
    tip = tip_ns / 1000. / 1000. / 1000.
    tis = tis_ns / 1000. / 1000. / 1000.
    ta = ta_ns / 1000. / 1000. / 1000.

    sum_abs_error = 0

    for i in instances_O0:
        o1 = find_instance_str(instances, str(i).replace('O0', 'O1'))
        if o1:
            try:
                t0 = total_time_ht.get(i, None)
                if t0 == None:
                    t0 = i.get_median('total_time')
                    total_time_ht[i] = t0

                t1 = total_time_ht.get(o1, None)
                if t1 == None:
                    t1 = o1.get_median('total_time')
                    total_time_ht[o1] = t1

                if t0 == None or t1 == None:
                    continue

                if t0 < t1:
                    continue

                nip0 = i.get_first('nb_incr_p')
                nip1 = o1.get_first('nb_incr_p')

                nis0 = i.get_first('nb_incr_s')
                nis1 = o1.get_first('nb_incr_s')

                na_0 = i.get_first('nb_accesses')
                na_1 = o1.get_first('nb_accesses')

                ba_0 = i.get_first('barriers_time') / 1000 / 1000/ 1000.
                ba_1 = o1.get_first('barriers_time') / 1000 / 1000/ 1000.

                tdiff = t0 - t1
                t_opt = t0 - ba_0  + ba_1 - (nip0 - nip1) * tip - (nis0 - nis1) * tis - (na_0 - na_1) * ta
                tdiff_opt = t0 - t_opt
                if t_opt < 0:
                    t_opt = 0
                abs_error = abs((t_opt - t1)/t1)
                sum_abs_error += abs_error
                if display:
                    print(i, 'tdiff=%03.2f' % tdiff, 'tdiff_opt=%03.2f' % (tdiff_opt), '    O1_speedup=%03.2f' % (t0/t1), '   t0=', t0,' t1=', t1, 't_opt=%3.2f' %(t_opt),'     => ', '%3.2f' % (abs_error * 100), '% off')
                    print('TAB', '"', i,'"' , ',', t0,',', t1, ',',t_opt)
            except:
                pass
                #print(i, 'Pass')

    #print('tip='+str(tip_ns), 'tis='+str(tis_ns), 'ta='+str(ta_ns), 'err=', sum_abs_error)
    return sum_abs_error

def main():
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
    print_table(instances, 'rate')

    sys.exit(1)

    #check_post_process_traces(instances)
    #post_process_traces(instances)

    transfer_key_from_trace(instances, 'nb_accesses')
    transfer_key_from_trace(instances, 'nb_incr_p')
    transfer_key_from_trace(instances, 'nb_incr_s')
    transfer_key_from_trace(instances, 'notifywait_time')
    transfer_key_from_trace(instances, 'barriers_time')

    #print_table(instances, 'idle_time')
    #print_table(instances, 'it_time')
    #print_table(instances, 'max_timing_comp')
    #print_table(instances, 'max_timing_comm')
    #print_table(instances, 'total_time')
    #print_table(instances, 'total_time', max_nb_results=1)
    #print_table(instances, 'nb_accesses')
    #print_table(instances, 'nb_accesses', max_nb_results=1)


    instances = [i for i in instances if not 'O3' in str(i)]
    instances = [i for i in instances if not 'O1static' in str(i)]
    instances = [i for i in instances if not str(i).startswith('instance(BerkeleyTrace')]
    print_table(instances, 'total_time')
    print_table(instances, 'checksum')

    if args.process_traces:
        print_table(instances, 'nb_accesses')
        print_table(instances, 'nb_incr_p', sort_key_fct=lambda a: a.benchmark['NPBTests'])
        print_table(instances, 'nb_incr_s')
        print_table(instances, 'barriers_time')
        print_table(instances, 'notifywait_time')

    sys.exit(1)
    init_instance_ht(instances)
    instances = clean_results(instances)

    for kernel in ['ft', 'is', 'mg', 'cg']:
        best_sum = 10000
        best = (None, None, None)
        instances_O0 = [i for i in instances if 'O0' in str(i) and kernel in str(i)]

        for tip in [2.2]:
            for tis in [2.6]:
                for ta in [1.1]:
                    sum = evaluate_opt(instances, instances_O0, tip, tis, ta)
                    if sum < best_sum:
                        best_sum = sum
                        best = (tip, tis, ta)
            print(kernel, tip, '/', 10, '   ', best, best_sum)

        tip, tis, ta = best
        print(kernel, tip, '/', 10, '   ', best, best_sum)
        sum = evaluate_opt(instances, instances_O0, tip, tis, ta, True)

    td = datetime.timedelta(reduce_sum_all('total_time', instances) / 60 / 60 / 24)
    print('Total simulation time : ' + str(td))

    if not args.graphs:
        return False

    for bench in ['is', 'ep', 'cg', 'mg', 'ft']:
        for npb_class in ['A', 'B']:
            instances_O0 = [i for i in instances if 'O0' in str(i) and bench in str(i)]
            instances_O0 = [i for i in instances_O0 if "'" + npb_class + "'" in str(i)]

            lst_extra = []

            for i in instances_O0:
                data = GraphData()
                data.name = 'Model-HW'
                data.x_val = i.platform.vector[1]
                data.y_val = predict_time(instances, i)
                data.extra = ''
                if data.y_val and data.y_val != 0.0:
                    lst_extra.append(data)

            try:
                do_graph(instances, 'total_time', bench, npb_class, extra_data=lst_extra)
            except Exception as e:
                print(e)
                print('Unable to create graph:', bench, npb_class)

            lst_extra = []

            for i in instances_O0:
                o1 = find_instance_str(instances, str(i).replace('O0', 'O1'))
                if not o1:
                    continue
                to1 = o1.get_median('total_time')
                data = GraphData()
                data.name = 'Model-HW'
                data.x_val = i.platform.vector[1]
                data.y_val = predict_time(instances, i)
                data.extra = ''
                if data.y_val and data.y_val != 0.0:
                    data.y_val = (data.y_val - to1)/to1
                    print('Error prediction', data.y_val)
                    lst_extra.append(data)

            try:
                if len(lst_extra) > 0:
                    do_graph_error(instances, 'total_time', bench, npb_class, extra_data=lst_extra)
            except Exception as e:
                print(e)
                print('Unable to create graph:', bench, npb_class)

    #td = datetime.timedelta(get_cpu_time(instances) / 60 / 60 / 24)
    #print('Total CPU time : ' + str(td))

def get_grapher(bench, npb_class):
    grapher = Grapher()
    grapher.title = bench.upper() + ' - Class ' + npb_class
    grapher.gnuplot.terminal = GNUPlotTerminalEPS()
    grapher.gnuplot.terminal.terminal = 'postscript enhanced eps color lw 2 "Helvetica" 16 size 10,7'
    grapher.derive_x_function = lambda i: i.platform.vector[1]
    grapher.derive_curve_function = lambda i: '-'.join([str(x) for x in i.benchmark.vector[2:]])
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

def do_graph_error(instances, metric, bench, npb_class, extra_data=None):
    def get_select(benchname, npb_class):
        def select(instance):
            return False
        return select
    grapher = Grapher()
    grapher.title = bench.upper() + ' - Class ' + npb_class
    grapher.gnuplot.terminal = GNUPlotTerminalEPS()
    grapher.gnuplot.terminal.terminal = 'postscript enhanced eps color lw 2 "Helvetica" 16 size 10,7'
    grapher.derive_x_function = lambda i: i.platform.vector[1]
    grapher.derive_curve_function = lambda i: '-'.join([str(x) for x in i.benchmark.vector[2:]])
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
    grapher.selection_function = get_select(bench, npb_class)
    grapher.name = 'error_' + metric + '_' + bench.lower() + npb_class
    def compute_v(ht, c, x):
        v1 = ht.get(str(c) + '_' + str(x) + '_')
        return v1
    grapher.gnuplot.ylabel = 'Error (%)'
    grapher.compute_value = compute_v
    grapher.gnuplot.key = 'default'
    grapher.do_graph(instances, label=metric, reduce_fct=lambda i, k: i.get_median(k), extra_data=extra_data, auto_axis=True)

def do_graph(instances, metric, bench, npb_class, extra_data=None, auto_axis=True):
    def get_select(benchname, npb_class):
        def select(instance):
            if instance.benchmark.vector[0] != bench:
                return False
            if instance.benchmark.vector[1] != npb_class:
                return False
            return True
        return select

    grapher = get_grapher(bench, npb_class)
    grapher.selection_function = get_select(bench, npb_class)
    grapher.name = 'time_' + metric + '_' + bench.lower() + npb_class

    def compute_v(ht, c, x):
        v1 = ht.get(str(c) + '_' + str(x) + '_')
        return v1

    grapher.gnuplot.ylabel = 'Time (s)'
    grapher.compute_value = compute_v
    grapher.gnuplot.key = 'default'
    grapher.do_graph(instances, label=metric, reduce_fct=lambda i, k: i.get_median(k), extra_data=extra_data)

    grapher = get_grapher(bench, npb_class)
    grapher.name = 'speedup_' + metric + '_' + bench.lower() + npb_class
    grapher.selection_function = get_select(bench, npb_class)
    grapher.gnuplot.ylabel = 'Performance Normalized to Code Without Manual Optimizations'
    grapher.graph_function = graph
    def compute_v(ht, c, x):
        c2 = 'O0'
        v1 = ht.get(c2 + '_' + str(x) + '_')
        v2 = ht.get(c + '_' + str(x) + '_')
        if not v1 or not v2:
            return None
        return v1/v2

    grapher.compute_value = compute_v

    grapher.do_graph(instances, label=metric, reduce_fct=lambda i, k: i.get_median(k), extra_data=extra_data)

if __name__ == "__main__":
    args = parse_arguments()

    if not args.profile:
        main()
    else:
        cProfile.run('main()', 'load_results.profile')
        p = pstats.Stats('load_results.profile')
        p.print_stats()
        p.sort_stats('cumtime').print_stats(15)
        p.sort_stats('tottime').print_stats(15)

