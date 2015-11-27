#!/usr/bin/tclsh
# DMC2280 uses cont-Z (hex 1a) as the EOF char
# Usage:
# ./putDMCprog.tcl -host dmcIP -port dmcPort < dmcprog.txt
# To send the code to the dmc2280 controller at dmcIP and
# read it from dmcprog.txt, dmcPort should be 1034.
#
# Note: Your computer must be on the same NBI vlan as the dmc
# controller for this to work.  However you can use ssh port
# forwarding to work remotely.
#
# On your computer run the following ssh command,
# ssh -L 1034:dmcIP:1034 sicsHostIP -lroot
# Then send the code with
# ./putDMCprog.tcl -host localhost -port 1034 < dmcprog.txt

global forever
set line_num 0

# Convert the argument list into a has table
array set args $argv

if { 0 } {
  set con4 stdout
  fconfigure $con4  -buffering line -translation crlf -eofchar \x1a
} else {
  # Open the socket to the controller
  set con4 [socket $args(-host) $args(-port)]
  # Set up the socket for the controller
  fconfigure $con4  -buffering none -translation crlf
}

proc Echo { chan } {
  global forever
  global line_num

  if { [eof stdin] } {
    puts stdout "\\"
    puts $chan "\\"
    flush stdout
    flush $chan
    after 500
#   puts stdout "XQ #AUTO,0"
#   puts $chan "XQ #AUTO,0"
#   flush stdout
#   flush $chan
#   after 500
    set forever done
    exit
  } else {
    set line [gets stdin]
    if { "$line" != "" } {
#     puts stdout "$line_num: $line"
#     set line_num [expr $line_num + 1]
      puts $chan $line
      flush stdout
      flush $chan
      after 10
    }
  }
}

puts stdout ""
puts $con4 ""
after 500
# Stop any execution that might interfere with the download
puts stdout "HX"
puts $con4 "HX"
after 500
# Start the download
puts stdout "DL"
puts $con4 "DL"
after 500
if { 0 } {
  fileevent $con4 writable [list Echo $con4]
  fileevent $con4 readable [list puts [gets $con4]]
  vwait forever
} else {
  while { 1 } {
    Echo $con4
  }
}

