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

import v49File

##############################################################################
def v49F64p20(w1, w2):
    return ((w1 << 32) + w2)/(2**20)

##############################################################################
def v49F16p7(w, signed=0):
    v = (w & 0xffff)
    if signed and (w & 0x8000): v = v - 65536
    return v/(2**7)

##############################################################################
def v49SamplesGet(vp, dat):
    i = 0
    while i < (len(vp.data)-1):
        #print("Adding to dat.")
        d32 = vp.data[i]
        v = (d32 >> 16) & 0xffff
        if v >= 32768: v = v-65536
        dat.append(v)
        v = d32 & 0xffff
        if v >= 32768: v = v-65536
        dat.append(v)
        i = i+1

##############################################################################
def v49HdrShow(vp, prefix='', eol=0):
    if len(prefix): print(prefix,end='')
    print(format(vp.pktHeader,'04x'), \
        " TS="+str(vp.timeSec)+"."+\
        format(vp.timeFrac, '012d'), \
        " SID=", format(vp.streamId,'08x'),\
        " typ="+str(vp.pktType),\
        end='')
    if eol: print()

##############################################################################
def v49CtxShow(vp):
    v49HdrShow(vp, prefix=' CTX:')
    ctxIdctr = vp.data[0]
    #print('ctxIdctr=',hex(ctxIdctr))
    if (ctxIdctr & 0x7fffffff) == 0x29a08000:
        print(\
            " bw="+format(v49F64p20(vp.data[1], vp.data[2]),'0.3e'),\
            " frq="+format(v49F64p20(vp.data[3], vp.data[4]),'0.3e'),\
            " lvl="+format(v49F16p7(vp.data[5], signed=1),'0.3e'),\
            " gain="+format(v49F16p7(vp.data[6], signed=1),'0.3e'),\
            " rate="+format(v49F64p20(vp.data[7], vp.data[8]),'0.3e'),
            " evt/fmt="+format(vp.data[9],'08x')\
            )
    elif (ctxIdctr & 0x7fffffff) == 0x08800000:
        print(\
            " frq="+format(v49F64p20(vp.data[1], vp.data[2]),'0.3e'),\
            " gain="+format(v49F16p7(vp.data[3], signed=1),'0.3e'),\
            )
    else:
        print(" idctr="+format(ctxIdctr,'08x'),end="")
        for x in range(len(vp.data)):
            print(" ", format(vp.data[x],'08x'),end="")
        print()
    

##############################################################################
def v49DatShow(vp, nW=0):
    n = nW
    dLen=len(vp.data)
    tlr=vp.data[dLen-1]
    if n > len(vp.data): n = len(vp.data)
    v49HdrShow(vp, prefix=' DAT:')
    print(\
        " dLen="+str(dLen),\
        " tlr="+format(tlr,'08x'),\
        end='')
    for d in vp.data[0:n]: print(' '+format(d,'08x'), end='')
    print()

    # Save info to a file also
    #tstamp = str( vp.timeSec)+"."+format(vp.timeFrac,'012d')+" "
    #with open("/home/<user>/<some dir>/results/tstamps.txt","a+") as f:
    #    f.write(tstamp)

##############################################################################
def v49ExtractData(fNames, dat):
    idx1=0
    ch1 = chLst[idx1]
    f = [0 for x in range(1,12+1)]
    vp = [0 for x in range(1,12+1)]
    for ch in chLst:
        idx=chLst.index(ch)
        f[idx] = open(fNames[idx], 'rb')
        vp[idx] = v49File.v49FilePkt(f[idx], do16BitSwap, doEndianSwap)
        vp[idx].getNextPkt()
    doAnother = True
    while doAnother:
        for ch in chLst:
            idx=chLst.index(ch)
            if (vp[idx].timeFrac % 8000000) != 0:
                print("idx="+str(idx), \
                    " TS="+str(vp[idx].timeSec)+"."+ \
                    format(vp[idx].timeFrac, '012d'), \
                    " SID=", format(vp[idx].streamId,'08x'))
            if vp[idx].pktType == 1:
                v49DatShow(vp[idx], nW=0)
                v49SamplesGet(vp[idx], dat[idx])
            elif vp[idx].pktType == 4:
                v49CtxShow(vp[idx])

        for ch in chLst:
            idx=chLst.index(ch)
            if vp[idx].getNextPkt() == False: doAnother = False

##############################################################################
def v49ExtractData1(fName, dat):
    f = open(fName, 'rb')
    vp = v49File.v49FilePkt(f, do16BitSwap, doEndianSwap)
    vp.getNextPkt()
    doAnother = True
    while doAnother:
        if vp.pktType == 1:
            v49DatShow(vp, nW=0)
            v49SamplesGet(vp, dat)
        elif vp.pktType == 4:
            v49CtxShow(vp)
        if vp.getNextPkt() == False: doAnother = False

##############################################################################
def ddrExtractData1(fName, dat, idx, skip):
    f = open(fName, 'rb')
    doAnother = True
    f.read(idx * 4)
    while doAnother:
        try:
            w16 = struct.unpack('hh', f.read(4))
            dat.append(w16[0])
            dat.append(w16[1])
            f.read(skip * 4)
        except:
            doAnother = False

##############################################################################
def capExtractInit(cap10Gig):
    global do16BitSwap, doEndianSwap
    if cap10Gig:
        do16BitSwap = True      # Passed to v49File
        doEndianSwap = True     # Passed to v49File
    else:
        do16BitSwap = True      # Passed to v49File
        doEndianSwap = False    # Passed to v49File

