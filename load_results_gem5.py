#!/usr/bin/env python3

import configuration_gem5
import instance

from gnuplot_lib import *
from grapher import *

import argparse
import datetime
import cProfile
import util
import pstats
import os
from load_results import print_table, reduce_sum_all

def parse_arguments():
    parser = argparse.ArgumentParser(description='Load GEM5 results')

    parser.add_argument('-g', '--graphs', action='store_true', help='Generate graphs')
    parser.add_argument('-m', '--missings', action='store_true', help='Only display instances with no results')
    parser.add_argument('-p', '--profile', action='store_true', help='Profile the execution')
    parser.add_argument('-f', '--fix', action='store_true', help='Try hard to fix issues')

    res = parser.parse_args()
    return res

class QuickTable():
    def __init__(self):
        self.table = []

    def fixup(self):
        """ Make sure all the rows are of equal length """

        max_length = max([len(r) for r in self.table])
        for r in self.table:
            to_add = max_length - len(r)
            for i in range(to_add):
                r.append('')

    def add_row(self, lst):
        self.table.append(lst)
        self.fixup()

    def add_column(self, lst):
        for (line, new_element) in zip(self.table, lst):
            line.append(new_element)
        self.fixup()

    def transpose(self):
        self.table = [list(i) for i in zip(*self.table)]

    def merge(self, qt):
        for l in qt.table:
            self.table.append(l)

        self.fixup()

    def delete_column(self, col_idx):
        for l in self.table:
            try:
                l.pop(col_idx)
            except:
                pass

    def delete_row(self, row_idx):
        self.table.pop(row_idx)

    def __str__(self):
        s = ''
        for l in self.table:
            s += ' | '.join(l)
            s += '\n'
        return s

    def to_latex(self):
        self.transpose()
        nb_colums = len(self.table[0])

        l1 = self.table.pop(0)
        s = r'\begin{tabular}{|'

        prev = None
        for e in l1:
            if prev == e:
                s += 'r|'
            else:
                if prev != None:
                    s += 'r||'
                prev = e
        if prev:
            s += 'r|'

#        s += 'r|' * nb_colums
        s += '}' + '\n'
        s+= r'\hline' + '\n'

        count = 0
        prev = None
        for e in l1:
            if prev == e:
                count += 1
            else:
                if prev != None:
                    s+= '\\multicolumn{' + str(count) + '}{|c||}{\\textbf{' + prev + '}} &'
                count = 1
                prev = e
        if prev:
            s+= '\\multicolumn{' + str(count) + '}{|c|}{\\textbf{' + prev + '}}'
        s+= r'\\' + '\n'
        s+= r'\hline' + '\n'
        s+= r'\hline' + '\n'

        l = self.table.pop(0)
        l2 = [str(e) for e in l]
        s += ' & '.join(l2)
        s+= r'\\' + '\n'
        s+= r'\hline' + '\n'

        for l in self.table:
            l2 = [str(e) for e in l]
            s += ' & '.join(l2)
            s+= r'\\' + '\n'

        s+= r'\hline' + '\n'
        s+= r'\end{tabular}'
        return s

