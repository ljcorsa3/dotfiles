#!/usr/bin/env python
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

import numpy
from matplotlib import pyplot
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

from capExtract import *
from capCapture import capFileNamesMake

# The time and fft lists are created for each plot set (call to one plot
# cycle) and represent the time and fft data, for each channel (indexed
# sequentially in chLst order). The timeList is either real or complex
# depending on isIq. The fftList elements are (freq[], phase[]) tuples,
# but phase is None for real FFTs.
timeList=[]
fftList=[]

##############################################################################
def fftCompute(isIq, dat, rate):
    # Perform an FFT based on the data, whether it is real or complex and
    # the data rate (to create the freq axis)
    l = len(dat)
    wdw = numpy.blackman(l)
    if isIq:
        #print("fftCompute IQ samples.")
        fft1 = numpy.fft.fft(wdw*dat)
        freqAxis = numpy.fft.fftfreq(l, d=1/rate)[0:len(fft1)]
        fft1a = 20*numpy.log10(numpy.abs(fft1/(32768*numpy.sum(wdw))))
        phase = numpy.angle(fft1)
        return (freqAxis, fft1a, phase)
    else:
        #print("fftCompute real data.")
        fft1 = numpy.fft.rfft(wdw*dat)
        freqAxis = numpy.fft.rfftfreq(l, d=1/rate)[0:len(fft1)]
        fft1a = 20*numpy.log10(numpy.abs(fft1*2/(32768*numpy.sum(wdw))));
        phase = numpy.angle(fft1)
        return (freqAxis, fft1a, phase)

##############################################################################
# Finds the frequency(s) of the peak amplitude(s) of the given FFT and returns
# the an array of (freq, ampl) tuples. For FFTs of real data (isIq=False) the
# array has only a single element. For FFTs of complex data, there are two --
# a frequency above 0 and a frequency below 0. idxOfst can be used to exclude
# a region (specified in samples) around DC.
def freqPeak(fft, rate, isIq, idxOfst=0):
    if isIq:
        pkIdx1 = numpy.argmax(fft[idxOfst:int(len(fft)/2-1)]) \
            + idxOfst
        f1 = pkIdx1 * rate/(len(fft))
        v1 = fft[pkIdx1]
        pkIdx2 = numpy.argmax(fft[int(len(fft)/2):len(fft)-idxOfst-1]) \
            + int(len(fft)/2)
        f2 = pkIdx2 * rate/(len(fft)) - rate
        v2 = fft[pkIdx2]
        return [(f1, v1), (f2, v2)]
    else:
        pkIdx = numpy.argmax(fft[idxOfst:]) + idxOfst
        f = pkIdx * rate/(2*(len(fft)-1))
        v = fft[pkIdx]
        return [(f, v)]

##############################################################################
def printFreqPeak(fft, rate, isIq):
    # Print the peak frequency and corresponding spectrum value in the FFT.
    # for complex fft, print two peaks" positive and and negative freqs.
    peaks = freqPeak(fft, rate, isIq)
    for (f,v) in peaks:
        print('f=', format(f, '15.7e'), ' v=', format(v,'7.3f'))

##############################################################################
def plotFileGroup(capFile, nCh, waitBetweenPlots):
    global fftList, timeList
    nPlotsX = 1
    nPlotsY = 0
    if plotFft:  nPlotsY += 1
    if plotTime: nPlotsY += 1
    if isIq:     nPlotsX += 1

    dat = [[] for ch in range(0,nCh)]

    fftList = []
    timeList = []

    # Extract the data portions of the V49 snapshot capture
    # v49ExtractData(capFile, dat)
    for idx in range(0,nCh):
        if captRaw:
            # Extract the data
            chWrdIdx = 0
            for idx2 in range(0,nCh):
                ddrExtractData1(capFile[0], dat[idx2], \
                   chWrdIdx, nCh-1)
                chWrdIdx += 1
        else:
            v49ExtractData1(capFile[idx], dat[idx])
    pyplot.clf()
    pyplot.ioff()
    print()
    nPlots = 0
    for d in dat:
        print("len d="+str(len(d)))
        if len(d) > 0:
            if isIq:
                # I and Q are interleaved starting with I
                dI = d[0::2]
                dQ = d[1::2]
                dd = numpy.complex64(dI + \
                    numpy.complex64(1j) * numpy.complex64(dQ))
            else:
                dd = d
            timeList.append(dd)
            if plotTime:
                # Time domain plots
                if plotTimeLen > 0: dLen = plotTimeLen
                else:               dLen = len(d)
                if isIq:
                    pyplot.subplot(nPlotsX, nPlotsY, 1)
                    pyplot.plot(dI[plotTimeSkip:dLen-1],'.')
                    pyplot.subplot(nPlotsX, nPlotsY, 1+nPlotsY)
                    pyplot.plot(dQ[plotTimeSkip:dLen-1],'.')
                else:
                    pyplot.subplot(nPlotsX, nPlotsY, 1)
                    pyplot.plot(range(plotTimeSkip, dLen-1),d[plotTimeSkip:dLen-1],'-')
                    print("maxVal,min=", str(max(d)),str(min(d)))
                nPlots += 1
            if plotFft:
                # FFT plots
                (freqAxis, fft1a, phase) = fftCompute(isIq, dd, rate)
                if isIq:
                    pyplot.subplot(nPlotsX, nPlotsY, nPlotsY)
                    pyplot.plot(freqAxis, fft1a)
                    pyplot.subplot(nPlotsX, nPlotsY, 2*nPlotsY)
                    #pyplot.plot(numpy.unwrap(phase))
                    pyplot.plot(numpy.unwrap(numpy.angle(dd)))
                else:
                    pyplot.subplot(nPlotsX, nPlotsY, 2)
                    pyplot.plot(freqAxis, fft1a)
                    pkIdx = numpy.argmax(fft1a)
                printFreqPeak(fft1a, rate, isIq)
                fftList.append((fft1a, phase))
                nPlots += 1
    if nPlotsX > 0 and nPlotsY > 0 and nPlots > 0:
        print("Redraw...")
        pyplot.draw()
        pyplot.show(block=waitBetweenPlots)
        pyplot.pause(0.001)
        print("Draw done")

##############################################################################
def plotOneIteration(loopCnt, waitBetweenPlots):
    capFile = capFileNamesMake(chLst, loopCnt)
    plotFileGroup(capFile, len(chLst), waitBetweenPlots)

##############################################################################
def capPlotFftGet(idx):
    return fftList[idx]

##############################################################################
def capPlotDataGet(idx):
    return timeList[idx]

##############################################################################
def capPlotInit(cList, pltTime, pltFft, pltTimeSkip, pltTimeLen, \
    iq, pltRate, raw):
    global      plotTime, plotFft, plotTimeSkip, plotTimeLen
    global      isIq, rate, captRaw
    global      chLst
    plotTime     = pltTime
    plotFft      = pltFft
    plotTimeSkip = pltTimeSkip
    plotTimeLen  = pltTimeLen
    isIq         = iq
    rate         = pltRate
    chLst        = cList
    captRaw = raw
