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

    # chase every command/query with *ESR?
    bcmd=f"{cmd}; *ESR?\n".encode('utf-8')
    expected = "*ESR "
    """
    # special case responses from PWD and CFG1
    if re.search(r'(?i)[ ]*PWD',cmd) != None:
        expected = "alid Password - System"
    elif re.search(r'(?i)[ ]*CFG[ ]*1',cmd) != None:
        expected = " bytes into NvSRAM"
    """

    # send it
    nw = ser.write(bcmd)
    time.sleep(0.06)

    # read lines until we get en echo of our command
    found = False
    while not found:
        line = ser.readline()
        line = re.sub('[,]?(\000|\r|\n)*$','',line.decode()).strip()
        resp = line.strip().split(';')
        for i in range(len(resp)):
            r = resp[i]
            #print(str(r).strip())
            if str(r).strip().find('*ESR?') >= 0:
                found=True
    # read lines until we see our expected response
    esr = -1
    esri = -1
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
                esri = i
            if esri < 0:
                # trim string, clean up nulls, add to return val
                s = re.sub(r'\000',r'\r\n',str(r).strip())
                responses.append(s)
            if str(r).find(expected) >= 0:
                found=True
    if esr>0:
        responses[0]=esr
    return responses

#n = serCmd('PWD DRS00015'); print(n)
n = serCmd('*idn?'); print(n)
n = serCmd('cfg1;#cop2; fid?; cfg 0'); print(n)
n = serCmd('PWD password; cap?; *esr?'); print(n)
n = serCmd('cfg1;#cop2; cfg 0'); print(n)

