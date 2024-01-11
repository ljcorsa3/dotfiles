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
import os
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


import tcpLib
import tunerApi
import v49File

ctlSockLst=[]
tenGigSock = 0

CTL_PORT = 8081

##############################################################################
def connect(ip):
    """setup the connection to the unit. It uses the global CTL_PORT as the
    port, and it returns sock for the socket connection."""
    print("Trying connection to : " + ip + ":" + str(CTL_PORT))
    sock = tcpLib.tcpConnect(ip, CTL_PORT)
    return sock

##############################################################################
def udpRcvRdy(sock, nRetry, timeOut):
    """Chedk if the specified UDP socket has a receive packet pending. The
    maximum of time to wait is approximately nRetry*timeOut (less accurate
    with decreasing timeOut). These parameters can be interpreted as setting
    the polling resolution. timeOut is in floating seconds (see select).
    Returns true if a packet is ready. """
    if nRetry <= 0: nRetry = 1
    for i in range(0, nRetry):
        rdy, unused1, unused2 = select.select([sock], [], [], timeOut)
        if len(rdy)!=0:
            break
    return len(rdy)!=0

##############################################################################
def udpRcvFlush(sock, nRetry, timeOut, timeOut1=-1):
    """Flush pending UDP receive packets. nRetry sets an upper limit in the
    number of packets to fush (so we don't do it forever) and timeOut is the
    time (floating seconds) to wait for each packet. timeOut1, if not 0, is
    used to set the time to wait for the first packet and would usually be
    much larger than timeOut (time for subsequent packets). Returns True
    if a packet is pending after the flush. """
    if nRetry <= 0: nRetry = 1
    if timeOut1 < 0: timeOut1=timeOut
    rdy =  udpRcvRdy(sock, 1, timeOut1)
    for i in range(0, nRetry):
        if not rdy:
            break
        sock.recv(10)
        rdy =  udpRcvRdy(sock, 1, timeOut)
    return rdy

##############################################################################
def capFileNamesMake(chLst, loopCnt):
    capFileName = []
    capNameBase = filePrefix
    if keepAllFiles: capNameBase += format(loopCnt,'04x')
    capFileNames = ["" for ch in range(0,len(chLst))]
    for ch in chLst:
        fName = capNameBase \
            +"d"+str(ch[0])\
            +"."+str(ch[1])\
            +".bin"
        capFileNames[chLst.index(ch)] = fName;
    return capFileNames

##############################################################################
def capMakeStdV49(inFname, outFname):
    fIn = open(inFname, 'rb')
    fOut = open(outFname, "wb")
    vp = v49File.v49FilePkt(fIn, True, False)
    vp.getNextPkt()
    doAnother = True
    while doAnother:
        vp.pktWrite(fOut)
        if vp.getNextPkt() == False: doAnother = False

