"""
tcpLib contains primitive, abstracted functions for dealing with TCP/IP
sockets. The data interface is bytes, which are differnt than strings.
"""
import socket
import select
import time

##############################################################################
def dotQuad2List(ip):
    """Convert a 'dotted quad' string into a list (array) of four integers
    with the first component in list index 0."""
    print("IP=",ip)
    l = [0,0,0,0]
    for i in range(0,4):
        l[i] = int(ip.strip(" ").split(".")[i].strip(" "))
    return l

##############################################################################
def list2DotQuad(ip):
    """Convert a list (array) of four integers into a 'dotted quad' string
    with list index 0 corresponding to the first component of the quad."""
    return "{ip0}.{ip1}.{ip2}.{ip3}".format(\
        ip0=str(ip[0]), ip1=str(ip[1]), ip2=str(ip[2]), ip3=str(ip[3]))

##############################################################################
def tcpConnect(host, port):
    """host is a string (IP or name), port is an integer returns a socket"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    return s

##############################################################################
def tcpSend(sock, data):
  """Send data to socket. data is bytes not a string"""
  while data:
    sent = sock.send(data)
    data = data[sent:]

##############################################################################
def tcpRecvReady(sock, timeout):
    """Check for data available in socket. timeout is in ms. A value of -1 waits
    forever, 0 does not wait. Returns true if data available else false"""
    rdyLst, unused1, unused2 = select.select([sock], [], [], timeout)
    if rdyLst:
        return True
    else:
        return False
##############################################################################
def _tcpRxChkTerm(data, prevDat, term):
    """
    This function (private to this module) returns True if the message terminator
    is found, otherwise false. It checks the last char(s) of the most recent
    buffer so it will miss a terminator in the middle of the message. The last
    char(s) are checked against term (a character code). If term is 0, then it
    assumes that there is no terminator. If term > 256, then it will check for a
    two character sequence where the first char is multiplied by 8 and added to
    the second char. For example, a CR-LF pair has a term value 0x0d0a. """
    retVal = False
    if (term != 0) and (len(data) > 0):
        termDat = 0
        if term > 255:
            if len(data) < 2:
                if len(prevDat) > 0: termDat = prevDat[len(prevDat)-1]
            else:
                termDat = data[len(data)-2]
            termDat *= 256
        termDat += data[len(data)-1]
        if termDat == term: retVal = True
    return retVal

##############################################################################
def tcpRecv(sock, maxSize, timeFirst, timeBetween, term=0x0d0a):
    """Receive up to maxSize data from the socket. The timeouts are in ms.
    timeFirst is time to wait for first byte, timeBetween is the time to
    wait between receives (retriggerable). It returns bytes type or None
    if no data is received. term specifies a terminator that can also signal
    that the receive is done. It is set to CR-LF by default. Setting it to 0
    means that only timeouts are used see _tcpRxChkTerm for more information
    on the terminator value. """
    data = ''
    done = False
    if tcpRecvReady(sock, timeFirst):
        data = sock.recv(maxSize)
        done =  _tcpRxChkTerm(data, '', term)
        while (len(data) < maxSize) and not done:
            if tcpRecvReady(sock, timeBetween):
                d = sock.recv(maxSize - len(data))
                done =  _tcpRxChkTerm(d, data, term)
                data += d
            else:
                done = True
    if len(data) > 0: return data
    else:             return None
