# Makefile for zmqGenerator

OBJ=neventArray.o zmqGenerator.o nexus2event.o posix-timers.o md5.o
NXINSTALL=/afs/psi.ch/project/sinq/sl6

ROBJ=zmqReader.o

all: zmqGenerator zmqReader

.c.o:
	$(CC) -c -g -I$(NXINSTALL)/include $*.c

zmqGenerator: $(OBJ)
	$(CC) -g -o zmqGenerator -L$(NXINSTALL)/lib $(OBJ) -lNeXus -lhdf5 -lsz -lrt -lzmq

zmqReader: $(ROBJ)
	$(CC) -g -o zmqReader $(ROBJ) -lzmq

clean:
	- rm *.o
	- rm zmqGenerator




