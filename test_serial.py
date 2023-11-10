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
ser.timeout = 0.5

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
    q=cmd.count('?')
    if q>0:
        q=cmd.find('?')
        if q>0:
            cmd1=cmd[0:q]
    foundCmd=False
    foundResp=False
    bcmd=f"{cmd}; *ESR?\n".encode('utf-8')
    nw = ser.write(bcmd)
    time.sleep(0.06)
    expected = "*ESR "
    if re.search(r'(?i)[ ]*PWD',cmd) != None:
        expected = "alid Password - System"
    elif re.search(r'(?i)[ ]*CFG[ ]*1',cmd) != None:
        expected = " bytes into NvSRAM"

    # read back lines until timeout
    while not foundCmd:
        line = ser.readline()
        line = re.sub('[,]?(\000|\r|\n)*$','',line.decode()).strip()
        resp = line.strip().split(';')
        for r in resp:
            print(str(r).strip())
            if str(r).strip().find('*ESR?') >= 0:
                foundCmd=True
    while not foundResp:
        line = ser.readline()
        line = re.sub('[,]?(\000|\r|\n)*$','',line.decode()).strip()
        resp = line.strip().split(';')
        for r in resp:
            print(str(r).strip())
            if str(r).find(expected) >= 0:
                foundResp=True
    return responses

n = serCmd('MLT 4,4,0; fid?')

