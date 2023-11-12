#!/usr/bin/env python3
import serial
import sys, os, stat, time
import argparse
from pathlib import Path
import json
import re

filename = None
port = None
verbose = False
args={}
fd=None

cmds = [
    "*IDN?", "FID?", "CAP?",
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
        if verbose: print(f"{me}: opening serial port {port}",file=sys.stderr)
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

        # make sure we're set for null terminated multiline responses, no acknowledgements,
        # clear status
        try:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            time.sleep(0.06)
            if verbose:
                print(f"{me}: sending initial commands to device",file=sys.stderr)
            ser.write("MLT 4,4,0; ACK 4,0; *ESR?; DDE?; *CLS\n".encode('utf-8'))
            time.sleep(0.06)
            ser.readlines() # throw away anything pending
        except serial.serialutil.SerialException as e:
            sys.exit(f"{me}: comms with {ser.name} failed. {e}")

        ser.timeout = 0.30

        results={}
        success=True
        # extract
        if args['extract']:
            for cmd in cmds:
                if verbose:
                    print(f"{me}: extracting '{cmd}' response",file=sys.stderr)
                res = serCmd(cmd)
                if res[0]==0:
                    results[res[1]]=res[2:]
                    if verbose:
                        print(res,file=sys.stderr)
                else:
                    success=False
            if success:
                json.dump(results, fd)
                if verbose:
                    print(f"{me}: extracted the following settings:",file=sys.stderr)
                    print(json.dumps(results, indent = 2),file=sys.stderr)
            else:
                sys.exit(f"{me}: error extracting command results:\n{results}")
        #restore
        else:
            try:
                results = json.load(fd)
            except json.decoder.JSONDecodeError:
                if stdio:
                    sys.exit(f"{me}: cannot parse input")
                else:
                    sys.exit(f"{me}: cannot parse input file '{filename}'")
            if verbose:
                print(f"{me}: sending the following settings:",file=sys.stderr)
                print(json.dumps(results, indent = 2),file=sys.stderr)

            # enter configuration mode
            if verbose: print(f"{me}: sending password",file=sys.stderr)
            csn = str(results['#CSN?'][0]).split()[-1]
            res = serCmd(f"PWD DRS{csn}")

            if verbose: print(f"{me}: entering CFG mode",file=sys.stderr)
            res = serCmd("CFG 1")
            for cmd in results.keys():
                if cmd[0] == '#':
                    setting=';'.join(results[cmd])
                    if verbose:
                        print(f"{me}: sending '{setting}'",file=sys.stderr)
                    res = serCmd(setting)
                    if verbose:
                        print(res,file=sys.stderr)
            # exit configuration mode
            res = serCmd("CFG 0")
            print(f"YOU MUST POWERCYCLE UNIT FOR SETTINGS TO BECOME EFFECTIVE!",file=sys.stderr)

    finally:
        ser.close()
        if not stdio:
            fd.close()

#-------------------------------------------------------------------------------
#---  functions  ---------------------------------------------------------------
#-------------------------------------------------------------------------------

def serCmd(cmd):
    global me
    global ser
    global verbose

    responses = [ 0, cmd ]

    # pyserial doesn't give a definitive way to know when done, so
    # chase every command/query with a known unique (benign simple quick safe) query
    # that is not already part of the command
    for q in [ '*ESR?', '*STB?', '*SRE?', '*ESE?' 'FUA?', 'UTC?' ]:
        # use first choice not in cmd
        if cmd.upper().count(q) == 0:
            xtra_q = q
            break
    timeout = 1
    for slow in [ "#REF", "#COP", "#DFM" ]:
        if cmd.upper().count(slow) > 0:
            timeout = 120

    # send command and extra query
    bcmd=f"{cmd}; {xtra_q}\r".encode('utf-8')
    nw = ser.write(bcmd)

    # read lines until we get an echo of our added query
    found = False

    t0 = time.monotonic()
    while not found and (time.monotonic() - t0) < 1:
        time.sleep(0.06)
        line = ser.readline()
        if len(line) == 0:
            continue
        line = re.sub('[,]?(\000|\r|\n)*$','',line.decode()).strip()
        resp = line.strip().split(';')
        for i in range(len(resp)):
            r = resp[i]
            if str(r).strip().find(xtra_q) >= 0:
                found=True
    if not found:
        responses[0]= -1
        return responses

    # read lines until we see our expected response
    # response will have space instead of '?'
    xtra_r = re.sub(r'\?',r' ',xtra_q).upper()
    esr = -1
    found_xtra = -1
    found = False
    t0 = time.monotonic()
    while not found and (time.monotonic() - t0) < timeout:
        time.sleep(0.06)
        line = ser.readline()
        if len(line) == 0:
            continue
        line = re.sub('[,]?(\000|\r|\n)*$','',line.decode()).strip()
        resp = line.strip().split(';')
        for i in range(len(resp)):
            r = resp[i]
            if str(r).find('ESR ') >= 0:
                esr = int(str(r)[4:])
            if str(r).find(xtra_r) >= 0:
                found_xtra = i
                found=True
            if found_xtra < 0:
                # trim string, clean up nulls, add to return val
                s = re.sub(r'\000',r'\r\n',str(r).strip())
                responses.append(s)
    if not found:
        responses[0]= -1
    if esr>0:
        responses[0]=esr
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
    parser.add_argument('--port',"-p", action = 'store', required=False,\
            help='full path to serial port device')
    parser.add_argument('--file','-f', action = 'store', required=False, \
            help = 'saved file')
    parser.add_argument('--verbose','-v',
            help='increase verbosity of output' , action='store_true')
    parser.add_argument('options', metavar='files',nargs='*',
            help='[PORT] [FILE]')
    args = vars(parser.parse_args())

    if args['verbose']:
        print(f"{me}: args = {args}",file=sys.stderr)
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
    else:
        # check options to detect file and port existence/type
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

    return

#-------------------------------------------------------------------------------
def openFile(filename):
    global me
    global verbose
    global args

    fd = None
    if filename == None or filename == '-':
        # no file, check to see if stdio still terminal (if so, fail)
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
            fd = sys.stdout
            if verbose:
                print(f"{me}: writing to stdout",file=sys.stderr)
    else:
        # file arg.  if reading, must exist
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
            try:
                fd = open(filename,"r")
            except:
                sys.exit(f"{me}: cannot open file {filename} for reading")
        else:
            try:
                fd = open(filename,"w")
            except:
                sys.exit(f"{me}: cannot open file {filename} for writing")
    return [ fd, stdio ]

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
    sys.exit(0)

# vim: nu
