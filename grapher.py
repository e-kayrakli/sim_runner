from gnuplot_lib import *
import os

@staticmethod
def selection_function_default(i):
    return True

@staticmethod
def derive_extra_default(i):
    return ''

@staticmethod
def compute_value_default(ht, c, x):
    return ht.get( str(c) + '_' + str(x) + '_' )

def get_pow2_scale(maxScale):
    s = 1
    x_axis = []
    while s<=maxScale:
        x_axis.append(s)
        s = s * 2

    return x_axis

def generate_dat2(x_axis, curves, ht, fct):
    lines = []

    for x in x_axis:
        line = []
        line.append(str(x))
        print(curves)
        for c in curves: #sorted(curves):
            val = fct(ht, c, x)
            if val:
                line.append(val)
            else:
                line.append(None)
        lines.append(line)
    return lines

def generate_dat(x_axis, curves, ht, fct):
    line = ''
    for x in x_axis:
        line += str(x) + " "
        for c in curves:
            val = fct(ht, c, x)
            if val:
                line += "%10.4f" % val + ", "
            else:
                line += "     ?    " + ", "

        if line.find("    0.0   ") == -1:
            line = line[:-2] + '\n'
        else:
            line = line[:-2] + '\n'
            print('Warning graph skip line ' + line)

    return line

def clean_x_axis(x_axis, curves, ht, fct):
    to_remove = []

    for x in x_axis:
        is_to_remove = True
        for c in curves:
            val = fct(ht, c, x)
            if val:
                is_to_remove = False
        if is_to_remove:
            to_remove.append(x)

    for x in to_remove:
        if x in x_axis:
            print('WARNING: Removing ' + str(x))
            x_axis.remove(x)

    return x_axis

def get_max(x_axis, curves, ht, fct):
    max_v = -10000000000.
    for x in x_axis:
        for c in curves:
            val = fct(ht, c, x)
            if val:
                if val > max_v:
                    max_v = val
    return max_v

@staticmethod
def graph_no_auto_x(gnuplot, x_axis, curves, ht, grapher, fct):
    gnuplot.filename = grapher.name
    gnuplot.title = grapher.title
    gnuplot.yrange = '[0:*]'

    s = "plot "
    n = 1
    for c in curves:
        c_name = grapher.curves_name.get(c, c)
        c_color = grapher.curves_color.get(c, n)
        c_point = grapher.curves_point.get(c, n)
        n = n + 1
        s += """    \"""" + grapher.name + """.dat" using 1:""" + str(n) + \
             " title '" + c_name + \
             "' w linespoints lt " + str(c_color) + " lw 3 pt " + str(c_point) + "  , \\\n"

    line = generate_dat(x_axis, curves, ht, fct)
    gnuplot.plot(s[:-4], line)

@staticmethod
def graph(gnuplot, x_axis, curves, ht, grapher, fct, auto_axis=False):
    gnuplot.filename = grapher.name

    gnuplot.title = grapher.title

    x_axis = clean_x_axis(x_axis, curves, ht, fct)

    if auto_axis:
        gnuplot.xrange = '[1:' + str(max(x_axis)) + ']'
    else:
        gnuplot.xrange = '[1:' + str(max(x_axis)) + ']'
        #max_y = get_max(x_axis, curves, ht, fct)
        #gnuplot.yrange = '[0:' + str(max_y*1.3) +']'
        gnuplot.yrange = '[0:*]'
    #gnuplot.key = 'right bottom'

    s = """plot \\\n"""
    n = 1
    for c in curves:
        c_name = grapher.curves_name.get(c, c)
        c_color = grapher.curves_color.get(c, n)
        c_point = grapher.curves_point.get(c, n)
        n = n + 1
        s += """    \"""" + grapher.name + """.dat" using 1:""" + str(n) + \
             " title '" + str(c_name) + \
             "' w linespoints lt " + str(c_color) + " lw 3 pt " + str(c_point) + "  , \\\n"

    line = generate_dat(x_axis, curves, ht, fct)
    gnuplot.plot(s[:-4], line)

@staticmethod
def graph_histogram(gnuplot, x_axis, curves, ht, grapher, fct):
    gnuplot.filename = grapher.name
    gnuplot.title = grapher.title
    gnuplot.style = ['data histogram', 'histogram cluster gap 1', 'fill pattern 4 border -1' ]
    x_axis = clean_x_axis(x_axis, curves, ht, fct)
    #max_y = get_max(x_axis, curves, ht, fct)
    #gnuplot.yrange = '[0:' + str(max_y*1.3) +']'
    #gnuplot.key = 'left'
    gnuplot.yrange = '[0:*]'

    s = "plot "
    n = 1
    for c in curves:
        c_name = grapher.curves_name.get(c, c)
        c_color = grapher.curves_color.get(c, n)
        c_point = grapher.curves_point.get(c, n)
        n = n + 1
        s += """    \"""" + grapher.name + """.dat" using """ + str(n) + ":xtic(1) title '" + c_name + \
             "' fill pattern " + str(c_color) + " lt " + str(c_point) + ", \\\n"

    line = generate_dat(x_axis, curves, ht, fct)

    gnuplot.plot(s[:-4], line)

