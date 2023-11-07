#!/usr/bin/env python3
verbose = True
cmds = [
    "*IDN?",
    "FID?",
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

import serial
import sys

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
    #print(responses)
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

ser = serial.Serial('/dev/ttyUSB0')
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
   sys.exit(f'Cannot open {ser.name}') 

#ser.timeout = 0.15

try:
    # make sure we're set for null terminated multiline responses, no acknowledgements
    ack4 = serCmd("ACK 4?")
    mlt4 = serCmd("MLT 4?")
    results={}
    res = serCmd("MLT 4,4,0; ACK 4,0")
    for cmd in cmds:
        res = serCmd(cmd)
        if res[0]==0:
            results[res[1]]=res[2:]
    for cmd in results.keys():
        print(f"{cmd} ==> {results[cmd]}")

finally:
    ser.close()
