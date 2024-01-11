"""
The tunerApi module provides abstracted functions that generally map directly
to tuner commands and queries. Most commands require a socket parameter that
identifies the TCP/IP socket to which the tuner is connected. There are two
generic functions -- sendCmd and sendRcvQuery -- which are used for sending
general commands and queries, respectively.
"""
import socket
import time
import subprocess
import tcpLib
import b64
import base64

##############################################################################
def parmParseGetField(inStr, fldNum, mnemLen):
    """
    Return the response string from the specified field (comma separated).
    If the field does not exist, then None is returned. inStr contains the
    complete response from the tuner including the query mnemonic and any
    trailing characters. Leading and trailing spaces and control chars and
    any embedded spaces are first removed. mnemLen is the length of the
    mnemonic, which is also the index of the first char of the first response
    field. fldNum is the 0-based index of the response field.
    """
    err = 0
    if inStr==None or inStr == "": err = 1
    if not err:
        inStr = inStr.replace(" ","").strip()
        parmList = inStr[mnemLen:].split(',')
        if fldNum >= len(parmList): err = 1
    if err: return None
    else: return parmList[fldNum]

##############################################################################
def parmParseInt(inStr, fldNum, mnemLen, base=10):
    """
    Parse the specified response field as a decimal integer. If the field does
    not exist, or the field cannot be converted as an integer, then None is
    returned. mnemLen is the length of the mnemonic, which is also the index
    of the first char of the first response field. fldNum is the 0-based index
    of the response field.
    """
    parmStr = parmParseGetField(inStr, fldNum, mnemLen)
    try:
        return int(parmStr, base)
    except:
        return None

##############################################################################
def sendRcvQuery(sock, outStr, maxSize, timeFirst, timeBetween):
    """
    Send a query and receive the response. The query output string is sent
    exactly as given, so the caller must supply the ? and \\n if required.
    There are two associated timeouts  for the response. timeFirst is the
    timeout to the first character of a response, and timeBetween is a
    retriggerable timeout between receives of a multiple-receive response.
    maxSize is the limit on the the number of bytes allowed in a response.
    Additional bytes are not received and may still be in the TCP pipeline.
    Similarly, any bytes pending in the TCP pipeline at the time of the call
    will be treated as part of the response. The response is returned as a
    string, which is empty if no response is received.
    """
    tcpLib.tcpSend(sock, outStr.encode('utf-8'))
    inMsg = tcpLib.tcpRecv(sock, maxSize, timeFirst, timeBetween)

    if inMsg != None:
        #print('sendRcvQuery',inMsg)
        return inMsg.decode('utf-8')
    else:             return None

##############################################################################
def sendCmd(sock, outStr):
    """
    Send a string to the specified socket. The string will be sent exactly as it
    is specified, so the caller must include the trailing \\n if required.
    """
    tcpLib.tcpSend(sock, outStr.encode('utf-8'))

##############################################################################
def doCmd(sock, batch, cmdStr, outStr):
    """Process the current command string (outStr) and the accumulated command
    string (cmdStr) according to batch as follows:
    batch == 0: Send command to socket and return nothing
        if cmdStr == None:  command is outStr + \n
        otherwise           command is cmdStr + outStr + \n
    batch != 0: Return command string
        if outStr == None:  command string is cmdStr + \n
        otherwise:          command string is cmdStr + outStr + ;
    This routine is normally called internally via other commands. For batched
    command sequences, normal sequence is:
        doCmd(sock, batch=1, cmdStr='', outStr=FirstCommand)
        doCmd(sock, batch=1, cmdStr=accumCmd, outStr=NextCmd) ...
        doCmd(sock, batch=0, cmdStr=accumCmd, outStr=LastCommand)
    An alternate ending to the sequence would be:
        doCmd(sock, batch=1, cmdStr=accumCmd, outStr=LastCommand)
        doCmd(sock, batch=0, cmdStr=None, outStr=accumCmd)"""
    if batch == 0:
        if cmdStr==None:    sendCmd(sock, outStr + '\n')
        else:               sendCmd(sock, cmdStr + outStr + '\n')
    else:
        if outStr==None:    return cmdStr + '\n'
        else:               return cmdStr + outStr + ';'

##############################################################################
def memRead(sock, addr, width=4):
    """Read absolute memory address width=1, 2 or 4 (default) bytes."""
    if width in (1,2,4):
        inStr = sendRcvQuery(sock, \
            "$MEM1,{width},{addr}?\n".format(
            width=str(width), addr=format(addr, '08x')),
            5000, 3, 0.01)
        #print(inStr)
        val = parmParseInt(inStr, 3, 4, base=16)
        #print("val=",val)
    else:
        val = None
    return val

