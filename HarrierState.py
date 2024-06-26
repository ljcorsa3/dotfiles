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
required = [
    "#CDT?",
    "#COP?",
    "#CSN?",
    "#MAC 3?",
    "#MDL?",
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

    ser = openSerial(port)
    fd = openFile(filename)

    ser.timeout = 0.30

    dev_settings={}
    success=True

    # extract
    if args['extract']:
        # query each command in list
        # add new dictionary entry with command as key, response as data
        # write dictionary to file as JSON 
        for cmd in cmds:
            if verbose:
                print(f"{me}: extracting '{cmd}' response",file=sys.stderr)
            res = serCmd(cmd)
            if res[0]==0:
                dev_settings[res[1]]=res[2:]
                if verbose:
                    print(res,file=sys.stderr)
            else:
                success=False
        if success:
            if verbose:
                print(f"{me}: writing settings to {fd.name} as JSON",file=sys.stderr)
            json.dump(dev_settings, fd)
            if verbose:
                print(f"{me}: extracted the following settings:",file=sys.stderr)
                print(json.dumps(dev_settings, indent = 2),file=sys.stderr)
        else:
            sys.exit(f"{me}: error extracting command dev_settings:\n{dev_settings}")

    # restore or reset
    if args['restore'] or args['reset']:
        # read dictionary from existing JSON file
        # unlock unit with password (serial number)
        # place unit into CFG mode 
        # optionally wipe NVRAM
        # 
        # send command (dictionary data) to 

        try:
            dev_settings = json.load(fd)
        except json.decoder.JSONDecodeError:
            sys.exit(f"{me}: cannot parse input {fd.name}")
        if verbose:
            print(f"{me}: sending the following settings:",file=sys.stderr)
            print(json.dumps(dev_settings, indent = 2),file=sys.stderr)

        # send password 
        if verbose:
            print(f"{me}: sending password",file=sys.stderr)
        csn = str(dev_settings['#CSN?'][0]).split()[-1]
        res = serCmd(f"PWD DRS{csn}")
        if res[0] != 0:
            sys.exit(f"{me}: attempt to use '{res[1]}' failed\n")

        # enter configuration mode
        if verbose:
            print(f"{me}: entering CFG mode",file=sys.stderr)
        res = serCmd("CFG 1")

        if args['reset']:
            if verbose:
                print(f"{me}: clearing NVRAM",file=sys.stderr)
            res = serCmd("#EED 1")

        # restore previous settings
        for cmd in dev_settings.keys():
            # if resetting, only send required settings
            if args['reset'] and cmd not in required:
                continue
            # if restoring, send everything
            if cmd[0] == '#':
                setting=';'.join(dev_settings[cmd])
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
        fd.close()

#-------------------------------------------------------------------------------
#---  functions  ---------------------------------------------------------------
#-------------------------------------------------------------------------------

def openSerial(port):
    global ser
    ser = serial.Serial(port)
    ser.baudrate = 115200
    ser.timeout = 0.5

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
    return

def serCmd(cmd):
    global me
    global ser
    global verbose

    # set default response list
    # first value is ESR value.  -1 if no ESR found
    responses = [ 0, cmd ]

    # pyserial doesn't give a definitive way to know when done, so
    # chase every command/query with a known unique (benign simple quick safe) query
    # that is not already part of the command
    added_query = None
    added_query_list = [ '*ESR?', '*STB?', '*SRE?', '*ESE?', 'FUA?', 'UTC?' ]
    for q in added_query_list:
        # use first choice not in cmd
        if cmd.upper().count(q) == 0:
            added_query = q
            break
    if added_query == None:
        sys.exit(f"{me}: command contains all of {', '.join(added_query_list)}"

    # send command and extra query
    binary_cmd=f"{cmd}; {added_query}\r".encode('utf-8')
    nw = ser.write(binary_cmd)

    # set a longer timeout for certain commands to complete
    timeout = 1
    for slow in [ "#REF", "#COP", "#DFM" ]:
        if cmd.upper().count(slow) > 0:
            timeout = 120

    # read lines until we get an echo of our command string
    # (including the additional query string)
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
            if str(r).strip().find(added_query) >= 0:
                found=True
    if not found:
        responses[0]= -1
        return responses

    # response will have space instead of '?'
    added_query_response = re.sub(r'\?',r' ',added_query).upper()
    # read lines until we see our expected response
    # ESR response is guaranteed to be present, so capture that especially
    esr = -1
    added_response_found = -1
    found = False
    t0 = time.monotonic()
    while not found and (time.monotonic() - t0) < timeout:
        time.sleep(0.06)
        line = ser.readline()
        if len(line) == 0:
            continue
        line = re.sub('[,]?(\000|\r|\n)*$','',line.decode()).strip()
        # split response into semicolon separated stanzas
        stanzas = line.strip().split(';')
        for i in range(len(stanzas)):
            resp = stanzas[i]
            if str(resp).find('ESR ') >= 0:
                esr = int(str(resp)[4:])
            if str(resp).find(added_query_response) >= 0:
                added_response_found = i
                found=True
            if added_response_found < 0:
                # trim string, clean up nulls, add to return val
                s = re.sub(r'\000',r'\r\n',str(resp).strip())
                responses.append(s)
    if not found:
        responses[0] = -1
    if esr > 0:
        responses[0] = esr
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
            help='extract settings from harrier at serial port')
    group.add_argument('--restore','-w', action='store_true', \
            help='restore settings to harrier at serial port')
    group.add_argument('--reset', action='store_true', \
            help='wipe NVRAM and restore default settings to harrier at serial port')
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
    #res = serCmd("#EED 1")
    #res = serCmd("CFG 0")
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
        if args['restore']:
            if not os.isatty(0):
                fd = sys.stdin
                if verbose:
                    print(f"{me}: reading from {fd.name}",file=sys.stderr)
            else:
                print(f"{me}: cannot read from terminal")
                exit(1)
        else:
            fd = sys.stdout
            if verbose:
                print(f"{me}: writing to {fd.name}",file=sys.stderr)
    else:
        # file arg.  if reading, must exist
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
    return fd

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
    sys.exit(0)

# vim: nu
