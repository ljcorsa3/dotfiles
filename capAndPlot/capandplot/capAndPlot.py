#!/usr/bin/env python
###############################################################################
#                           capAndPlot.py:
# Captures and plots data from one or more channels on one or more Vespers.
#   It executes in a loop with each iteration capturing one pass of over
#   all defined channels. The script is parameterized by importing a python
#   module that you would edit for your setup (see capParms at the start of
#   the main() function).
# Each iteration does the following:
#   1. Captures data from each channel into files (one per channel)
#   2. Extracts the data from the files and plots them in time and  FFT.
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

from capCapture import *
from capExtract import *
from capPlot import *

# ctlSockLst:
#   is the array of control sockets for the various tuners. It is declared
#   in capCapture and initialized by one of the capCapture_Init functions.
#   There is one entry per unit (i.e., it is the length of unitIps). It can
#   be used to perform additional unit initialization or per-iteration control.

##############################################################################
def capSetup():

    # Capture parameters depend on what capture type is used.
    if cap10Gig:
        capCapture10gInit(chLst, unitIps, filePrefix, keepAllFiles, chType, \
            pcIp, vitaPort, StopStartStream, n10GigPackets)
    else:
        capCaptureNot10gInit(chLst, unitIps, filePrefix, keepAllFiles, chType, \
            captRawType, capMode, capSize, fixV49Swap)

    # Plotting consists of extracting the data and the plotting the results
    if cap10Gig: 
        raw = False
        capExtractInit(cap10Gig)
    else:        
        raw = captRawType != 0
        capExtractInit(fixV49Swap)
    capPlotInit(chLst, plotTime, plotFft, plotTimeSkip, plotTimeLen, \
        isIq, rate, raw)

##############################################################################
def main():
    err = 0

    # Setup for capture/plot processing.
    exec("from capParms import *", globals())
    capSetup()

    # Main loop. Each iteration captures one set of data (could be multiple
    # channels) and plots it.
    loopCnt = 0
    while loopCnt < nIter:
        err = capOneIteration(loopCnt, flush=capFlush)
        if not err:
            plotOneIteration(loopCnt, waitBetweenPlots)
        if waitBetweenLoops > 0.0: time.sleep(waitBetweenLoops)
        loopCnt += 1
        err = 0

if __name__ == "__main__":
    main()
