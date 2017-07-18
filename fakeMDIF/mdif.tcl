#------------------------------------------------------------------------------------
# This is a simulator for the MDIF thing at SINQ
# Usage: nc  -l <port> -k -c "tclsh mdif.tcl"
#
# Mark Koennecke, July 2017
#------------------------------------------------------------------------------------

set state local
set DT 0

while {[gets stdin line] > 0} {
    set line [string toupper $line]
    switch  $line {
	case "RMT 1" {
	    set state echo
	}
	case "ECHO 0" {
	    set state init
	}
	default {
	    if {[string compare $state init] == 0 && [string first DT $line] >=0} {
		set l [split $line]
		set DT [lindex $l 1]
            } else {
		puts "?OF"
		continue
            }
	}
    } 
    puts ""
}
