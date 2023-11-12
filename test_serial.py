#!/usr/bin/env python3

import serial
import sys, os, stat, time
import argparse
from pathlib import Path
import json
import re

port = '/dev/ttyUSB0'
ser = serial.Serial(port)
ser.baudrate = 115200
ser.timeout = 0.3

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

ser.write("MLT 4,4,0\r".encode('utf-8'))
lines = ser.readlines()

def serCmd(cmd, check=True):
    global me
    global ser
    global verbose

    responses = [ 0, cmd ]

    # chase every command/query with a known unique query
    for q in [ '*ESR?', '*STB?', '*SRE?', '*ESE?' 'FUA?', 'UTC?' ]:
        # use first choice not in cmd
        if cmd.upper().count(q) == 0:
            xtra_q = q
            break
    # response will have space instead of '?'
    xtra_r = re.sub(r'\?',r' ',xtra_q).upper()
    """
    # special case responses from PWD and CFG1
    if re.search(r'(?i)[ ]*PWD',cmd) != None:
        expected = "alid Password - System"
    elif re.search(r'(?i)[ ]*CFG[ ]*1',cmd) != None:
        expected = " bytes into NvSRAM"
    """

    # send it
    bcmd=f"{cmd}; {xtra_q}\r".encode('utf-8')
    nw = ser.write(bcmd)
    time.sleep(0.06)

    # read lines until we get an echo of our added query
    found = False
    while not found:
        line = ser.readline()
        if len(line) == 0:
            time.sleep(0.06)
            continue
        line = re.sub('[,]?(\000|\r|\n)*$','',line.decode()).strip()
        resp = line.strip().split(';')
        for i in range(len(resp)):
            r = resp[i]
            #print(str(r).strip())
            if str(r).strip().find(xtra_q) >= 0:
                found=True
    # read lines until we see our expected response
    esr = -1
    found_i = -1
    found = False
    while not found:
        line = ser.readline()
        if len(line) == 0:
            time.sleep(0.06)
            continue
        #print(f"line: {line}")
        line = re.sub('[,]?(\000|\r|\n)*$','',line.decode()).strip()
        resp = line.strip().split(';')
        for i in range(len(resp)):
            r = resp[i]
            if str(r).find('ESR ') >= 0:
                esr = int(str(r)[4:])
            if str(r).find(xtra_r) >= 0:
                found_i = i
                found=True
            if found_i < 0:
                # trim string, clean up nulls, add to return val
                s = re.sub(r'\000',r'\r\n',str(r).strip())
                responses.append(s)
    if esr>0:
        responses[0]=esr
    return responses

#n = serCmd('PWD DRS00015'); print(n)
n = serCmd('*idn?'); print(n)
n = serCmd('cfg1;#cop2; *esr?; cfg 0'); print(n)
n = serCmd('PWD password; fid?; *esr?'); print(n)
n = serCmd('cfg1;#cop2; cfg 0'); print(n)

