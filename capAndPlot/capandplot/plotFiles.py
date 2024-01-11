#!/usr/bin/env python
###############################################################################
#                           plotFiles.py:
# Plots data from a list of files that were captured before.
# The script is parameterized by importing a python module that you would edit
#   to describe what/how to plot. See the exec(... import ...) in main().
###############################################################################
import sys
import getopt
import socket
import time
import datetime
import subprocess
import struct
import csv
import array
import ctypes
import select
import argparse as arg

###############################################################################
import os,pathlib
if sys.path[0] == '':
    try:
        script_dir = str(pathlib.Path(__file__).parent.resolve())
    except:
        script_dir = os.environ["HOME"] + "/capAndPlot/capandplot"
else:
    script_dir=sys.path[0]

lib_dir = str(pathlib.Path(f"{script_dir}/../mylib").resolve())
sys.path.insert(1, lib_dir)
sys.path.insert(1, script_dir)
del script_dir
del lib_dir

from capPlot import *

##############################################################################
def plotSetup():

    cList = [ [0,i] for i in range(0,len(names))]
    # Plotting consists of extracting the data and the plotting the results
    capExtractInit(cap10Gig)
    if cap10Gig: raw = False
    else:        raw = captRaw
    capPlotInit(cList, plotTime, plotFft, plotTimeSkip, plotTimeLen, \
        isIq, rate, raw)

##############################################################################
def parseCommand(argv):
    global names
    global filePath
    global plotTime
    global plotFft
    global plotTimeSkip
    global plotTimeLen
    global isIq
    global rate
    global waitBetweenPlots
    global aPrs
    global args

    # Setup for capture/plot processing.
    exec("from plotFilesParms import *", globals())

    aPrs = arg.ArgumentParser()
    aPrs.add_argument("file_name", nargs='*',
        help='input file. Multiple files allowed')
    aPrs.add_argument('-f','--no-fft', dest='no_fft', action='store_true',
        help='no FFT plot')
    aPrs.add_argument('-l','--length', dest='length', type=int, default=plotTimeLen,
        help='length (number of samples) to plot')
    aPrs.add_argument('-p','--path', default=filePath,
        help='path prefix for input files')
    aPrs.add_argument('-s','--skip', dest='skip', type=int, default=plotTimeSkip,
        help='number of samples to skip')
    aPrs.add_argument('-t','--no-time', dest='no_time', action='store_true',
        help='no time plot')
    aPrs.add_argument('-r','--rate', dest='rate', type=float, default=rate,
        help='sample rate to assume')
    aPrs.add_argument('-R','--real', dest='real',  action='store_true',
        help='plot as real data (otherwise complex)')
    aPrs.add_argument('-w','--wait', dest='wait', action='store_true',
        help='wait between plots and plot files separately')

    args = aPrs.parse_args()
    print(args)

    filePath = args.path
    plotTime = False if args.no_time else plotTime
    plotFft  = False if args.no_fft else plotFft
    plotTimeSkip = args.skip
    plotTimeLen = args.length
    isIq = False if args.real else isIq
    rate = args.rate
    waitBetweenPlots = True if args.wait else waitBetweenPlots
    names = args.file_name
    filePath = args.path



##############################################################################
def main(argv):
    err = 0

    print('testing')

    parseCommand(argv)
    for nm in names: print(filePath+nm)
    print('plotTime        : '+str(plotTime        ))
    print('plotFft         : '+str(plotFft         ))
    print('plotTimeSkip    : '+str(plotTimeSkip    ))
    print('plotTimeLen     : '+str(plotTimeLen     ))
    print('isIq            : '+str(isIq            ))
    print('rate            : '+str(rate            ))
    print('waitBetweenPlots: '+str(waitBetweenPlots))

    plotSetup()

    fNames = [ filePath+n for n in names]
    if waitBetweenPlots:
        for nm in fNames:
            plotFileGroup([nm], 1, True)
    else:
        plotFileGroup(fNames, len(names), True)

if __name__ == "__main__":
    main(sys.argv[1:])