##############################################################################
def capOneIteration(loopCnt, flush=False):
    err = 0
    global capFile, dat
    dat = []
    capFile = capFileNamesMake(chLst, loopCnt)
    if cap10Gig: #############################################################
        if flush: udpRcvFlush(tenGigSock, 10000, 0.01)
        for ch in chLst:
            capBuff = bytes(0)
            sock = ctlSockLst[ch[0]]
            if StopStartStream:
                #Enable stream in timed snapshot mode and collect data
                tunerApi.ste(sock, chType, ch[1], 1, 0)
            if udpRcvRdy(tenGigSock, 500, 0.01):
                #print("UDP rcv is ready")
                for i in range(0, n10GigPackets):
                    # Capture a packet, put it in the buffer, repeat
                    try:
                        tmpData = tenGigSock.recv(9000)
                        capBuff += tmpData
                        #print(str(i)+": new="+str(len(tmpData))+" ttl="+str(len(capBuff)))
                    except socket.timeout:
                        pass
                        print("data recv timed out after packet "+str(i))
                        break
            if StopStartStream:
                # disable the stream and then read any pending data from
                # the socket
                tunerApi.ste(sock, chType, ch[1], 0, 0)
                udpRcvFlush(tenGigSock, 1000, 0.01)
            dat.append([])
            fName = capFile[chLst.index(ch)]
            capFile.append(fName)
            tmpFile = open(fName, 'wb')
            tmpFile.write(capBuff)
            #print("buffer length = ",len(capBuff))
            tmpFile.close()
    else: # not 10gE. #########################################################
        if err == 0:
            if captRawType == 1: # Raw JESD
                if len(chLst) == 1 and chType == 1:
                    ch = chLst[0]
                    sock = ctlSockLst[ch[0]]
                    tunerApi.dpc(sock, 2, 13, [format(ch[1],'d')])
                else:
                    err = 2
                    print("captRawJesd only allows one wideband channel")
            elif captRawType == 2: # Raw DDR
                capMap = 0
                for ch in chLst:
                    capMap |= 1 << (ch[1]-1)
                    sock = ctlSockLst[ch[0]]
                tunerApi.dpc(sock, 2, 14, [format(capMap,'x'), round(capSize)])
            print("Waiting for data ...")
            for ch in chLst:
                sts = 0
                retry = 100
                sock = ctlSockLst[ch[0]]
                while (sts == 0) and (retry > 0):
                    if captRawType == 1: # Raw JESD
                        sts = tunerApi.snapStatusGet(sock, 13)
                    elif captRawType == 2: #Raw DDR
                        sts = tunerApi.snapStatusGet(sock, 14)
                    else: #not raw (type==0)
                        sts = tunerApi.snapStatusGet(sock, ch[1])
                    if sts != 2:
                        retry -= 1
                        time.sleep(0.01)
                if sts == 0:
                    print("Unit "+str(ch[0])+" chnl "+str(ch[1])+\
                        " not ready. sts="+str(sts))
                    err = 1
        if err == 0:
            # Upload snapshots from all channel streams
            # Create arrays of capture file names and data arrays.
            dat = [[] for ch in range(0,len(chLst))]
            # Upload the snapshot from every channel to a corresponding file
            for ch in chLst:
                sock = ctlSockLst[ch[0]]
                fName = capFile[chLst.index(ch)]
                if captRawType == 1: # raw JESD
                    tunerApi.snapUpload(sock, 13, round(capSize/2), fName)
                elif captRawType == 2: # raw DDR
                    tunerApi.snapUpload(sock, 14, round(capSize/2), fName)
                else: # not raw (type=0)
                    tunerApi.snapUpload(sock, ch[1], capSize, fName)
                    if captRawType == 0 and fixV49Swap: #reformat Vesper 49 to 10gE
                        tmpName = fName+".tmp"
                        os.rename(fName, tmpName)
                        capMakeStdV49(tmpName, fName)
                        os.remove(tmpName)
    return err

##############################################################################
def capCaptureNameInit(fPrefix, keep, tenGig):
    global filePrefix, keepAllFiles, cap10Gig

    filePrefix = fPrefix
    keepAllFiles = keep
    cap10Gig = tenGig

##############################################################################
def capCaptureCmnInit(cList, ips, fPrefix, keep, tenGig, cType):
    global chLst, unitIps, filePrefix, keepAllFiles
    global cap10Gig, chType

    capCaptureNameInit(fPrefix, keep, tenGig)
    chLst = cList
    unitIps = ips
    chType = cType

    # Connect to the units involved
    for i in range(0, len(unitIps)):
        sock = connect(unitIps[i])
        ctlSockLst.append(sock)

##############################################################################
def capCapture10gInit(cList, ips, fPrefix, keep, cType,
    pcIp, vitaPort, stopStart, nPkts):

    global StopStartStream, n10GigPackets
    global tenGigSock

    capCaptureCmnInit(cList, ips, fPrefix, keep, True, cType)
    StopStartStream = stopStart
    n10GigPackets = nPkts

    # Setup the 10Gig params
    tenGigSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("Binding socket to " + str(pcIp[0]) + ":" + str(vitaPort))
    tenGigSock.bind((pcIp[0], vitaPort))
    tenGigSock.settimeout(5)
    print("Setup 10Gig port on IP " + pcIp[0] + ":" + str(vitaPort))

##############################################################################
def capCaptureNot10gInit(cList, ips, fPrefix, keep, cType, \
    rawType, cMode, cSize, fixSwap):

    global captRaw, capMode, capSize, captRawType, fixV49Swap

    capCaptureCmnInit(cList, ips, fPrefix, keep, False, cType)
    capMode = cMode
    capSize = cSize
    captRaw = rawType != 0 # rawType=0 is not raw (i.e., is V49)
    captRawType = rawType  # rawType (JESD or DDR)
    fixV49Swap = fixSwap # Fix byte/word swap in Vesper V49 cap files

    if captRawType == 0: # not raw
        for ch in chLst:
            sock = ctlSockLst[ch[0]]
            tunerApi.dpc(sock, 2, ch[1],[capMode])    
    elif captRawType == 1: # raw JESD
        if len(chLst) == 1 and chType == 1:
            ch = chLst[0]
            sock = ctlSockLst[ch[0]]
            tunerApi.dpc(sock, 2, 13, [ch[1]])  
        else:
            err = 2
            print("captRawJesd only allows one wideband channel")
    elif captRawType == 2: #raw DDR; Nothing to do
        pass
    else:
        print("Unknown captRawType")
        err = 3

