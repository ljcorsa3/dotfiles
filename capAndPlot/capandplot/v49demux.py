#!/usr/bin/env python
###############################################################################
#                               v49demux.py
# Demultiplex a VITA-49 multi-stream file. It separates stream in a V49 capture
# file (inFile) into output files (outFile) with one stream per file.
#   python3 [-h] v49demux.py input [options]
# where:
#   input is the input file including path
# Output files are named as outPath/outNm-streamId.ext, where outNm is the name
#   portion of output (w/o extenstion) and ext is the extension of output.
#   streamId is the 8 hex digit stream ID. By default output is the same input
# Use -h or --help for other options
###############################################################################
import os
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

# For 10gE V49 parsing
do16BitSwap = True
doEndianSwap = True

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

# Include V49 file access/parse
import v49File as v49

##############################################################################
# Open and add a new file for the specified stream. Add it to the streams
# dictionary.
def addStreamFile(sId, name, strms):
    # If name not given, then create an auto-name
    if len(name) == 0:
        (nm, ext) = os.path.splitext(outName)
        name = nm+'-'+format(sId,'08x')+ext
    outNm = outPath+name
    print("SID=", format(sId,'08x')+": "+outNm)
    outFl = open(outNm, 'wb')
    strms.update({sId : (outFl, outNm)})

##############################################################################
def main(argv):
    err = 0
    global outStrm
    global outName
    global outPath
    global inPath
    global inName
    global timeRange
    global streamIds

    aPrs = arg.ArgumentParser()
    aPrs.add_argument("in_file",
        help='input file with path')
    aPrs.add_argument('-o','--out_file',
        help='output file base name with path')
    aPrs.add_argument('-t','--time_range', nargs=2, type=float,
        help='specify range of times "start stop" times (-1 for ignored)')
    aPrs.add_argument('-i','--stream_ids', nargs='*', type=lambda x: int(x,0),
        help='specify list of stream ids (use 0x for hex. Defaults to all)')
    args = aPrs.parse_args()
    #print(args)
    #exit(0)

    # Break input file name into name and path portions.
    (path, inName) = os.path.split(args.in_file)
    if len(path) > 0 and path[len(path)-1] != '/': path += '/'
    inPath = path

    # if (optional) output base is specified, use it, otherwise, use the input
    # base. The output can include a full name (path/name.ext). The name is used
    # as a base to which stream IDs are added for each stream. inPath is used of
    # no outPath is given and inName is used as the base if no outName is given.
    if args.out_file:
        (path, outName) = os.path.split(args.out_file)
        if len(path) == 0:             outPath = inPath
        elif path[len(path)-1] != '/': outPath = path + '/'
        else:                          outpath = path
    else:
        outPath = inPath
        outName = inName

    # Use the time range if specified, or set it to ignored (all)
    if args.time_range: timeRange = args.time_range
    else:               timeRange = [-1, -1]

    # Use the stream ID list specified, or set it to empty ( output all)
    if args.stream_ids: streamIds = args.stream_ids
    else:               streamIds = []

    # Empty the output stream/file dictionary and open the input file for V49
    # packet processing
    outStrm = {}
    inNm = inPath+inName
    inFl = open(inNm, 'rb')
    vp = v49.v49FilePkt(inFl, do16BitSwap, doEndianSwap)

    doAnother = vp.getNextPkt()
    while doAnother:
        sId = vp.streamId
        #print("SID=", format(sId,'08x')+" len="+str(vp.pktLength))
        inRange = True
        tPkt = vp.timeSec + vp.timeFrac/1e12
        if timeRange[0] >= 0 and tPkt < timeRange[0]: inRange = False
        if timeRange[1] >= 0 and tPkt > timeRange[1]: inRange = False
        if inRange:
            # Add packet to output stream. If stream file is already open
            # then use it. Otherwise decide if it is to kept.
            if sId in outStrm:
                fOut = outStrm[sId][0]
            else:
                # if no ID list was given, or if the packet is in the
                # specified list, then capture it.
                if len(streamIds) < 1 or sId in streamIds:
                    addStreamFile(sId, '', outStrm)
                    fOut = outStrm[sId][0]
                else :
                    fOut = None
            if fOut != None: vp.pktWrite(fOut)
        doAnother = vp.getNextPkt()

    inFl.close()
    for i in outStrm:
        fOut = outStrm[i][0]
        fOut.close()

if __name__ == "__main__":
    main(sys.argv[1:])