def main():
    instances = configuration_gem5.generate_instances(check_platform=False)

    if len(instances)==0:
        print("No instances available")
        return

    instance.instances_load_results(instances)
    if args.fix:
        for i in instances:
            i.fix_issues()
        return
    instance.instances_check_results(instances)

    if args.missings:
        missings = 0
        for i in instances:
            if len(i.results_ht) == 0:
                missings += 1
                print(i, i.results_ht, i.still_running)
        print('Missings :', missings)
        return

    #print_table(instances, 'sim_seconds')
    #print_table(instances, 'host_mem_usage', function=lambda x: x/1024./1024., unit='MB')
    print_table(instances, 'host_inst_rate', function=lambda x: x/1000., unit='k inst/s')
    #print_table(instances, 'system.physmem.bytesRead')
    #print_table(instances, 'system.physmem.bytesWritten')

    print_table(instances, 'system.cpu.num_pgas_loads')
    print_table(instances, 'system.cpu.num_pgas_stores')
    #print_table(instances, 'crc')
    #print_table(instances, 'cycles')
    print_table(instances, 'host_seconds', wanted_nb_results = 2, function=lambda x: x/60./60., unit='hr')
    print_table(instances, 'host_seconds', wanted_nb_results = 2, function=lambda x: x/60./60., unit='hr',
            file=open('logs/' + util.get_log_time() + '_host_seconds', 'w'))

    print_table(instances, 'total_time', wanted_nb_results = 2)
    print_table(instances, 'total_time', wanted_nb_results = 2,
            file=open('logs/' + util.get_log_time() + '_total_time', 'w'))

    print('Adding pgas_loads and pgas_stores to instances')
    init_instance_ht(instances)

    def get_val(s, key):
        i = find_instance_str(instances, s)
        if i == None:
            return None
        for ht in i.results_ht:
            if key in ht:
                return ht[key]
        return None

    missing = 0
    for key in ['system.cpu.num_pgas_loads', 'system.cpu.num_pgas_stores']:
        for i in instances:
            for ht in i.results_ht:
                if key in ht:
                    continue

                s = str(i)
                s = s.replace("'timing', 32, 4096", "'atomic', 0, 0")
                s = s.replace("'detailed', 32, 4096", "'atomic', 0, 0")
                s = s.replace('BO1', 'BO3')
                v = get_val(s, key)

                if v == None:
                    s = s.replace('BO3', 'BO1')
                    v = get_val(s, key)

                if v == None:
                    #print('No value :( ', str(ht))
                    missing += 1
                    continue
                ht[key] = v
    print('NB stats missing', missing)

    for i in instances:
        t = i.get_median('total_time')
        pl = i.get_median('system.cpu.num_pgas_loads')
        if pl == None:
            continue
        pl += i.get_median('system.cpu.num_pgas_stores')

        t2 = t+pl/1000/1000/1000./2.


    cpus_avail = ['atomic', 'timing', 'detailed']
    for bench in['cg', 'ft', 'is', 'mg', 'mm', 'sobel', 'heat']:
        #print(bench)
        qt_bench = QuickTable()
        for cpu in cpus_avail:
            qt = QuickTable()
            qt.add_row(['', '\\# Th'])
            qt.add_row([cpu, '0-0'])
            qt.add_row([cpu, '1-0'])
            qt.add_row([cpu, '1-1'])
            qt.add_row([cpu, '2-1'])

            npb_class = 'W'
            if bench in ['mm', 'heat', 'sobel']:
                if bench == 'mm':
                    bname = 'UBMatrixMultiplicationHW'
                    size = 512
                if bench == 'heat':
                    bname='UBHeatMultiDHW'
                    size = 64
                if bench == 'sobel':
                    bname='UBSobelHW'
                    size = 4096
                def select(instance):
                    if instance.benchmark.get_name() != bname:
                        return False
                    if instance.benchmark.vector[0] != size:
                        return False
                    if bname=='UBMatrixMultiplicationHW':
                        if instance.benchmark.vector[1] != 'MO_SOFT2':
                            return False
                    #if bname=='UBMatrixMultiplicationHW':
                    #    if instance.benchmark.vector[1] not in ['MO_SOFT2']:
                    #        if instance.benchmark.vector[2] != 'no':
                    #            return False
                    if instance.platform.vector[1] != cpu:
                        return False
                    if not instance.has_results():
                        return False
                    return True
            else:
                def select(instance):
                    if instance.benchmark.vector[0] != bench:
                        return False
                    if instance.benchmark.vector[1] != npb_class:
                        return False
                    if instance.benchmark.vector[2].find('static') != -1:
                        return False
                    if instance.benchmark.vector[2] != 'O0': #.find('O3') != -1:
                        return False
                    if instance.platform.vector[1] != cpu:
                        return False
                    if instance.platform.vector[5] != 'BO1':
                        return False
                    if not instance.has_results():
                        return False
                    return True

            instances_x = list(filter(select, instances))
            for i in instances_x:
                if bench in ['mm', 'heat', 'sobel']:
                    if i.benchmark.vector[2] != 'no':
                        continue
                else:
                    if i.benchmark.vector[3] != 'no':
                        continue
                i2 = find_instance_str(instances, str(i).replace('no', 'yes'))
                t_o = i.get_median('total_time')
                t_hw = i2.get_median('total_time')
                nb_loads = i2.get_median('system.cpu.num_pgas_loads')
                nb_stores = i2.get_median('system.cpu.num_pgas_stores')
                if nb_loads == None:
                    continue

                nb_threads = i.platform.vector[0]

                speedup_hw = t_o / t_hw

                p1_0 = nb_loads + 0 * nb_stores
                p1_1 = nb_loads + nb_stores
                p2_1 = 2*nb_loads + nb_stores

                extra_time1_0 = p1_0/1000/1000/1000./2.
                extra_time1_1 = p1_1/1000/1000/1000./2.
                extra_time2_1 = p2_1/1000/1000/1000./2.

                t1_0 = t_hw + extra_time1_0
                t1_1 = t_hw + extra_time1_1
                t2_1 = t_hw + extra_time2_1

                speedup_hw1_0 = t_o / t1_0
                speedup_hw1_1 = t_o / t1_1
                speedup_hw2_1 = t_o / t2_1

                qt.add_column(['%d' % nb_threads,
                    '%4.2f' % speedup_hw,
                    '%4.2f' % speedup_hw1_0,
                    '%4.2f' % speedup_hw1_1,
                    '%4.2f' % speedup_hw2_1
                    ]
                    )
            #print(qt)
            if qt_bench.table:
                qt.delete_row(0)
            qt.delete_row(len(qt.table) - 1)
            #util.format_table(qt.table)
            qt_bench.merge(qt)

        mls = max([len(z) for z in qt_bench.table])
        if mls <= 2:
            continue

        benchu = bench.upper()
        print()
        print(r'''
\begin{table}[tb]
\tbl{PGAS Instruction Stall Cycles Sensitivity Study %(benchu)s}
{
\small
\label{tab:sensitivity_%(bench)s}''' % locals()
        )
        print(qt_bench.to_latex())
        print(r'''}
\end{table}''')

    td = datetime.timedelta(reduce_sum_all('host_seconds', instances) / 60 / 60 / 24)
    print()
    print('Total simulation time : ' + str(td))
    print('Estimate cpu core usage time : ' + str(td * 8. / 3.))

    show_speedup = False
    if show_speedup:
        nb_goods = 0
        for i in instances:
            if i.benchmark.vector[3] != 'no':
                continue
            try:
                i2 = find_instance_str(instances, str(i).replace('no', 'yes').replace('O1', 'O0'))
                t_o = i.get_median('total_time')
                t_hw = i2.get_median('total_time')
                print('%105s' % i, '%5.2f' % t_o, '%5.2f' % t_hw, '%5.2f' % (t_o/ t_hw))
                nb_goods += 1
            except:
                print('Error ', i)
                continue
        print('Nb goods', nb_goods)


    if not args.graphs:
        return False

    cpus_avail = ['atomic', 'timing', 'detailed']

    for half_size in [True, False]:
        for cpu in cpus_avail:
            for size in ['S', 'W', 'A']:
                for test_kernel in ['vector_add', 'mm', 'ra', 'hd']:
                    try:
                        lst_extra = []
                        do_graph_chapel(instances, 'total_time', cpu, size, half_size, bname=test_kernel)
                    except Exception as e:
                        print(e)
                        print('Unable to create graph:', cpu, size)
    return

    for half_size in [True, False]:
        for cpu in cpus_avail:
            for size in [256, 512]:
                try:
                    do_graph_mm(instances, 'total_time', cpu, size, half_size)
                except Exception as e:
                    print(e)
                    print('Unable to create graph:', cpu, size)

        for cpu in cpus_avail:
            for size in [64]:
                try:
                    lst_extra = []
                    do_graph_mm(instances, 'total_time', cpu, size, half_size, bname='UBHeatMultiDHW')
                except Exception as e:
                    print(e)
                    print('Unable to create graph:', cpu, size)

        for cpu in cpus_avail:
            for size in [4096]:
                try:
                    lst_extra = []
                    do_graph_mm(instances, 'total_time', cpu, size, half_size, bname='UBSobelHW')
                except Exception as e:
                    print(e)
                    print('Unable to create graph:', cpu, size)

        for cpu in cpus_avail:
            for bench in ['is', 'ep', 'cg', 'mg', 'ft']:
                for npb_class in ['W']:
                    try:
                        do_graph(instances, 'total_time', cpu, bench, npb_class, half_size)
                    except Exception as e:
                        print(e)
                        print('Unable to create graph:', cpu, bench, npb_class)