##############################################################################
def memWrite(sock, addr, data, width=4, batch=0, cmdStr=""):
    """Write absolute memory address width=1, 2 or 4 (default) bytes."""
    if width in (1,2,4):
        doCmd(sock, batch, cmdStr, "$MEM1,{width},{addr},{data}".format(
            width=str(width), addr=format(addr, '08x'),
            data=format(data, '08x')))

##############################################################################
def spiRead(sock, chan, dev, dOut):
    """Write to and Read from SPI device (see factory IDD)."""
    inStr = sendRcvQuery(sock, \
        "$SPI{chan},{dev},{dOut}?\n".format(
        chan=str(chan), dev=format(dev), dOut=format(dOut,'08x')),
        5000, 3, 0.01)
    #print(inStr)
    val = parmParseInt(inStr, 3, 4, base=16)
    #print("val=",val)
    return val

##############################################################################
def spiWrite(sock, chan, dev, dOut, batch=0, cmdStr=""):
    """Write to SPI device."""
    doCmd(sock, batch, cmdStr, "$SPI{chan},{dev},{dOut}".format(
        chan=str(chan), dev=format(dev), dOut=format(dOut,'08x')))

##############################################################################
def agc(sock, typ, ch, mode, cmdStr = "", batch=0):
    """ AGC... )"""
    return doCmd(sock, batch, cmdStr,
        "AGC{typ},{ch},{mode}".format(
            typ=str(typ), ch=str(ch), mode=str(mode)))

##############################################################################
def att(sock, tuner, atn, cmdStr = "", batch=0):
    """ATT..."""
    return doCmd(sock, batch, cmdStr, "ATT{tuner},{atn}".format(
        tuner=str(tuner), atn=str(atn)))

##############################################################################
def attQry(sock, chn):
    """Get the attenuation for the specified channel. """
    inStr = sendRcvQuery(sock, "ATT{chn}?\n".format(chn=str(chn)),
         5000, 3, 0.01)
    return parmParseInt(inStr, 1, 3)

##############################################################################
def bwt(sock, tuner, bw, cmdStr = "", batch=0):
    """ BWT... bandwidth given as code (1..4)"""
    return doCmd(sock, batch, cmdStr,
        "BWT{tuner},{bw}".format(tuner=str(tuner), bw=str(bw)))

##############################################################################
def bwtQry(sock, chn):
    """Get the bandwidth for the specified channel. """
    inStr = sendRcvQuery(sock, "BWT{chn}?\n".format(chn=str(chn)),
         5000, 3, 0.01)
    return parmParseInt(inStr, 1, 3)

##############################################################################
def csrQry(sock, typ, chn):
    """CSR query. Returns an integer status word. None is returned on error """
    inStr = sendRcvQuery(sock,
        "CSR{typ},{chn}?\n".format(
        typ=str(typ), chn=str(chn)),
         5000, 3, 0.01)
    return parmParseInt(inStr, 2, 3)

##############################################################################
""" Configure data path. The parms parameter is specific to the path type
and is an array of items. The items are converted to strings with comma
separators. If they are already strings, then conversion is actually
performed, but the separators are still inserted. """
def dpc(sock, pthTyp, pthNum, parms=[], cmdStr = "", batch=0):
    outS="DPC"+str(pthTyp)+","+str(pthNum)
    for i in parms: outS+=","+str(i)
    return doCmd(sock, batch, cmdStr, outS)

##############################################################################
def enc(sock, typ, ch, mode, cmdStr = "", batch=0):
    """ ENC (enable channel)..."""
    return doCmd(sock, batch, cmdStr,
        "ENC{typ},{ch},{mode}".format(
            typ=str(typ), ch=str(ch), mode=str(mode)))

##############################################################################
def frq(sock, typ, chnl, freq, cmdStr = "", batch=0):
    """FRQ typ, chnl, frq...; freq is given in MHz"""
    return doCmd(sock, batch, cmdStr, "FRQ{typ},{chnl},{freq}".format(
        typ=str(typ), chnl=str(chnl), freq=str(freq)))

##############################################################################
def frqQry(sock, typ, chn):
    """Get the frequency for the specified type/channel. """
    inStr = sendRcvQuery(sock, "FRQ{typ},{chn}?\n".format(
        typ=str(typ), chn=str(chn)),
         5000, 3, 0.01)
    return parmParseInt(inStr, 2, 3)

##############################################################################
def frt(sock, tuner, freq, cmdStr = "", batch=0):
    """FRT...; freq is given in MHz"""
    return doCmd(sock, batch, cmdStr, "FRT{tuner},{freq}".format(
        tuner=str(tuner), freq=str(freq)))

