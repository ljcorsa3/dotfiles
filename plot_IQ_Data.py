#!/usr/bin/env python3

""" set DDC center frequency and sampling rate, bandwidth of interest
"""
Fc = 15.0e6
sampling_rate = 6400e3
bw = 20e3

""" import a bunch of libraries (most unused here)
"""
import argparse, pdb, sys, os, platform, scipy, scipy.signal
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import re
from numpy import log10, abs, pi, sin, cos, exp, linspace, amax, amin, around
from numpy import rint, blackman, real, imag, cumsum, absolute
from numpy import array, shape
from numpy.random import normal, rand
from scipy.signal import firwin, remez, freqz, hilbert, decimate, lfilter, filtfilt
from matplotlib.pyplot import rcParams, tight_layout, gca, figure, show, subplot
from matplotlib.pyplot import psd, plot, specgram
from matplotlib import rc
from scipy.signal import chirp
from pathlib import Path


p=Path(__file__)
me=str(p)
mydir=str(p.parent.resolve())

parser = argparse.ArgumentParser(prog=me, description='IQ data plotter')
parser.add_argument('-v','--verbose', help='increase verbosity of output' , action='store_true')
parser.add_argument('files', metavar='files',nargs='+')
args = vars(parser.parse_args())
#print(args); exit(1)

""" load csv file, convert columns to complex
"""
for filename in args['files']:
    csvdata = np.loadtxt(filename,
            delimiter=',',
            usecols=(0,1))
    IQdata = csvdata.astype(np.float32).view(np.complex64).flatten()
    IQdata /= 2**24 # crude scaling
    del csvdata

    """ set up matplotlib figure
    """
    fig, (ax1,ax2,ax3) = plt.subplots(3,1)
    #fig.suptitle('IQ_Data')
    fig.set_size_inches(12, 10)
    fig.set_dpi(96)
    fig.tight_layout(pad=3)

    """ plot four packets of I/Q data as magnitude
    """
    ax1.plot(abs(IQdata[0:2047]))
    ax1.title.set_text('Mag v Sample')
    ax1.set_ylabel('Mag')
    ax1.set_xlabel('Sample')

    """ plot the power spectral density
    """
    npts = 2**11  # play with npts as you get more data points
    ax2.psd(IQdata, Fs=sampling_rate, NFFT=npts, window=blackman(npts))
    ax2.title.set_text('PSD')
    ax2.set_xlabel('Frequency')
    #ax2.set_ylim(-140,0)
    #ax2.set_xlim(-1.2*bw, 1.2*bw)

    """ plot the spectrogram
    """
    npts = 2**10
    ax3.specgram(IQdata, Fc=Fc, Fs=sampling_rate, NFFT=npts, window=blackman(npts),
            noverlap=npts/2, scale_by_freq=True)
    ax3.title.set_text('Spectrogram')
    ax3.set_ylabel('Frequency')
    ax3.set_xlabel('Time(s)')
    ax3.set_ylim(Fc-1.2*bw, Fc+1.2*bw)

    """ finally, show the figure
    """
    show()
