###############################################################################
# File list and path to files.
filePath = '/home/drs/ljump/_tmp_/'
filePath = '/proj/accts/ljump/test/capFiles/'
filePath =''
names = [ '003-data0.cap' ]

###############################################################################
# Capture related parameters. These are required because the capture file
# formats vary by capture interface.
# cap10Gig (otherwise V49 or DDR/raw).
cap10Gig = True         #10gE capture disables other capture methods
if not cap10Gig:
    captRaw = False     # Raw vs V49 capture path

###############################################################################
# Plot related parameters.
plotTime = True     # Time domain plot
plotFft = True      # FFT plot
plotTimeSkip = 0    # how many samples to skip at start in time plot
plotTimeLen = 0     # How many time points to plot. 0 means full length
isIq = True        # IQ data vs real. This program does not auto-detect
rate = 256e6        # sample rate
waitBetweenPlots = False
