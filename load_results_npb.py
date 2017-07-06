#!/usr/bin/env python3

from configuration import *

from platform import *
from instance import *

from gnuplot_lib import *
from grapher import *

import datetime

def reduce_sum_all(key, instances):
    sum = 0
    for i in instances:
        for l in i.results_ht:
            v = l.get(key, 0)
            if v:
                sum += v
    return sum

def graph_npb(instances):
    for npt in ['is', 'ep', 'cg', 'mg', 'ft']:
        graph_npb_test(instances, npt)

def graph_npb_test(instances, npt):
    print('Graphing NPB ' , npt)

    def get_select(platname):
        def select(instance):
            if instance.benchmark.__class__.__name__ != 'BenchmarkNPB':
                return False
            if instance.platform.__class__.__name__ != 'Platform' + platname:
                return False
            if instance.benchmark.vector[0] != npt:
                return False
            best_opt = {'is': 'O1static', 'cg': 'O3static', 'mg': 'O3', 'ft': 'O1static', 'ep': 'O0'}
            if instance.benchmark.vector[2] != best_opt[npt]:
                return False
            if instance.platform.vector[3] == 'opt_enabled':
                return False
            return True
        return select

    for plat in ['BerkeleyTile']:
        grapher = Grapher()
        grapher.gnuplot.terminal = GNUPlotTerminalPostscript()
        grapher.title = 'NPB - ' + plat + ' - ' + npt
        grapher.name = 'time_npb_' + npt + '_' + plat.lower()
        grapher.selection_function = get_select(plat)
        grapher.derive_x_function = lambda i: i.platform.vector[1]
        grapher.derive_curve_function = lambda i: str(i.platform.vector[0]) + '_' + str(i.benchmark.vector[2])
        grapher.curves_name = {'smp_O0': 'SMP-O0', 'smp_O1': 'SMP-O1', 'smp_O1static': 'SMP-O1static',
                               'mpi_O0': 'MPI-O0', 'mpi_O1': 'MPI-O1', 'mpi_O1static': 'MPI-O1static'}
        grapher.curves_color = {'smp_O0': 1, 'smp_O1': 2, 'smp_O1static': 3,
                               'mpi_O0': 4, 'mpi_O1': 5, 'mpi_O1static': 6}

        def compute_v(ht, c, x):
            #print(ht)
            #print(c)
            #print(x)
            v1 = ht.get(str(c) + '_' + str(x) + '_')
            return v1
        grapher.compute_value = compute_v
        grapher.do_graph(instances)

        grapher = Grapher()
        grapher.gnuplot.terminal = GNUPlotTerminalPostscript()
        grapher.title = 'NPB - ' + plat + ' - ' + npt
        grapher.name = 'speedup_npb_' + npt + '_' + plat.lower()
        grapher.selection_function = get_select(plat)
        grapher.derive_x_function = lambda i: i.platform.vector[1]
        grapher.derive_curve_function = lambda i: str(i.platform.vector[0]) + '_' + str(i.benchmark.vector[2])
        grapher.curves_name = {'smp_O0': 'SMP-O0', 'smp_O1': 'SMP-O1', 'smp_O1static': 'SMP-O1static',
                               'mpi_O0': 'MPI-O0', 'mpi_O1': 'MPI-O1', 'mpi_O1static': 'MPI-O1static'}
        grapher.curves_color = {'smp_O0': 1, 'smp_O1': 2, 'smp_O1static': 3,
                               'mpi_O0': 4, 'mpi_O1': 5, 'mpi_O1static': 6}
        grapher.derive_extra_function = lambda i: ''
        grapher.gnuplot.ylabel = 'Speedup'
        grapher.gnuplot.removeTemporaryFiles = False
        grapher.graph_function = graph
        def compute_v(ht, c, x):
            #print(ht)
            #print(c)
            #print(x)
            v1 = ht.get( str(c) + '_' + str(x) + '_' )
            v2 = ht.get( str(c) + '_' + str(1) + '_')
            print(v1, v2)
            if not v1 or not v2:
                return None
            return v2/v1
        grapher.compute_value = compute_v
        grapher.do_graph(instances)

def main():
    instances = generate_instances(check_platform=False)
    for i in instances:
        print(i)
    if len(instances)==0:
        print("No instances available")
        return

    instances_load_results(instances)
    instances_check_results(instances)

    for i in instances:
        if len(i.results_ht) > 0:
            print(i, '  ', round(i.get_median('total_time')/60, 2), '   ', [int(x['total_time'] / 60) for x in i.results_ht])
        else:
            print(i, '  No results')

    td = datetime.timedelta(reduce_sum_all('total_time', instances) / 60 / 60 / 24)
    print('Total simulation time : ' + str(td))
    print('')

    return
    graph_npb(instances)


    def get_select(benchname, platname):
        def select(instance):
            if instance.benchmark.__class__.__name__ != 'Benchmark' + benchname:
                return False
            if instance.platform.__class__.__name__ != 'Platform' + platname:
                return False
            if instance.benchmark.vector[0] != 512:
                return False
            return True
        return select

    for bench in ['MatrixMultiplication']:
        print(bench)

        for plat in ['BerkeleyTile']:
            grapher = Grapher()
            grapher.gnuplot.terminal = GNUPlotTerminalPostscript()
            grapher.title = bench + ' - ' + plat
            grapher.name = 'time_' + bench.lower() + '_' + plat.lower()
            grapher.selection_function = get_select(bench, plat)
            grapher.derive_x_function = lambda i: i.platform.vector[1]
            grapher.derive_curve_function = lambda i: str(i.benchmark.vector[0]) + '_' + str(i.benchmark.vector[1])
            def compute_v(ht, c, x):
                #print(ht)
                #print(c)
                #print(x)
                v1 = ht.get( str(c) + '_' + str(x) + '_')
                return v1
            grapher.compute_value = compute_v
            grapher.do_graph(instances)

            grapher = Grapher()
            grapher.gnuplot.terminal = GNUPlotTerminalPostscript()
            grapher.title = bench + ' - ' + plat + ' speedup'
            grapher.name = 'speedup_' + bench.lower() + '_' + plat.lower()
            grapher.selection_function = get_select(bench, plat)
            grapher.derive_x_function = lambda i: i.platform.vector[1]
            grapher.derive_curve_function = lambda i: str(i.benchmark.vector[0]) + '_' + str(i.benchmark.vector[1])
            grapher.derive_extra_function = lambda i: ''
            grapher.gnuplot.removeTemporaryFiles = False
            grapher.graph_function = graph
            def compute_v(ht, c, x):
                print(ht)
                print(c)
                print(x)
                v1 = ht.get( str(c[:-1]) + '2_' + str(x) + '_' )
                v2 = ht.get( str(c) + '_' + str(x) + '_')
                print(v1, v2)
                if not v1 or not v2:
                    return None
                return v1/v2
            grapher.compute_value = compute_v
            grapher.do_graph(instances)
    return

if __name__ == "__main__":
    main()