def set_grapher_size(grapher, half_size=False):
    if half_size:
        grapher.gnuplot.terminal.terminal = 'postscript enhanced eps color lw 2 "Helvetica" 16 size 2.5,3.5'
        grapher.gnuplot.lmargin = 'at screen 0.15'
        grapher.gnuplot.rmargin = 'at screen 0.96'
    else:
        grapher.gnuplot.terminal.terminal = 'postscript enhanced eps color lw 2 "Helvetica" 16 size 5,3.5'

def get_grapher_chapel(size, half_size=False):
    grapher = Grapher()
    grapher.title = None #'MM ' + str(size)
    grapher.gnuplot.terminal = GNUPlotTerminalEPS()
    set_grapher_size(grapher, half_size)
    grapher.derive_x_function = lambda i: i.platform.vector[0]
    grapher.derive_curve_function = lambda i: '-'.join([str(x) for x in i.benchmark.vector[1:]])
    grapher.derive_extra_function = lambda i: ''
    grapher.gnuplot.removeTemporaryFiles = False
    grapher.curves_name = {
            'MO_SOFT1-yes': 'No Manual, HW',
            'MO_SOFT2-yes': 'No Manual, HW',
            'MO_SOFT3-yes': '3y',
            'MO_SOFT4-yes': '4y',
            'MO_SOFT5-yes': '5y',
            'MO_SOFT1-no': 'No Manual, no HW',
            'MO_SOFT2-no': 'No Manual, no HW',
            'MO_SOFT3-no': 'Privatization, no HW',
            'MO_SOFT4-no': 'Privatization 2, no HW',
            'MO_SOFT5-no': '5n',
            'S-O0-yes': 'No Manual, HW',
            'S-O0-no': 'No Manual, no HW',
            'S-O1-no': 'Manual opts, no HW',
            'W-O0-yes': 'No Manual, HW',
            'W-O0-no': 'No Manual, no HW',
            'W-O1-no': 'Manual opts, no HW',
            'A-O0-yes': 'No Manual, HW',
            'A-O0-no': 'No Manual, no HW',
            'A-O1-no': 'Manual opts, no HW',
            }
    return grapher