##############################################################################
def frtQry(sock, chn):
    """Get the frequency for the specified channel. """
    inStr = sendRcvQuery(sock, "FRT{chn}?\n".format(chn=str(chn)),
         5000, 3, 0.01)
    return parmParseInt(inStr, 1, 3)

##############################################################################
def mod(sock, typ, ch, mode, cmdStr = "", batch=0):
    """ MOD... bandwidth given as code (1..4)"""
    return doCmd(sock, batch, cmdStr,
        "MOD{typ},{ch},{mode}".format(
            typ=str(typ), ch=str(ch), mode=str(mode)))

##############################################################################
def ref(sock, typ, src, osc, pps, cmdStr = "", batch=0):
    """REF command. Set reference mode """
    return doCmd(sock, batch, cmdStr,
        "REF{typ},{src},{osc},{pps}".format(
        typ=str(typ), src=str(src), osc=str(osc), pps=str(pps)))

##############################################################################
def scrRead(sock, addr):
    """Read from specified SCR register."""
    inStr = sendRcvQuery(sock, "SCR{addr}?\n".format(
        addr=format(addr, '08x')),5000, 3, 0.01)
    val = parmParseInt(inStr, 1, 3, base=16)
    return val

##############################################################################
def scrWrite(sock, addr, data, batch=0, cmdStr=""):
    """Write to specified SCR register."""
    doCmd(sock, batch, cmdStr, "SCR{addr},{data}".format(
        addr=format(addr, '08x'), data=format(data, '08x')))

##############################################################################
def sge(sock, typ, chn, en, dwell=0, mode=0, cmdStr = "", batch=0):
    """SGE command. Stream Group enable """
    if mode == 0:
        return doCmd(sock, batch, cmdStr,
            "SGE{typ},{chn},{en},{dwell}".format(
            typ=str(typ), chn=str(chn), en=str(en),
            dwell=str(dwell)))
    else:
        return doCmd(sock, batch, cmdStr,
            "SGE{typ},{chn},{en},{dwell},{mode}".format(
            typ=str(typ), chn=str(chn), en=str(en),
            dwell=str(dwell), mode=str(mode)))

##############################################################################
def stbUtcSet(sock, tId, sec, uSec, cmdStr = "", batch=0):
    """STB command in UTC timer mode """
    return doCmd(sock, batch, cmdStr, "STB0,{tId},{sec},{uSec}".format(
        tId=str(tId), sec=str(sec), uSec=str(uSec)))

##############################################################################
def stbSwStrobe(sock, cmdStr = "", batch=0):
    """STB command in software strobe mode """
    return doCmd(sock, batch, cmdStr, "STB1, 3ff")

##############################################################################
def stc(sock, typ, chn, pthTyp, pthNum, upId=-1, cmdStr = "", batch=0):
    """ Set up a stream data connection between a generator (typ, chn) and a
    data path (pthTyp, pthNum). The stream ID (upper 16 bits) can be specified
    using upId.  """
    if upId >= 0: sufx = "," + format(upId,'04x');
    else:         sufx = ""
    return doCmd(sock, batch, cmdStr, "STC{typ},{chn},{pthTyp},{pthNum}{sfx}".format(
        typ=str(typ), chn=str(chn),
        pthTyp=str(pthTyp), pthNum=str(pthNum),
        sfx=sufx))

##############################################################################
def stcQry(sock, typ, chn):
    """STC query. Returns a triple of [pathTyp, pathNum, upId]. None is returned
    on error """
    inStr = sendRcvQuery(sock,
        "STC{typ},{chn}?\n".format(
        typ=str(typ), chn=str(chn)),
         5000, 3, 0.01)
    return [
        parmParseInt(inStr, 2, 3),
        parmParseInt(inStr, 3, 3),
        parmParseInt(inStr, 4, 3) ]

##############################################################################
def ste(sock, typ, chn, en, dwell=0, mode=0, cmdStr = "", batch=0):
    """STE command. Stream enable """
    if mode == 0:
        return doCmd(sock, batch, cmdStr,
            "STE{typ},{chn},{en},{dwell}".format(
            typ=str(typ), chn=str(chn), en=str(en),
            dwell=str(dwell)))
    else:
        return doCmd(sock, batch, cmdStr,
            "STE{typ},{chn},{en},{dwell},{mode}".format(
            typ=str(typ), chn=str(chn), en=str(en),
            dwell=str(dwell), mode=str(mode)))

