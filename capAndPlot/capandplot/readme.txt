This folder contains capture/plot utilities for Vesper. It relies on modules
in "../mylibs" which must be located accordingly. It also uses Python and
third-party modules (see PythonInstallation.txt in the directory above).

The following are "user main scripts," meaning that they are intended to be
run directly. They are written so as not to need editting and are, instead,
parameterized using a separate parameter module. However, they can serve as
the basis for a custom script (be sure to adjust the module include paths
if the scripts are moved).

capAndPlot.py: Capture and plot (time/fft) data from one or more channels,
which may be on multiple Vesper units. The capture/plot runs continuously
for a specified number of iterations. The script saves the files for the
last iteration or all iterations if specified. This file does not set up streams 
so data streams must be configured on the unit using mnemonics. The capParms.py file
contains other configurable settings that should be set before running this script. 
Note that capParms.py does not need to be run, just edited before running this script. 

plotFiles.py: Plot the data in a list of files.

The other python files are not intended to be run directly as a main script.
Instead, they are included as modules in other scripts.