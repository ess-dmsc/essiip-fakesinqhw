# $Revision: 1.3 $
# $Date: 2007/10/31 06:10:30 $
# Author: Ferdi Franceschini (ffr@ansto.gov.au)
# Last revision by: $Author: ffr $

# Creates a socket server which listens for connections and accepts commands
# from clients (eg SICS).
proc serverOpen {channel addr port} {
  global voltage
  global connected
  set connected 1
  set voltage 0
# fconfigure $channel -translation binary -buffering none
  fileevent $channel readable "readLine $channel"
  puts "OPENED"
  return;
}

# <input ABCD>,<off/on [10]>,<high>,<low><deadband>,<latch enable>,<audible>,<visible>
# Default to off for all inputs
array set ALARM {"A" 0 "B" 0 "C" 0 "D" 0}
array set ALARMST {"A" 0 "B" 0 "C" 0 "D" 0}
array set CRVHDR {
1 "DT-336-1       ,STANDARD  ,1,+500.000,1"
2 "DT-336-2       ,STANDARD  ,2,+0.500,1"
3 "DT-336-3       ,STANDARD  ,3,+2.000,2"
4 "DT-336-4       ,STANDARD  ,4,+0.301,2"
}
array set HTR {1 0 2 0}
array set HTRST {1 0 2 0}
set IDN "LSCI,MODEL336,336A03T/#######,1.2"
array set INCRV {"A" 1 "B" 2 "C" 3 "D" 4}
array set INTYPE {"A" "1,0,1,0,1" "B" "1,0,1,0,1" "C" "1,0,1,0,1" "D" "1,0,1,0,1" }
array set KRDG {"A" 300 "B" 300 "C" 300 "D" 300}
array set MOUT {1 0.0 2 0.0 3 0.0 4 0.0}
array set OUTMODE {1 1,1,0 2 1,2,0 3 1,3,0 4 1,4,0}
array set PID {1 +0150.0,+0005.0,+000.0 2 +0150.0,+0005.0,+000.0}
array set RAMP {1 +000.00 2 +000.00}
array set RAMPST {1 0 2 0}
array set RANGE {1 0 2 0 3 0 4 0}
array set RDGST {"A" 0 "B" 0 "C" 0 "D" 0}
array set RELAY {1 "1,A,0" 2 "2,A,0"}
array set RELAYST {1 0 2 0}
array set SETP {1 300.0 2 300.0 3 300.0 4 300.0}
set STB 0

proc driveTotemp {} {
global array SETP
global array KRDG
global array stepKRDG
set tol 0.1
  foreach {spi t} {1 A 2 B 3 C 4 D} {
    set diff [expr abs( $KRDG($t) - $SETP($spi) )]
    if { $diff > $tol } {
    puts "[info level 0] diff = $diff, stepKRDG($t) = $stepKRDG($t)"
     if  {$diff < [expr abs($stepKRDG($t)) ]} {
      set KRDG($t) $SETP($spi)
     } else {
      set KRDG($t) [expr $KRDG($t) + $stepKRDG($t)]
     }
    }
  }
}
proc readLine {channel} {
global array ALARM
global array ALARMST
global array CRVHDR
global array HTR
global array HTRST
global IDN
global array INCRV
global array INTYPE
global array KRDG
global array MOUT
global array OUTMODE
global array PID
global array RAMP
global array RAMPST
global array RANGE
global array RDGST
global array RELAY
global array RELAYST
global array SETP
global array stepKRDG
global STB

  if [eof $channel] {
    # Channel will be closed then re-opened
    return -code error "GOT EOF"
  }
  gets $channel data
  puts "RECEIVED: $data"
  switch [llength $data] {
    0 {
      puts "Oops received nothing"
      set cmd XXX
    }
    1 {
      set cmd [lindex $data 0]
    }
    2 {
      set cmd [lindex $data 0]
      set arg [lindex $data 1]
    }
    default {
      puts $channel "ERR: Invalid command: $data"
      flush stdout
      flush stderr
      flush $channel
      return -code error "Invalid command: $data"
    }
  }

  switch $cmd {
    "ALARM?" {
      puts $channel $ALARM($arg)
    }
    "ALARMST?" {
      puts $channel $ALARMST($arg)
    }
    "CRVHDR?" {
      puts $channel $CRVHDR($arg)
    }
    "HTR?" {
      puts $channel $HTR($arg)
    }
    "HTRST?" {
      puts $channel $HTRST($arg)
    }
    "*IDN?" {
      driveTotemp
      puts $IDN
      puts $channel $IDN
    }
    "INCRV?" {
      puts $channel $INCRV($arg)
    }
    "INTYPE?" {
      puts $channel $INTYPE($arg)
    }
    "KRDG?" {
      puts $channel [expr rand() + $KRDG($arg) - 0.5]
    }
    "MOUT?" {
      puts $channel $MOUT($arg)
    }
    "OUTMODE?" {
      puts $channel $OUTMODE($arg)
    }
    "PID?" {
      puts $channel $PID($arg)
    }
    "RAMP?" {
      puts $channel $RAMP($arg)
    }
    "RAMPST?" {
      puts $channel $RAMPST($arg)
    }
    "RANGE?" {
      puts $channel $RANGE($arg)
    }
    "RDGST?" {
      puts $channel $RDGST($arg)
    }
    "RELAY?" {
      puts $channel $RELAY($arg)
    }
    "RELAYST?" {
      puts $channel $RELAYST($arg)
    }
    "SETP?" {
      puts $channel $SETP($arg)
    }
    "*STB?" {
      puts $channel $STB
    }
    "*TST?" {
      puts $channel 0
    }
    "ALARM" {
    }
    "INCRV" {
    }
    "INTYPE" {
    }
    "MOUT" {
    }
    "OUTMODE" {
    }
    "PID" {
    }
    "RAMP" {
    }
    "RANGE" {
      array set RANGE [split $arg ,]
    }
    "RELAY" {
    }
    "SETP" {
      foreach {s v} [split $arg ,] {}
      puts "set SETPOINT $s $v"
      array set SETP "$s $v"
      switch $s {
        "1" {set stepKRDG(A) [expr  ( $v - $KRDG(A) )/10.0] }
        "2" {set stepKRDG(B) [expr  ( $v - $KRDG(B) )/10.0] }
        "3" {set stepKRDG(C) [expr  ( $v - $KRDG(C) )/10.0] }
        "4" {set stepKRDG(D) [expr  ( $v - $KRDG(D) )/10.0] }
      }
    }
  }


  flush stdout
  flush stderr
  flush $channel

}

# startserver -port 1034
proc startserver {args} {
  global tcl_interactive;
  array set parr $args;
  set connected 0;
  set server [socket -server serverOpen $parr(-port)];
  after 100 update;
  if {$tcl_interactive==0} {vwait forever }
  return;
}

startserver -port 7777
