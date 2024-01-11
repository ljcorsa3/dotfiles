"""
The b64 module conversions between base-64 strings and binary byte arrays.
to tuner commands and queries. Most commands require a socket parameter that
identifies the TCP/IP socket to which the tuner is connected. There are two
generic functions -- sendCmd and sendRcvQuery -- which are used for sending
general commands and queries, respectively.
"""

# Mapping table that maps a 6 bit binary number into its b64 ASCII code.
# Note the inverse table (b64ToNumTbl). A change to one requires a change
# to the other.
b64FromNumTbl = [\
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', #  0.. 7 \
    'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', #  8..15 \
    'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', # 16..23 \
    'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', # 24..31 \
    'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', # 32..39 \
    'o', 'p', 'q', 'r', 's', 't', 'u', 'v', # 40..47 \
    'w', 'x', 'y', 'z', '0', '1', '2', '3', # 48..55 \
    '4', '5', '6', '7', '8', '9', '+', '/'] # 56..63

# Mapping table that maps 7 bit ASCII characters that represent a B64 char
# into the 6 bit binary number it represents or -1 if the char is not valid.
b64ToNumTbl = [\
    #x00 x01 x02 x03 x04 x05 x06 x07 x08 x09 x0a x0b x0c x0d x0e x0f
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, \
    #x10 x11 x12 x13 x14 x15 x16 x17 x18 x19 x1a x1b x1c x1d x1e x1f
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, \
    #    !   "   #   $   %   &   '   (   )   *   +   ,   -   .   /
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, 63, \
    #0   1   2   3   4   5   6   7   8   9   :   ;   <   =   >   ?
    52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1, \
    #@   A   B   C   D   E   F   G   H   I   J   K   L   M   N   O
    -1,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, \
    #P   Q   R   S   T   U   V   W   X   Y   Z   [   \   ]   ^   _
    15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1, \
    #`   a   b   c   d   e   f   g   h   i   j   k   l   m   n   o
    -1, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, \
    #p   q   r   s   t   u   v   w   x   y   z   {   |   }   ~  x7f
    41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, -1, -1, -1, -1, -1]

##############################################################################
def b64CharToBin(c):
    """Convert one b64 character into the 6 bit binary number it represents.
    If the character is not valid b64, then return None. """
    iC = ord(c)
    if (iC < 0) or (iC > 127): return None
    else:
        b = b64ToNumTbl[iC]
        if b < 0: return None
        else:     return b

##############################################################################
def b64ToBytes(inStr):
    """Convert a character string (inStr) in b64 format to the array of binary
    bytes it represents. It returns the binary unless it encounters error, in
    which case it returns None. It discards and trailing any partial byte
    at the end."""
    b64Pad = '='
    outBytes = []
    err = 0
    nBits = 0
    w = 0
    sLen = len(inStr)
    sIdx = 0
    if ord(b64Pad) > 0:
        if (sLen > 0) and (inStr[sLen-1] == b64Pad): sLen -= 1
        if (sLen > 0) and (inStr[sLen-1] == b64Pad): sLen -= 1
    while (err == 0) and (sIdx < sLen):
        # Convert the next B64 char into 6 bit data.
        b = b64CharToBin(inStr[sIdx])
        if b == None: err = 1
        else:
            # Shift new bits in after the accumulated partial bits (LSB
            # first), then increment the number of partial bits for the
            # next iteration.
            w <<= 6
            w |= b
            nBits  += 6
            # If we have accumulated a byte (8 or more bits) then output
            # 8 bits and shift the accumulator down by that much so any
            # additional partial bits are in LSBs. Then adjust partial
            # bitcount for the 8 we just output.
            if nBits >= 8:
                outBytes.append((w >> (nBits-8)) & 255)
                nBits -= 8
            sIdx = sIdx + 1
    if (err == 0) & (nBits == 8):
        outBytes.append(w & 255)
    if (err == 0): return outBytes
    else:          return None