class GraphData(object):
    pass

class Grapher(object):
    selection_function = selection_function_default
    graph_function = graph
    derive_curve_function = None
    derive_x_function = None
    derive_extra_function = derive_extra_default
    compute_value = compute_value_default
    name = 'name'
    title = 'title'
    curves_name = {}
    curves_color = {}
    curves_point = {}

    def __init__(self):
        self.gnuplot = GNUPlot()
        self.gnuplot.ylabel = 'Time (s)'
        self.gnuplot.xrange = None

    def auto_fill_curves_name(self, instances):
        lst = []
        for i in instances:
            if self.selection_function(i):
                name = self.derive_curve_function(i)
                if not name in lst:
                    lst.append(name)

        color = 2
        self.curves_name = {}
        self.curves_color = {}
        self.curves_point = {}
        for name in lst:
            self.curves_name[name] = name
            self.curves_color[name] = color
            self.curves_point[name] = color
            color = color + 1

    def do_preprocess(self, instances, label='total_time', reduce_fct=None, extra_data=None):
        curves = []
        ht = {}
        x_axis = []

        if not reduce_fct:
            reduce_fct = lambda i, x: i.get_median(x)

        lst_data = []
        if extra_data:
            lst_data = list(extra_data)

        for i in instances:
            if self.selection_function(i):
                data = GraphData()

                data.name = self.derive_curve_function(i)
                data.x_val = self.derive_x_function(i)
                data.y_val = reduce_fct(i, label)
                data.extra = self.derive_extra_function(i)

                lst_data.append(data)

        for i in lst_data:
            if self.curves_name.get(i.name):
                if not i.name in curves:
                    curves.append(i.name)
            else:
                print('Warning: no name for curve ', i.name)
                if not i.name in curves:
                    curves.append(i.name)

            if not i.x_val in x_axis:
                x_axis.append(i.x_val)

            key = str(i.name) + '_' + str(i.x_val) + '_' + str(i.extra)
            ht[key] = i.y_val

        # DEBUG
        #print(curves)
        #print(ht)
        #print(x_axis)

        return (curves, ht, x_axis)

    def do_graph(self, instances, label='total_time', auto_axis=False, reduce_fct=None, extra_data=None):
        # Make sure that the directory exists
        folder = os.path.dirname('graphs/' + self.name)
        if not os.path.exists(folder):
            print('Creating ', folder)
            os.makedirs(folder)

        (curves, ht, x_axis) = self.do_preprocess(instances, label, reduce_fct=reduce_fct, extra_data=extra_data)

        if isinstance(self.graph_function, staticmethod):
            self.graph_function = self.graph_function.__get__(self)

        self.graph_function(self.gnuplot, x_axis, curves, ht, self, self.compute_value, auto_axis)

    def do_dat_file(self, instances, label='total_time'):
        (curves, ht, x_axis) = self.do_preprocess(instances, label)
        lines = generate_dat2(x_axis, curves, ht, self.compute_value)
        return lines

    def do_perl_histogram(self, instances, label='total_time', names=['PCA-DT ', 'PCA-ST', 'Base']):
        name2 = ";".join(names)
        header = """#Normalized Ruby Cycles
=cluster;""" + name2 + """
#=patterns
#colors=grey3,grey6
#xlabel=Benchmarks
yformat=%g
ylabel=Normalized Execution Time
legendx=right
legendy=center
=nolegoutline
=noupperright
#=nogridy
=table
max=1.0
min=0.5

#rotateby=-60
# stretch it out in x direction
#extraops=set size 1.2,1
=nocommas

"""
        result = header
        lines = self.do_dat_file(instances, label)

        for l in lines:
            try:
                m = max(l[1:])
            except:
                m = None
            if m != None:
                if len(l) < 3:
                    continue
                name = str(l[0])
                if name.startswith('Benchmark'):
                    name = name[9:]
                result = result + name + ' '
                for v in l[1:]:
                    result = result + str(v/m) + ' '
                result = result + "\n"

        folder = 'graphs/'
        phg_filename = folder + self.name + ".phg"

        f = open(phg_filename, 'w')
        f.write(result)
        f.close()

        (status, data) = subprocess.getstatusoutput('cd ' + folder + '; perl ../bargraph.pl ' + self.name + '.phg > '+  self.name + '_phg.eps')
        print('Perl script returned : ' + str(status))
        print(data)

