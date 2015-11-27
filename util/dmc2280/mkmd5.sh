#!/bin/sh
# Strip all horizontal and vertical whitespace from the galil controller programs
# and generate md5 sums.
for f in controller*.txt
do
  name=`basename $f .txt`
  cat $f |tr -d '[:space:]'|md5sum > $name.md5
done
