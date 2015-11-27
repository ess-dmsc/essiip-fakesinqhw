#!/usr/bin/tclsh
# DMC2280 uses cont-Z (hex 1a) as the EOF char
# Usage:
# ./getDMCprog.tcl -host dmcIP -port dmcPort > dmcprog.txt
# To fetch the code from the dmc2280 controller at dmcIP and
# write it to dmcprog.txt, dmcPort should be 1034.
# Note: Your computer must be on the same NBI vlan as the dmc
# controller for this to work.  However you can use ssh port
# forwarding to work remotely.

# On your computer run the following ssh command,
# ssh -L 1034:dmcIP:1034 sicsHostIP -lroot
# Then send the code with
# ./getDMCprog.tcl -host localhost -port 1034 > dmcprog.txt

array set args $argv

set con4 [socket $args(-host) $args(-port)]
fconfigure $con4  -buffering line -translation crlf -eofchar \x1a

proc Echo {chan } {
  global forever

   if {[eof $chan]} {
   # A rude exit works best. Closing the socket and terminating the forever loop is unreliable
     exit
     #close $chan
     #set forever done
   } else {
    puts [gets $chan]
  }
}

fileevent $con4 readable [list Echo $con4]
puts $con4 UL
vwait forever
