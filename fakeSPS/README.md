# SPS Simulation for AMOR

This is a simulation of the SPS for AMOR. This is actually a Siemens SPS5 with a custom
RS232 interface. And a SPS is a programmable logic component. The command protocol is
pretty simple:

R

prints 16 bytes worth of binary inputs

A

prints 8 bytes worth of analog inputs. The conversion of the analog input value to a meaningful value is
application dependent and different per instrument.

S0001

Flips a digictal input. The first three numbers denote the byte in which to flip the input, the last character denotes the
bit. Thus the example flips bit 1 in byte 0.


For AMOR the following input bits have been implemented:

* 0,0 for the shutter. Changes output byte 5
* 0,1 for switching on the laser, changes byte 16
* 0,7 for switching the RF on and off for the spin flipper, changes byte 13


## Other Instruments

For other instruments, I suggest to make a copy, verify the byte initialisation and implement the method doPush(self,byte,bit) according
to the SPS implementation at that instrument. Of course it will be different then at AMOR.


