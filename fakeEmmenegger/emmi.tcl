#------------------------------------------------------------------------------------
# This is a simulator for the Emmenegger chopper electronics at SINQ
# Usage: nc  -l <port> -k -c "tclsh emmi.tcl"
#
# Mark Koennecke, July 2017
#------------------------------------------------------------------------------------

set D 0
set W 0

fconfigure stdin -translation cr
fconfigure stdout -translation cr

while {[gets stdin line] > 0} {
    set line [string toupper $line]
    if {[string first D $line] >= 0} {
	set l [split $line]
	if {[llength $l] > 1} {
	    set D [lindex $l 1]
	    puts ""
        } else {
	    puts  "$D"
        }
    }
    if {[string first W $line] >= 0} {
	set l [split $line]
	if {[llength $l] > 1} {
	    set W [lindex $l 1]
	    puts ""
        } else {
	    puts  "$W"
        }
    }
}
  
