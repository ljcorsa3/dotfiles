import sys
import struct
sys.path.insert(0, '../mylib')

##############################################################################
##############################################################################
class v49FilePkt:
    """
    This class provides an interface to a binary VITA-49 capture file created
    with a DDO snapshot upload of one of the V49 snapshot buffers. The data in
    the file is organized as a sequence of V49 packets, each comprising some
    number of 32 bit words. It is assumed that the file starts on a V49 packet
    boundary (i.e., with the V49 header word). Subsequent packets can be found
    using the packet length field in the header. The file can be traversed from
    the start using the length field. Each object defines the following public
    data attributes (nothing else shoud be directly accessed):
        typ: Packet type
        header: packet header word
        length: length of packet in 32-bit words.
        streamId: packet stream ID
        timeSec: Seconds value from packet
        timeFrac: Fractions seconds in ps.
        partial: Packet is truncated because file ran out
        data: An array of 32-bit data words after the "header."
        The header, in this context, comprises the first 5 words og the packet,
        starting at the V49 header word and continuing throug the time stamp.
    """
    def __init__(self, f, do16Swap=False, doEndianSwap=False, do32Swap=False):
        """f is a binary file handle and must be specified. If the file is
        not positioned at the start, then the data before it will not be read
        when processing the next packet. The first packet is not read when the
        object is first created."""

        self.pktHeader = 0
        self.pktType = -1
        self.pktCField = -1
        self.pktTField = -1
        self.pktRsvdField = -1
        self.pktCount = -1
        self.pktLength = 0
        self.streamId = 0
        self.timeSec = 0
        self.timeFrac = 0
        self.swap16 = do16Swap
        self.swap32 = do32Swap
        self.endianSwap = doEndianSwap
        self.partial = False
        self.hdr = []
        self.data = []
        self.f = f



    ##############################################################################
    def readV49Word(self):
        """Read one 32 bit word from the file. V49 is 32-bit word oriented. We
        also swap 16 bit halves if required (self.swap16). This returns the 32
        bit unsigned integer or None if there are any errors. Under normal
        conditions, None is returned at the end of file. """

        try:
            if self.swap32:
                global w64b,f64buffered
                if f64buffered == False:
                    f64buffered = True
                    w64b = self.f.read(4)
                    w32 = self.f.read(4)
                else:
                    f64buffered = False
                    w32 = w64b
            else:
                w32 = self.f.read(4)

            w16 = 0
            if self.endianSwap:
                w16 = struct.unpack('>HH', w32)
            else:
                w16 = struct.unpack( 'HH', w32)

            if self.swap16: return (w16[0] << 16) + w16[1]
            else:           return (w16[1] << 16) + w16[0]

        except:
            # This is actually a normal condition at EOF
            return None

    ##############################################################################
    def readV49Array(self, arr, num):
        """Read a number of 32 bit words and append them to the passed array. The
        function returns the number of words actually read. """
        nRead = 0
        for i in range(0,num):
            w = self.readV49Word()
            if w == None: break
            arr.append(w)
            nRead = nRead + 1
        return nRead



    ##############################################################################
    def getNextPkt(self):
        """Get the next packet from the file. This reads the entire packet data
        from the file and moves the file pointer to the next packet. Returns True
        if packet found or False on EOF or error."""
        global w64b,f64buffered
        minPkt = 0x26
        maxPkt = 0x806
        err = 0
        self.data = []
        self.interpacketcnt = -1

        while -1:
            hdr = []
            f64buffered = False
            self.interpacketcnt += 1
            if (self.readV49Array(hdr, 1) == 0): return False       ## gotPkt = False, EOF
            self.pktHeader = hdr[0]
            self.pktType = (hdr[0] >> 28) & 0xf
            self.pktCField = (hdr[0] >> 27) & 0x1
            self.pktTField = (hdr[0] >> 26) & 0x1
            self.pktRsvdField = (hdr[0] >> 24) & 0x3
            self.pktTsiField = (hdr[0] >> 22) & 0x3
            self.pktTsfField = (hdr[0] >> 20) & 0x3
            self.pktCount = (hdr[0] >> 16) & 0xf
            self.pktLength = self.pktHeader & 0xffff
            #print(format(hdr[0],'8x'))
            if (self.pktLength <= maxPkt) and (self.pktLength >= 5):                                         ## v49 Length is acceptable
                if (self.pktType == 1) \
                    and (self.pktRsvdField == 0) \
                    and (self.pktLength >= minPkt) \
                    and (self.pktLength <= maxPkt): break    ## v49 Type 1 is acceptable
            if (self.pktType == 4) and (self.pktLength <= 0x10): break                                  ## v49 Type 4 is acceptable

        #print([hex(x) for x in hdr])

        self.readV49Array(hdr, 4)
        if len(hdr) < 5: return False                           ## gotPkt = False, EOF
        self.hdr = hdr
        self.streamId = hdr[1]
        self.timeSec = hdr[2]
        self.timeFrac = hdr[3] * 0x100000000 + hdr[4]

        if (self.pktLength > maxPkt) or (self.pktLength < 5): err = 20     ## v49 Length is too long

        if err==0:
            self.readV49Array(self.data, self.pktLength-5)
            if (len(self.data)+len(hdr)) < self.pktLength: gotPkt = False
            else:                                          gotPkt = True
        else:
            gotPkt = False

        return gotPkt

    ##############################################################################
    def writeV49Word(self, fOut, w):
        fOut.write(bytearray(struct.pack('!I',w)))

    ##############################################################################
    def pktWrite(self, fOut):
        for i in range(0,len(self.hdr)): self.writeV49Word(fOut, self.hdr[i])
        for i in range(0,len(self.data)): self.writeV49Word(fOut, self.data[i])


    ##############################################################################
    def __iter__(self):
        return self
    ##############################################################################
    def __next__(self):
        if self.getNextPkt():
            return self
        else:
            raise StopIteration
    ##############################################################################
    def next(self):
        return self.__next__()