def do_graph_chapel(instances, metric, cputype, size, half_size=False, bname='vector_add'):
    def get_select(cputype, size):
        def select(instance):
            if instance.benchmark.get_name() != 'ChapelHW':
                return False
            if instance.benchmark.vector[0] != bname:
                return False
            if instance.benchmark.vector[1] != size:
                return False
            if instance.platform.vector[2] != cputype:
                return False
            if instance.platform.vector[1] != 2 and instance.platform.vector[0] != 1:
                return False
            return True
        return select

    grapher = get_grapher_chapel(size, half_size)
    grapher.selection_function = get_select(cputype, size)

    if half_size:
        folder = 'half_size/' + cputype + '/'
    else:
        folder  = 'full_size/' + cputype + '/'

    grapher.name = folder + 'time_' + cputype + '_' + metric + '_' + bname.lower() + '_' + str(size)

    def compute_v(ht, c, x):
        v1 = ht.get(str(c) + '_' + str(x) + '_')
        return v1

    grapher.gnuplot.ylabel = 'Time (s)'
    grapher.compute_value = compute_v
    grapher.gnuplot.key = 'default'
    grapher.do_graph(instances, label=metric, reduce_fct=lambda i, k: i.get_min(k))

    grapher = get_grapher_chapel(size, half_size)
    grapher.name = folder + 'speedup_' + cputype + '_' + metric + '_' + bname.lower() + '_' + str(size)
    grapher.selection_function = get_select(cputype, size)
    grapher.gnuplot.ylabel = 'Performance Normalized to Code Without Manual Optimizations'
    grapher.graph_function = graph

    def compute_v(ht, c, x):
        lst = c.split('-')
        lst[1] = 'O0'
        lst[2] = 'no'
        c2 = '-'.join(lst)
        v1 = ht.get(c2 + '_' + str(x) + '_')
        v2 = ht.get(c + '_' + str(x) + '_')
        if not v1 or not v2:
            return None
        return v1/v2
    grapher.compute_value = compute_v

    grapher.do_graph(instances, label=metric, reduce_fct=lambda i, k: i.get_min(k))

    grapher = get_grapher_chapel(size, half_size)
    grapher.name = folder + 'scalability_' + cputype + '_' + metric + '_' + bname.lower() + '_' + str(size)
    grapher.selection_function = get_select(cputype, size)
    grapher.gnuplot.ylabel = 'Scalability'
    grapher.gnuplot.key = 'top left'
    grapher.graph_function = graph
    def compute_v(ht, c, x):
        v1 = ht.get(c + '_' + str(1) + '_')
        v2 = ht.get(c + '_' + str(x) + '_')
        if not v1 or not v2:
            return None
        return v1/v2
    grapher.compute_value = compute_v

    grapher.do_graph(instances, label=metric, reduce_fct=lambda i, k: i.get_min(k))

