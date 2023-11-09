#!/usr/bin/env python3
cmds = [
    "*IDN?",
    "FID?",
    "CAP?",
    ]
"""
    "#AGS 1?", "#AGS 2?", "#AGS 3?", "#AGS 4?",
    "#BIT?",
    "#BND 1?", "#BND 2?", "#BND 3?", "#BND 4?",
    "#CDT?",
    "#COP?",
    "#CSN?",
    "#DDP?",
    "#DFM?",
    "#ETH 1?", "#ETH 3?",
    "#FLT?",
    "#IPC?",
    "#KAT 1?", "#KAT 2?", "#KAT 3?", "#KAT 5?", "#KAT 6?", "#KAT 7?", "#KAT 8?", "#KAT 9?", "#KAT 10?", "#KAT 11?",
    "#MAC 1?", "#MAC 3?",
    "#MDL?",
    "#MLT 1?", "#MLT 2?", "#MLT 3?", "#MLT 4?", "#MLT 5?", "#MLT 6?", "#MLT 7?", "#MLT 8?", "#MLT 9?", "#MLT 10?", "#MLT 11?",
    "#MSD?",
    "#REF?",
    "#RTV?",
    "#SID?",
    "#SRR?",
    "#UDP?",
    "#VSI?",
    "#VUI?",
    "#WPM?",
]
"""

import serial
import sys, os, stat
import argparse
from pathlib import Path
import json

#-------------------------------------------------------------------------------
def serCmd(cmd, check=True):
    global ser
    global verbose
    bcmd=f"{cmd}\n".encode('utf-8')
    nw = ser.write(bcmd)
    echo = ser.readline()
    responses = [ 0, cmd ]
    if cmd.count('?')>0:
        lines = ser.readlines()
        for line in lines:
            resp = line.decode().strip().split('\0')
            responses += resp
    if check:
        resp = serCmd("*ESR?", False)
        resp1 =  resp[-1].split(" ")[-1]
        esr=int(resp1)
        if esr!=0:
            responses[0] = esr
            if esr & 4:
                print(f"Command {cmd} caused Query error")
            elif esr & 8:
                resp = serCmd("DDE?", False)
                resp1 =  resp[-1].split(" ")[-1]
                dde = int(resp1)
                print(f"Command {cmd} caused Device Dependent Error {resp}")
            elif esr & 16:
                print(f"Command {cmd} caused Execution error")
            elif esr & 32:
                print(f"Command {cmd} caused Command error")
    if check and verbose:
        print(responses)
        #for resp in responses:
            #print(resp)
    return responses

#-------------------------------------------------------------------------------

p=Path(__file__)
me=str(p)
mydir=str(p.parent.resolve())

file = None
port = None
verbose = False

parser = argparse.ArgumentParser(description='Save/Restore Harrier default settings')
parser.add_argument('--port',"-p", action = 'store', nargs=1, required=False,\
        help='full path to serial port device')
parser.add_argument('--file','-f', action = 'store', nargs = 1, required=False, \
        help = 'saved file')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--extract','-r', action='store_true', \
        help='extract default settings from harrier at serial port')
group.add_argument('--restore','-w', action='store_true', \
        help='restore default settings to harrier at serial port')
parser.add_argument('--verbose','-v',
        help='increase verbosity of output' , action='store_true')
parser.add_argument('options', metavar='files',nargs='*',
        help='[PORT] [FILE]')
args = vars(parser.parse_args())

print(f"{me}: args = {args}")
if args['verbose']:
    verbose = True

# first try to get file and port from specific argument
if args['port'] != None:
    port = args['port']
if args['file'] != None:
    file = args['file']
if file != None and port != None:
    if len(args['options'])>0:
        print(f"{me}: Don't need optional arguments",file=sys.stderr)
        parser.print_usage()
        exit(1)
else: # check options to detect file and port existence/type
    for f in args['options']:
        if file == None and f == '-':
            file = '-'
            continue
        try:
            mode = os.stat(f).st_mode
            if port==None and stat.S_ISCHR(mode):
                port=f
                args['options'].remove(f)
            elif file==None and stat.S_ISREG(mode):
                file=f
                args['options'].remove(f)
        except FileNotFoundError:
            pass
# port has to exist, file does not, so use missing file anyway
if port != None and file == None and args['restore']:
    for f in args['options']:
        if f != _port:
            file = f
            args['options'].remove(f)
            break

# see if we have a port
if port == None:
    print(f"{me}: Need --port/-p argument or optional argument",file=sys.stderr)
    parser.print_usage()
    exit(1)

breakpoint()
# see if we have a real file arg required for read
if args['extract'] and file != '-':
    try:
        mode = os.stat(file).st_mode
        if not stat.S_ISREG(mode):
            print(f"{me}: file {file} is not a file",file=sys.stderr)
            parser.print_usage()
            exit(1)
    except FileNotFoundError:
        print(f"{me}: file {file} cannot be found",file=sys.stderr)
        parser.print_usage()
        exit(1)

try:
    # see if we have a file
    if file == None or file == '-':
        stdio = True
        if args['extract']:
            if not os.isatty(0):
                fd = sys.stdin
                if verbose:
                    print(f"{me}: reading from stdin",file=sys.stderr)
            else:
                print(f"{me}: cannot read from terminal")
                exit(1)
        elif args['restore']:
            if not os.isatty(1):
                fd = sys.stdout
                if verbose:
                    print(f"{me}: writing to stdout",file=sys.stderr)
        else:
            print(f"{me}: need --file/-f argument or optional argument",file=sys.stderr)
            parser.print_usage()
            exit(1)
    else:
        stdio = False
        if args['extract']:
            fd = open(file,"r")
        else:
            fd = open(file,"w")

    breakpoint()
    ser = serial.Serial(port)
    ser.baudrate = 115200
    ser.timeout = 0.4

    try:
        ser.open()
    except serial.SerialException:
        ser.close()
        ser.open()
        ser.write("*CLS; DDE?; DDE?\n".encode('utf-8'))
        ser.readlines() # throw away anything pending

    if not ser.isOpen():
        sys.exit(f'{me}: cannot open {ser.name}',file=sys.stderr)

    ser.timeout = 0.20

    # make sure we're set for null terminated multiline responses, no acknowledgements
    results={}
    res = serCmd("MLT 4,4,0; ACK 4,0")
    for cmd in cmds:
        res = serCmd(cmd)
        if verbose:
            print(res,file=sys.stderr)
        if res[0]==0:
            results[res[1]]=res[2:]
    if verbose:
        for cmd in results.keys():
            s='\n    '.join(results[cmd])
            print(f"{cmd} ==> {s}",file=sys.stderr)
    json.dump(results, fd)
    results = json.load(fd)
finally:
    ser.close()
    if not stdio:
        close(fd)

# vim: nu
