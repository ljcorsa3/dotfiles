import sys
import socket
import time
import parms
sys.path.insert(0, '../mylib')
import tcpLib
import tunerApi
from myUtils import bytesToInt
from udpCapBin import UdpCapPkt, UdpCapture

##############################################################################
def streamExistCheck(sIdList, fileName):
    """Parse a capture file and check for existence of streams in sIdList"""
    fail = 0
    f = open(fileName, 'rb')
    f.seek(0)
    pkt = UdpCapPkt(f, start=0)
    pktCount = {x:0 for x in sIdList}
    for pkt in pkt:
        sId = bytesToInt(pkt.data, start=1*4, num=4)[0]
        if sId in pktCount:
            pktCount[sId] += 1
        else:
            print("Unknown stread ID", hex(sId))
    for sId, cnt in pktCount.items():
        print(hex(sId), cnt)
        if cnt < 1:
            print("** zero packets on SID", hex(sId))
            fail += 1
    f.close()
    if fail > 0:
        for sId, cnt in pktCount.items(): print(hex(sId), cnt)
    return fail

##############################################################################
def sipIdxtGet(quad, fpga):
    """Return the entry index to use for SIP cmd based on quad/fpga-b"""
    return (quad-1)*4 + (fpga-1)*2 + 1

##############################################################################
def stcTeardownQuadSide(sock, quad, fpga_b):
    """ Tear all stream on this half (fpga_b) of the quad"""
    scxDef=[
        #(NumItems per FPGA, sId for first item on quad)
        (36, 1),    #DDC
        (2, 0xa1),  #Demod
        (2, 0x81),  #WB real
        (2, 0x89),  #WB complex
        (2, 0xa9)]  #HF
    scxBase = (quad-1)*0x100
    limits = []
    for sDef in scxDef:
        scxMin = scxBase+(fpga_b-1)*sDef[0]+sDef[1]
        limits.append((scxMin, scxMin+sDef[0]-1))
    tunerApi.stcTeardownAll(sock, limits=limits),
    return

##############################################################################
def fpgaBModeSet(sock, quad, b, mode, force=False):
    """ Ensure FPGA-B is in the specified mode and put it in that mode if it
    is not. If force is True, then don't check, just force the mode set"""
    crntMode = 0
    if not force:
        crntMode = tunerApi.fldQry(sock, quad, b)
    if force or (mode != crntMode):
        crntMode = tunerApi.fpgaBLoad(sock, quad, b, mode)
        if mode != crntMode:
            raise Exception("Failed to set FPGA-B mode")

##############################################################################
def fpgaBModeCheck(sock, quad, b, mode, pollDly=0.1, retry=20):
    """Poll for FPGA-B in the specified mode. Returns True if it is in that
    mode (within timeout), else false. Timeout is specified by the pollDelay
    (delay between polls) and the retry count."""
    done = False
    while not done:
        crntMode = tunerApi.fldQry(sock, quad, b)
        if mode == crntMode:
            done = True
        else:
            time.sleep(pollDly)
            if retry > 0:
                retry = retry - 1
                if retry <= 0: done = True
    if mode == crntMode: return True
    else:                return False