##############################################################################
def steQry(sock, typ, chn):
    """STE query. Returns a double of [ en , dwell]. None is returned on error """
    inStr = sendRcvQuery(sock,
        "STE{typ},{chn}?\n".format(
        typ=str(typ), chn=str(chn)),
         5000, 3, 0.01)
    return [ parmParseInt(inStr, 2, 3) , parmParseInt(inStr, 3, 3) ]

##############################################################################
def syn(sock, typ, parms=[], cmdStr = "", batch=0):
    """SYN command. Send sync command type,value where value is an array of
    values, e.g., [1, 2, 3] """
    outS="SYN{typ}".format(typ=str(typ))
    for i in parms: outS+=","+str(i)
    return doCmd(sock, batch, cmdStr, outS)

##############################################################################
def synQry(sock, typ, synTyp):
    """SYN query. Returns sync value. None is returned on error, synTyp is
    a list (1, 2, 3...) """
    outS="SYN{typ}".format(typ=str(typ))
    for i in synTyp: outS += ","+str(i)
    outS += "?\n"
    inStr = sendRcvQuery(sock, outS, 5000, 3, 0.01)
    return parmParseInt(inStr, 1+len(synTyp), 3)

##############################################################################
def tmpQry(sock, sensor):
    """TMP query. Returns temperature in celsius.  None is returned
    on error."""
    inStr = sendRcvQuery(sock, "TMP{snr}?\n".format(snr=str(sensor)), 5000,3,0.01)
    return parmParseInt(inStr,1,3)

##############################################################################
def utc(sock, sec, cmdStr = "", batch=0):
    """UTC seconds"""
    return doCmd(sock, batch, cmdStr, "UTC{sec}".format(sec=str(sec)))

##############################################################################
def utcQry(sock):
    """UTC query. """
    inStr = sendRcvQuery(sock, "UTC?\n", 5000, 3, 0.01)
    #print(inStr, parmParseInt(inStr, 0, 3))
    return parmParseInt(inStr, 0, 3)

##############################################################################
def utcSync(sock):
    """Wait for a PPS roll over by polling UTC or time out trying (2 sec)"""
    tmOut = time.clock() + 2
    utc = utcQry(sock)
    while True:
        utc2 = utcQry(sock)
        if utc2 > utc:
            #print("utcSync utc="+str(utc)+" utc2="+str(utc2))
            break
        if time.clock() > tmOut:
            print("utcSync timeout time="+str(time.clock())+" tmOut="+str(tmOut))
            break

##############################################################################
def groupTunerDestroyAll(sock, cmdStr="", batch=0):
    """Destroy all coherent groups"""
    for i in range(1, 12):
        doCmd(sock, batch, cmdStr, "GRP2,1,{ch}".format(ch=str(i)))

##############################################################################
def groupCreate(sock, typ, chList, cmdStr = "", batch=0):
    return doCmd(sock, batch, cmdStr,
        "GRP 1,{typ},".format(typ=str(typ))
        + str(chList).translate({ord('[') : None, ord(']') : None }))

##############################################################################
def snapClear(sock, num):
    """Clear the specified snapshot buffer. This is a query, but we throw
    the response away """
    inStr = sendRcvQuery(sock,
        "DDO{chn},2,1,0?\n".format(chn=str(num)), 5000, 3, 0.01)

##############################################################################
def snapStatusGet(sock, num):
    """Get the status for the specified snapshot buffer. 0 means no data captured
    yet, 1 means some data, but not full, 2 means full """
    inStr = sendRcvQuery(sock, "DDO{path},0,0,0?\n".format(path=str(num)),
         5000, 3, 0.01)
    return parmParseInt(inStr, 1, 3)

##############################################################################
def snapUpload(sock, pathNum, nWords, filNam):
    """Upload a snapshot buffer to a file, including strippng the the B64 encoding
    so that a binary file results. nWords is the number of 32 bit words to upload"""
    # 4 chars for each 3 bytes, 4 bytes per word + header info chars
    maxSize = round((nWords * 16)/3 + 100);
    inStr = sendRcvQuery(sock, "DDO{path},2,{numW},0?\n".format(
        path=str(pathNum), numW=str(nWords)),
        maxSize, 3, 0.3)
    #print("Got " + str(nWords) + " words from path " + str(pathNum) )
    inStr = parmParseGetField(inStr, 6, 3)
    #outStr = b64.b64ToBytes(inStr)
    if inStr != None: outStr = base64.b64decode(inStr)
    else:             outStr = b''
    f = open(filNam, 'wb')
    f.write(bytes(outStr))
    f.close()

##############################################################################
def genCmd(sock, cmd, cmdStr = "", batch=0):
    """Send a generic command (not query) string """
    return doCmd(sock, batch, cmdStr, cmd)
