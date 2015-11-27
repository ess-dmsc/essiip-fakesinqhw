#!/bin/sh
# Generate md5 sums for the files in the SICS server directory.
if [ ! -d server ]
then
  echo "There must be a 'server' subdirectory"
  exit 1
fi

relnum_file="server/config/nexus/nxscripts_common_1.tcl"
relnum=`grep 'Name: RELEASE-' server/config/nexus/nxscripts_common_1.tcl|sed 's/.*\(RELEASE-[^ ]\+\).*/\1/'`

if [ $relnum = "" ]
then
  echo "Could not find RELEASE_NUMBER: in $relnum_file"
  exit 1
else
  echo "RELEASE_NUMBER is $relnum"
fi
md5file="SICS-${relnum}-server-md5sums.txt"
if [ ! -f $md5file ]
then
  find server| xargs -i md5sum {} > $md5file
  echo $md5file
  chmod 444 $md5file
else
  echo "$md5file already exists"
  exit 1
fi