def get_grapher_mm(size, half_size=False):
    grapher = Grapher()
    grapher.title = None #'MM ' + str(size)
    grapher.gnuplot.terminal = GNUPlotTerminalEPS()
    set_grapher_size(grapher, half_size)
    grapher.derive_x_function = lambda i: i.platform.vector[0]
    grapher.derive_curve_function = lambda i: '-'.join([str(x) for x in i.benchmark.vector[1:]])
    grapher.derive_extra_function = lambda i: ''
    grapher.gnuplot.removeTemporaryFiles = False
    grapher.curves_name = {
            'MO_SOFT1-yes': 'No Manual, HW',
            'MO_SOFT2-yes': 'No Manual, HW',
            'MO_SOFT3-yes': '3y',
            'MO_SOFT4-yes': '4y',
            'MO_SOFT5-yes': '5y',
            'MO_SOFT1-no': 'No Manual, no HW',
            'MO_SOFT2-no': 'No Manual, no HW',
            'MO_SOFT3-no': 'Privatization, no HW',
            'MO_SOFT4-no': 'Privatization 2, no HW',
            'MO_SOFT5-no': '5n',
            }
    return grapher

def do_graph_mm(instances, metric, cputype, size, half_size=False, bname='UBMatrixMultiplicationHW'):
    def get_select(cputype, size):
        def select(instance):
            if instance.benchmark.get_name() != bname:
                return False
            if instance.benchmark.get_name() != 'ChapelHW':
                if instance.benchmark.vector[0] != size:
                    return False
            else:
                if instance.benchmark.vector[1] != size:
                    return False
            if bname=='UBMatrixMultiplicationHW':
                if instance.benchmark.vector[1] in ['MO_SOFT1', 'MO_SOFT5']:
                    return False
            if bname=='UBMatrixMultiplicationHW':
                if instance.benchmark.vector[1] not in ['MO_SOFT2']:
                    if instance.benchmark.vector[2] != 'no':
                        return False
            if instance.benchmark.get_name() != 'ChapelHW':
                if instance.platform.vector[1] != cputype:
                    return False
                else:
                    if instance.platform.vector[2] != cputype:
                        return False
                    if instance.platform.vector[1] != 2 or instance.platform.vector[0] == 1:
                        return False
            print(instance)
            return True
        return select

    grapher = get_grapher_mm(size, half_size)
    grapher.selection_function = get_select(cputype, size)

    if half_size:
        folder = 'half_size/' + cputype + '/'
    else:
        folder  = 'full_size/' + cputype + '/'

    grapher.name = folder + 'time_' + cputype + '_' + metric + '_' + bname.lower() + '_' + str(size)

    def compute_v(ht, c, x):
        v1 = ht.get(str(c) + '_' + str(x) + '_')
        return v1

    grapher.gnuplot.ylabel = 'Time (s)'
    grapher.compute_value = compute_v
    grapher.gnuplot.key = 'default'
    grapher.do_graph(instances, label=metric, reduce_fct=lambda i, k: i.get_min(k))

    grapher = get_grapher_mm(size, half_size)
    grapher.name = folder + 'speedup_' + cputype + '_' + metric + '_' + bname.lower() + '_' + str(size)
    grapher.selection_function = get_select(cputype, size)
    grapher.gnuplot.ylabel = 'Performance Normalized to Code Without Manual Optimizations'
    grapher.graph_function = graph

    def compute_v(ht, c, x):
        lst = c.split('-')
        if bname == 'UBSobelHW':
            lst[0] = 'MO_SOFT4'
        elif bname == 'UBMatrixMultiplicationHW':
            lst[0] = 'MO_SOFT2'
        else:
            lst[0] = 'MO_SOFT1'
        lst[1] = 'no'
        c2 = '-'.join(lst)
        v1 = ht.get(c2 + '_' + str(x) + '_')
        v2 = ht.get(c + '_' + str(x) + '_')
        if not v1 or not v2:
            return None
        return v1/v2
    grapher.compute_value = compute_v

    grapher.do_graph(instances, label=metric, reduce_fct=lambda i, k: i.get_min(k))

    grapher = get_grapher_mm(size, half_size)
    grapher.name = folder + 'scalability_' + cputype + '_' + metric + '_' + bname.lower() + '_' + str(size)
    grapher.selection_function = get_select(cputype, size)
    grapher.gnuplot.ylabel = 'Scalability'
    grapher.gnuplot.key = 'top left'
    grapher.graph_function = graph
    def compute_v(ht, c, x):
        v1 = ht.get(c + '_' + str(1) + '_')
        v2 = ht.get(c + '_' + str(x) + '_')
        if not v1 or not v2:
            return None
        return v1/v2
    grapher.compute_value = compute_v

    grapher.do_graph(instances, label=metric, reduce_fct=lambda i, k: i.get_min(k))

