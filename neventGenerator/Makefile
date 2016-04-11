# Makefile for zmqGenerator

OBJ=neventArray.o zmqGenerator.o nexus2event.o posix-timers.o md5.o
NXINSTALL=/afs/psi.ch/project/sinq/sl6-64

ROBJ=zmqReader.o

all: zmqGenerator zmqReader

.c.o:
	$(CC) -c -ggdb -I$(NXINSTALL)/include $*.c

zmqGenerator: $(OBJ)
	$(CC) -ggdb -o zmqGenerator -L$(NXINSTALL)/lib $(OBJ) -lNeXus -lhdf5 -lsz -lrt -lzmq -lsodium

zmqReader: $(ROBJ)
	$(CC) -ggdb -o zmqReader $(ROBJ) -L$(NXINSTALL)/lib -lzmq -lsodium

clean:
	- rm *.o
	- rm zmqGenerator zmqReader




