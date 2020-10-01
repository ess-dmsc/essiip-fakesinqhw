# Fake Phytron Motor Controller Simulator

This simulator emulates a limited but sufficient subset of the  commands of the Phytron mcc-2. As this
thing is used at SINQ. The mcc-2 has a ASCII protocol but enclosed in <STX> and <ETXY where STX and ETX are binary character codes. It
also throws ACK and NACK into the messages.

Thus there are two programs:

**physhell.tcl** which implements a shell which translates user input into the phytron protocol. It is called with a single
argument which is the program to use to communicate with the mcc-2.

**phytron.tcl** The actual simulator. It reads from stdin and writes to stdout. It is meant to be used as a server either through
inetd or with ncat -k -e phytron.tcl -l -p 5050.

For the supported command set, see phytron.tcl. Please note that this implementation is for an older version of the phytron motor controller.
The command set for newer modells may differ. Also we hard coded only one controller in the chain, at address 0. But you can have two motors
on the phytron, X and Y. I also do not know in which way the command set is dependent on local adaptions made to the phytron by PSI
electronics staff.