def get_grapher(bench, npb_class, half_size=False):
    grapher = Grapher()
    grapher.title = None # bench.upper() + ' - Class ' + npb_class
    grapher.gnuplot.terminal = GNUPlotTerminalEPS()
    set_grapher_size(grapher, half_size)
    grapher.derive_x_function = lambda i: i.platform.vector[0]
    grapher.derive_curve_function = lambda i: '-'.join([str(x) for x in i.benchmark.vector[2:]])
    grapher.derive_extra_function = lambda i: ''
    grapher.gnuplot.removeTemporaryFiles = False
    if half_size:
        grapher.curves_name = {
                'O0-no': 'No Manual',
                'O0-yes': 'No Manual, HW',
                'O1-no': 'Privatization',
                'O1static-no': 'Privatization, static',
                'O3-no': 'Privatized+Prefetching',
                'O3static-no': 'Privatized+Prefetching, static'
                }
    else:
        grapher.curves_name = {
                'O0-no': 'No Manual Opts',
                'O0-yes': 'With HW support',
                'O1-no': 'Manual Privatization',
                'O1static-no': 'Manual Privatization, static',
                'O3-no': 'Privatized+Prefetching',
                'O3static-no': 'Privatized+Prefetching, static'
                }
    return grapher

def do_graph(instances, metric, cputype, bench, npb_class, half_size=False):
    def get_select(benchname, cputype, npb_class):
        def select(instance):
            if instance.benchmark.vector[0] != bench:
                return False
            if instance.benchmark.vector[1] != npb_class:
                return False
            if instance.benchmark.vector[2].find('static') != -1:
                return False
            if instance.benchmark.vector[2].find('O3') != -1:
                return False
            if instance.platform.vector[1] != cputype:
                return False
            if instance.platform.vector[5] != 'BO1':
                return False
            return True
        return select

    grapher = get_grapher(bench, npb_class, half_size)
    grapher.selection_function = get_select(bench, cputype, npb_class)
    if half_size:
        folder = 'half_size/' + cputype + '/'
    else:
        folder  = 'full_size/' + cputype + '/'
    grapher.name = folder + 'time_' + cputype + '_' + metric + '_' + bench.lower() + npb_class
    def compute_v(ht, c, x):
        v1 = ht.get(str(c) + '_' + str(x) + '_')
        return v1
    grapher.gnuplot.ylabel = 'Time (s)'
    grapher.compute_value = compute_v
    grapher.gnuplot.key = 'default'
    grapher.do_graph(instances, label=metric, reduce_fct=lambda i, k: i.get_min(k))

    grapher = get_grapher(bench, npb_class, half_size)
    grapher.name = folder + 'speedup_' + cputype + '_' +  metric + '_' + bench.lower() + npb_class
    grapher.selection_function = get_select(bench, cputype, npb_class)
    grapher.gnuplot.ylabel = 'Performance Normalized to Code Without Manual Optimizations'
    grapher.gnuplot.ylabel = 'Performance Improvement over No Opts., No HW'
    grapher.graph_function = graph
    def compute_v(ht, c, x):
        lst = c.split('-')
        lst[0] = 'O0'
        lst[1] = 'no'
        c2 = '-'.join(lst)
        v1 = ht.get(c2 + '_' + str(x) + '_')
        v2 = ht.get(c + '_' + str(x) + '_')
        if not v1 or not v2:
            return None
        return v1/v2
    grapher.compute_value = compute_v
    grapher.do_graph(instances, label=metric, reduce_fct=lambda i, k: i.get_min(k))

    grapher = get_grapher(bench, npb_class, half_size)
    grapher.name = folder + 'scalability_' + cputype + '_' +  metric + '_' + bench.lower() + npb_class
    grapher.selection_function = get_select(bench, cputype, npb_class)
    grapher.gnuplot.ylabel = 'Scalability'
    grapher.gnuplot.key = 'top left'
    grapher.graph_function = graph
    def compute_v(ht, c, x):
        v1 = ht.get(c + '_' + str(1) + '_')
        v2 = ht.get(c + '_' + str(x) + '_')
        if not v1 or not v2:
            return None
        return v1/v2
    grapher.compute_value = compute_v
    grapher.do_graph(instances, label=metric, reduce_fct=lambda i, k: i.get_min(k))

instances_ht = {}
def init_instance_ht(instances):
    for i in instances:
        instances_ht[str(i)] = i

def find_instance_str(instances, s):
    return instances_ht.get(s, None)


if __name__ == "__main__":
    args = parse_arguments()

    if not args.profile:
        main()
    else:
        cProfile.run('main()', 'load_results.profile')
        p = pstats.Stats('load_results.profile')
        p.print_stats()
        p.sort_stats('tottime').print_stats(15)

