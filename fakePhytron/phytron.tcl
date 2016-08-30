#!/usr/bin/tclsh
#------------------------------------------------------------------------------
# This is a simulator for a phytron motor controller. It is supposed to
# be run either via ncat or inetd. It reads commands from stdin, calculates
# its act and responds to stdout.
#
# Mark Könnecke, September 2016
#------------------------------------------------------------------------------

set x(pos) 0
set x(lowlim) -100
set x(uplim) 100
set x(speed) 100
set x(target) 0
set x(mov) 0
set x(last) 0

set y(pos) 7
set y(lowlim) -100
set y(uplim) 100
set y(speed) 100
set y(target) 0
set y(mov) 0
set y(last) 0

proc phyReply {err data} {
    if {$err == 1} {
	puts stdout [format "%c%c%s%c" 0x02 0x05  $data 0x03]
    } else {
	puts stdout [format "%c%c%s%c" 0x02 0x06 $data 0x03]
    }
}
#--------------------------------------------------------------------
proc updateMotor {motar} {
    upvar #0 $motar mot

    if {$mot(mov) == 0} {
	return
    }

    if {$mot(target) < $mot(pos)} {
	set sign -1
    } else {
	set sign 1
    }

# I assume that one unit of the motor is 1000 steps    
    set tdiff [expr [clock seconds] - $mot(last)]
    set progress [expr ($tdiff * $mot(speed))/1000. ]
    set pos [expr $mot(pos) + $sign*$progress]
    if {$sign > 0} {
	if {$pos >= $mot(target)} {
	    set mot(mov) 0
	    set mot(pos) $mot(target)
	} else {
	    set mot(pos) $pos
	}
    } else {
	if {$pos <= $mot(target) } {
	    set mot(mov) 0
	    set mot(pos) $mot(target)
	} else {
	    set mot(pos) $pos
	}
    }
    set mot(last) [clock seconds]
}
#--------------------------------------------------------------------
proc processMotor {motar motcom} {
    upvar #0 $motar mot

    updateMotor $motar
    
    if { [string compare $motcom P20R] == 0 || \
	     [string compare $motcom P22R] ==  0 } {
	phyReply 0 $mot(pos)
	return
    }

    if { [string compare $motcom P20S] >= 0 || \
	     [string compare $motcom P22S] >=  0 } {
	set mot(pos) [string range $motcom 4 end]
	phyReply 0 ""    
	return
    }

    if {[string first A $motcom] == 0} {
	set val [string range $motcom 1 end]
	set mot(target) $val
	set mot(mov) 1
	set mot(last) [clock seconds]
	phyReply 0 ""
	return
    }

    if {[string first =H $motcom] >= 0} {
	if {$mot(mov) == 1} {
	    phyReply 0 N
	} else {
	    phyReply 0 E
	}
	return
    }

    if {[string first =I+ $motcom] >= 0} {
	if {$mot(pos) >= $mot(uplim)} {
	    phyReply 0 E
	} else {
	    phyReply 0 N
	}
	return
    }

    if {[string first =I- $motcom] >= 0} {
	if {$mot(pos) <= $mot(lowlim)} {
	    phyReply 0 E
	} else {
	    phyReply 0 N
	}
	return
    }

    if {[string first =E motcom] >= 0} {
	phyReply 0 N
	return
    }

    if {[string first P14R $motcom] >= 0} {
	phyReply 0 $mot(speed)
	return
    }

    if {[string first P14S $motcom] >= 0} {
	set mot(speed) [string range $motcom 4 end]
	phyReply 0 ""
	return
    }
    
    if {[string first SN $motcom] >= 0} {
	set mot(mov) 0
	phyReply 0 ""
	return
    }

    if {[string first O- $motcom] >= 0} {
	set mot(mov) 1
	set mot(target) $mot(lowlim)
	phyReply 0 ""
	return
    }

    phyReply 1 ""
}
#--------------------------------------------------------------------
proc processCommand {command} {
    if {[string first 0X $command] >= 0} {
	set mot x
    } else {
	set mot y
    }
    set motcom [string range $command 2 end]
    processMotor $mot $motcom
}

proc mainLoop {} {
    fconfigure stdout -buffering none
    fconfigure stdout -translation binary
    fconfigure stdin -translation binary
    set etx [format "%c" 0x03]
    set stx [format "%c" 0x02]

    set mode start
    while {1} {
	set c [read stdin 1]
	switch $mode {
	    start {
		if {[string compare $stx $c] == 0} {
		    set mode data
		    set command ""
		}
	    }
	    data {
		if {[string compare $etx $c] == 0} {
		    set mode start
		    processCommand $command
		} else {
		    append command $c
		}
	    }
	}    
    }
}

mainLoop
