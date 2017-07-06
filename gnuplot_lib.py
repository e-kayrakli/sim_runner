#!/usr/bin/env python3

import subprocess
import os
from util import *

class GNUPlotTerminal(object):
    terminal = None
    output_format = None

    def __str__(self):
        return self.terminal

class GNUPlotTerminalPNG(GNUPlotTerminal):
    terminal = "png giant size 1024,768"
    output_format = "png"

class GNUPlotTerminalPostscript(GNUPlotTerminal):
    terminal = 'postscript enhanced color lw 1 "Helvetica" 12'
    output_format = "ps"

    def post_processing(self, filename, updated):
        suffix = ".ps"
        if filename.endswith(suffix):
            basename = filename[:-len(suffix)]

        if not updated:
            if os.path.isfile(basename + '.pdf'):
                return

        run_cmd('epstopdf ' + filename)
        run_cmd('pdftk %(basename)s.pdf cat 1-endE output %(basename)s.2.pdf' % locals())
        run_cmd('mv %(basename)s.2.pdf %(basename)s.pdf' % locals())

class GNUPlotTerminalEPS(GNUPlotTerminal):
    terminal = 'postscript enhanced eps color lw 2 "Helvetica" 16'
    output_format = "eps"

    def post_processing(self, filename, updated):
        suffix = ".eps"
        if filename.endswith(suffix):
            basename = filename[:-len(suffix)]

        if not updated:
            if os.path.isfile(basename + '.pdf'):
                return

        run_cmd('epstopdf ' + filename)

class GNUPlot(object):
    title = None
    filename = None

    terminal = GNUPlotTerminalPNG()

    xlabel = 'Number of threads'
    ylabel = 'Time (s)'

    xtics = "(1,2,4,8,16,32,64,128,256,512,1024,2048)"
    xrange = "[1:128]"

    gnuplot_data = None
    gnuplot_cmd = None

    key = 'left bottom'
    pointsize = 2

    style = None
    removeTemporaryFiles=True

    folder = None

    yrange = None

    lmargin = 'at screen 0.08'
    rmargin = 'at screen 0.98'
    tmargin = 'at screen 0.96'
    bmargin = 'at screen 0.10'

    def command_add(self, command):
        self.gnuplot_cmd.write(command + '\n')

    def plot(self, plot, data, folder='graphs/'):
        if self.folder:
            folder = self.folder

        dat_filename = folder + self.filename + ".dat"
        cmd_filename = folder + self.filename + ".gplt"

        self.gnuplot_data = open(dat_filename, "w")
        self.gnuplot_cmd = open(cmd_filename, "w")

        options = [ \
            ('terminal', False), ('xtics', False), ('title', True), \
            ('xrange', False), ('xlabel', True), \
            ('yrange', False), ('ylabel', True), \
            ('key', False), ('pointsize', True), ('style', False), \
            ('lmargin', False), \
            ('rmargin', False), \
            ('tmargin', False), \
            ('bmargin', False), \
            #   ('log', False) \
        ]

        self.command_add("set grid")
        self.command_add('set logscale x')

        for (option, quoted) in options:
            quote = ''
            if quoted:
                quote = '"'
            val = getattr(self, option, '')
            if val == None:
                continue
            if option == 'ylabel':
                self.command_add('set ' + option + ' ' + quote + str(val) + quote + ' offset 2')

            if isinstance(val, list):
                for i in val:
                    self.command_add('set ' + option + ' ' + quote + str(i) + quote)
            else:
                self.command_add('set ' + option + ' ' + quote + str(val) + quote)

        output_filename = self.filename + '.' + self.terminal.output_format

        self.command_add('set output "' + output_filename + '"')
        previous_crc32 = compute_file_crc32(folder + output_filename)

        self.command_add(plot)
        self.gnuplot_data.write(data)

        self.gnuplot_cmd.close()
        self.gnuplot_data.close()

        (status, data) = subprocess.getstatusoutput('cd ' + folder + '; gnuplot ' + self.filename + '.gplt')
        print(self.filename + ' = ' + str(status))
        #if status == 0 and self.removeTemporaryFiles:
        #    os.remove(dat_filename)
        #    os.remove(cmd_filename)

        updated = True
        if previous_crc32:
            new_crc32 = compute_file_crc32(folder + output_filename)
            if previous_crc32 == new_crc32:
                updated = False

        if hasattr(self.terminal, 'post_processing'):
            self.terminal.post_processing(folder + output_filename, updated)

