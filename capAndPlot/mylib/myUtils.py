import struct

##############################################################################
def bytesToInt(data, big=True, nBytes=4, start=0, num=-1):
    """Return a range of bytes in data (bytearray) as an array of integers of
    the type specified by big and nBytes. big True mean big endian. nBytes
    specifies the number of bytes and can be +/- 1, 2, 4 or 8. Negative
    values of nBytes mean signed, otherwise they are unsigned. start and
    num specify the range (0-based) in the data array where num < 0 means
    to go to the end. Any partial trailing bytes in the data array that do
    not comprise a complete word of the size specified are ignored."""
    if num < 0: num = len(data)
    d08 = data[start:start+num]
    if big: fmt = '>'
    else: fmt = '<'
    if   nBytes ==  1: fmt = fmt + 'B'
    elif nBytes ==  2: fmt = fmt + 'H'
    elif nBytes ==  4: fmt = fmt + 'L'
    elif nBytes ==  8: fmt = fmt + 'Q'
    elif nBytes == -1: fmt = fmt + 'b'
    elif nBytes == -2: fmt = fmt + 'h'
    elif nBytes == -4: fmt = fmt + 'l'
    elif nBytes == -8: fmt = fmt + 'q'
    if nBytes < 0: nBytes = -nBytes
    d = [struct.unpack(fmt,bytes(d08[i:i+nBytes]))[0]
        for i in range(0,len(d08)-nBytes+1, nBytes)]
    return d
