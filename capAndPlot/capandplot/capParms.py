###############################################################################
# Capture configuration parameters are here. They must be customized to match
# your setup.
#
# The channel list is pairs: [unitIdx, chNum]. UnitIdx is zero based and
# indexes into unitIps. So the channels to be captured can span Vepser
# modules (except in raw capture mode).
#unitIps = [ '192.168.1.40' ]
unitIps = [ '172.22.24.104' ]
unitIps = [ '172.22.24.78' ]
chType=1       #1=tuner, 2=DDC...
chLst=[ [0, 1]]#, [0,2] ]

waitBetweenLoops = 0.01  #For capture part. Mainly when not plotting
waitBetweenPlots = False #pause between plots to inspect graph.
capFlush = True        #Flush pending data before each iter capture
keepAllFiles = False    #If false, each iteration overwrites files
nIter = 10000           #Loop iterations. Be careful if keepAllFiles
filePrefix = 'd'        #prefix of file name.
###############################################################################
# Capture related parameters.
# cap10Gig (otherwise V49 or DDR/raw). Each selection has unique parameters
cap10Gig = False         #10gE capture disables other capture methods
if cap10Gig:
    vitaPort = 4991     # Port used for 10gig capture
    pcIp = ['192.168.11.105'] # Interface to collect data on
    #pcIp = ['192.168.2.3'] # Interface to collect data on
    n10GigPackets = 4
    StopStartStream = False  #Stop and restart stream on each iter.
else:
    captRawType = 0     # 0=V49, else raw: 1=JESD, 2=DDR. JESD only 1 WB chnl
    capMode = 0         # For V49 capture trig. 0=on context, 1=on any packet
    capSize = 16384      # Number words to capture. 32768 is max for V49
    fixV49Swap = True   # Fix cap file byte/word swap in Vesper V49

###############################################################################
# Plot related parameters.
plotTime = True     # Time domain plot
plotFft = True      # FFT plot
plotTimeSkip =  0# 300    # how many samples to skip at start in time plot
plotTimeLen =   0   # How many time points to plot. 0 means full length
isIq = False         # IQ data vs real. This program does not auto-detect
rate = 125e6        # sample rate

