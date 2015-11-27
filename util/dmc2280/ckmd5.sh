#!/bin/sh
# Strip all horizontal and vertical whitespace from the galil controller programs
# and compare md5 sums.

instrument=${HOSTNAME#ics1-}
i=1
for f in controller*.md5
do
  name=`basename $f .md5`
  echo -n "$name "
  ./getDMCprog.tcl -host mc${i}-$instrument -port pmc${i}-$instrument |tr -d '[:space:]'|md5sum -c $f 2> /dev/null
  let i++
done
