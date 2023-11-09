#!/usr/bin/env python3
import serial
import sys, os, stat, time
import argparse
from pathlib import Path
import json

filename = None
port = None
verbose = False
args={}
fd=None

cmds = [
    "*IDN?",
    "FID?",
    "CAP?",
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
#-------------------------------------------------------------------------------
def main():
    global me
    global verbose
    global args
    global filename
    global port
    global cmds
    global ser

    # get me, a name I call myself
    p=Path(__file__)
    me=str(p.stem)
    mydir=str(p.parent.resolve())

    parseArgs()

    ser = serial.Serial(port)
    ser.baudrate = 115200
    ser.timeout = 0.5
    fd, stdio = openFile(filename)

    try:
        if verbose:
            print(f"{me}: opening serial port {port}",file=sys.stderr)
        try:
            ser.open()
        except serial.SerialException:
            ser.close()
        try:
            ser.open()
        except serial.SerialException:
                sys.exit(f'{me}: cannot open {ser.name}')
        if not ser.isOpen():
            sys.exit(f'{me}: cannot open {ser.name}')

        if verbose:
            print(f"{me}: sending initial commands to device",file=sys.stderr)
        ser.write("MLT 4,4,0; ACK 4,0; *ESR?; DDE?; *CLS\n".encode('utf-8'))
        ser.readlines() # throw away anything pending

        ser.timeout = 0.30

        # make sure we're set for null terminated multiline responses, no acknowledgements
        results={}
        success=True
        if args['extract']:
            for cmd in cmds:
                res = serCmd(cmd)
                if verbose:
                    print(res,file=sys.stderr)
                if res[0]==0:
                    results[res[1]]=res[2:]
                else:
                    success=False
            if verbose:
                for cmd in results.keys():
                    s='\n    '.join(results[cmd])
                    print(f"{cmd} ==> {s}",file=sys.stderr)
            if success:
                json.dump(results, fd)
                if verbose:
                    print(json.dumps(results, indent = 2),file=sys.stderr)
            else:
                sys.exit(f"{me}: error extracting command results:\n{results}")
        else:
            try:
                results = json.load(fd)
            except json.decoder.JSONDecodeError:
                if stdio:
                    sys.exit(f"{me}: cannot parse input")
                else:
                    sys.exit(f"{me}: cannot parse input file '{filename}'")
            if verbose:
                pass#print(json.dumps(results, indent = 2),file=sys.stderr)
            for cmd in results.keys():
                if cmd[0] == '#':
                    print(f"sending: '{''.join(results[cmd])}'",file=sys.stderr)
                else:
                    pass#print(f"not sending: {str(results[cmd])}",file=sys.stderr)

    finally:
        ser.close()
        if not stdio:
            fd.close()

#-------------------------------------------------------------------------------
def serCmd(cmd, check=True):
    global me
    global ser
    global verbose

    responses = [ 0, cmd ]
    bcmd=f"{cmd}\n".encode('utf-8')
    nw = ser.write(bcmd)
    time.sleep(0.1)
    # if query, ready back response
    lines = ser.readlines()
    if cmd.find('?')>0:
        for line in lines:
            resp = line.decode().strip().split('\0')
            if str(resp[0]).find(cmd) == -1:
                responses += resp
    # avoid bottomless recursion!
    if check and not cmd.strip().upper() in [ "*ESR?", "DDE?" ]:
        resp = serCmd("*ESR?", False)
        resp1 =  resp[-1].split(" ")[-1]
        esr=int(resp1)
        if esr!=0:
            responses[0] = esr
            if esr & 4:
                print(f"{me}: command '{cmd}' caused Query error",file=sys.stderr)
            elif esr & 8:
                resp = serCmd("DDE?", False)
                resp1 =  resp[-1].split(" ")[-1]
                dde = int(resp1)
                print(f"{me}: command '{cmd}' caused Device Dependent Error {dde}",file=sys.stderr)
            elif esr & 16:
                print(f"{me}: command '{cmd}' caused Execution error",file=sys.stderr)
            elif esr & 32:
                print(f"{me}: command '{cmd}' caused Command error",file=sys.stderr)
    return responses

#-------------------------------------------------------------------------------
def parseArgs():
    global me
    global verbose
    global args
    global filename
    global port

    parser = argparse.ArgumentParser(description='extract or restore Harrier default settings')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--extract','-r', action='store_true', \
            help='extract default settings from harrier at serial port')
    group.add_argument('--restore','-w', action='store_true', \
            help='restore default settings to harrier at serial port')
    parser.add_argument('--port',"-p", action = 'store', nargs=1, required=False,\
            help='full path to serial port device')
    parser.add_argument('--file','-f', action = 'store', nargs = 1, required=False, \
            help = 'saved file')
    parser.add_argument('--verbose','-v',
            help='increase verbosity of output' , action='store_true')
    parser.add_argument('options', metavar='files',nargs='*',
            help='[PORT] [FILE]')
    args = vars(parser.parse_args())

    print(f"{me}: args = {args}",file=sys.stderr)
    if args['verbose']:
        verbose = True

    # first try to get file and port from specific argument
    if args['port'] != None:
        port = args['port']
    if args['file'] != None:
        filename = args['file']
    if filename != None and port != None:
        if len(args['options'])>0:
            parser.print_usage()
            sys.exit(f"{me}: Don't need optional arguments")
    else: # check options to detect file and port existence/type
        for f in args['options']:
            if filename == None and f == '-':
                filename = '-'
                continue
            try:
                mode = os.stat(f).st_mode
                if port==None and stat.S_ISCHR(mode):
                    port=f
                elif filename==None and stat.S_ISREG(mode):
                    filename=f
            except FileNotFoundError:
                print(f"{me}: cannot find '{f}'",file=sys.stderr)
                pass
    if port in args['options']:
        args['options'].remove(port)
    if filename in args['options']:
        args['options'].remove(filename)

    #print(f"parseArgs: filename={filename} port={port}",file=sys.stderr)
    # port has to exist, file does not, so use missing file anyway
    if port != None and filename == None and args['extract']:
        for f in args['options']:
            if f != port:
                filename = f
                break

    # see if we have a port
    if port == None:
        parser.print_usage()
        sys.exit(f"{me}: Need --port/-p argument or optional argument")
    print(f"parseArgs 2: filename={filename} port={port}",file=sys.stderr)

    return

#-------------------------------------------------------------------------------
def openFile(filename):
    global me
    global verbose
    global args

    fd = None
    if filename == None or filename == '-': # no file, check to see if stdio still terminal (if so, fail)
        stdio = True
        if args['restore']:
            if not os.isatty(0):
                fd = sys.stdin
                if verbose:
                    print(f"{me}: reading from stdin",file=sys.stderr)
            else:
                print(f"{me}: cannot read from terminal")
                exit(1)
        else:
            if not os.isatty(1):
                fd = sys.stdout
                if verbose:
                    print(f"{me}: writing to stdout",file=sys.stderr)
    else: # file arg.  if reading, must exist
        stdio = False
        if args['restore']: # see if we have a real file arg required for read
            try:
                mode = os.stat(filename).st_mode
                if not stat.S_ISREG(mode):
                    print(f"{me}: file {filename} is not a file",file=sys.stderr)
                    parser.print_usage()
                    exit(1)
            except FileNotFoundError:
                parser.print_usage()
                sys.exit(f"{me}: file {filename} cannot be found")
            fd = open(filename,"r")
        else:
            fd = open(filename,"w")
    return [ fd, stdio ]

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main())

# vim: nu
