#!/bin/bash

gnuplot $1.gplt
epstopdf $1.ps
pdftk $1.pdf cat 1-1right output $1.2.pdf
mv $1.2.pdf $1.pdf

