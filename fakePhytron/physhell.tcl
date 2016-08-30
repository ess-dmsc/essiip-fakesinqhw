#!/usr/bin/tclsh
# This is a little program which acts as a shell to the phytron.
# It connects to another program which is supposed to talk to the phytron controller
# It reads from stdin, packages the message into the phytron format and sends it to
# the phytron communication program. Then it reads from the phytron communication program
# and unpacks the reply.
#
# This is also a nice exampe for dealing with binary in Tcl
# Making the binary character only worked with %c
# The only way to do the comparison is with the string comare
#
# Mark Könnecke, September 2016


if {[llength $argv] < 1} {
    puts stdout "Usage:\n\t physhell.tcl phytronprogram"
    exit
}

set phprogram [lindex $argv 0]

set phyio [open "| $phprogram" "w+b"]
fconfigure $phyio -buffering none
fconfigure $phyio -translation {binary binary}
set etx [format "%c" 0x03]
set stx [format "%c" 0x02]
set ack [format "%c" 0x06]
set nack [format "%c" 0x05]


while {1} {
    set inp [gets stdin]
    puts -nonewline $phyio [format "%c%s%c" 0x02 $inp 0x03]
    set mode start
    set reply ""
    while {[string compare $mode done] != 0 } {
	set c [read $phyio 1]
	switch $mode {
	    start {
		if {[string compare $c $stx] == 0} {
		    set mode data
		}
	    }
	    data {
		if {[string compare $c $etx] == 0} {
		    puts stdout $reply
		    set mode done
		} elseif {[string compare $c $nack] == 0} {
		    append reply NACK
		} elseif {[string compare $c $ack] == 0} {
		    append reply ACK
		} else {
		    append reply $c
		}
	    }
	}
    }
}    
