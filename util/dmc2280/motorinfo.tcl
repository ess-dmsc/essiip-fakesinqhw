package require Tk

proc unknown {args} {}

# Check that the current position matches the configured home position
proc checkHome {motor} {
  global channel
  upvar #0 $motor motName
  upvar #0 ${motor}_status motStatus
  set chan $channel($motName(host))
  if {[info exists motName(absenc)] && $motName(absenc) == 1} {
    dmc_sendCmd $chan "TP$motName(axis)"
    set homeIndex absenchome
  } else {
    dmc_sendCmd $chan "TD$motName(axis)"
    set homeIndex motorhome
  }
  set home [dmc_receive $chan]
  set motStatus(position) $home
  set motStatus(home) $motName($homeIndex)
  if {$home == $motName($homeIndex)} {
    set motStatus(homeTest) TEST_PASSED
  } else {
    set motStatus(homeTest) TEST_FAILED
  }
   return $motStatus(homeTest)
}

# This implementation of the "Motor" command stores the
# configured motor parameters in an array named
# after the motor.
proc Motor {name type par} {
  global motors
  upvar #0 $par arr
  upvar #0 $name param_arr
  upvar #0 ${name}_status status
  array set param_arr [array get arr]
  array set status [list position "" home "" upperLim "" lowerLim "" homeTest NOTDONE limitTest NOTDONE]
  lappend motors $name
}

# Returns the test result status colour for the gui
proc color {status} {
  switch $status {
    TEST_PASSED {return green}
    TEST_FAILED {return red}
    default {return lightgrey}
  }
}

# You can easily test the home position of individual motors
# with this gui
# Click on the button to run the checkHome command, the position
# (in encoder counts or motor steps) will be displayed with
# green if the configured home matches the reported position,
# red otherwise.
proc testgui {} {
  package require Tk
  global motors
  toplevel .w
  frame .w.top

  foreach m $motors {
    global ${m}_status
    set info($m) [frame .w.top.f$m]

    set testResult $info($m).e$m
    button $info($m).$m -text $m -command "$testResult configure -background \[color \[checkHome $m\]\]"
    entry $testResult -textvariable ${m}_status(position)
    pack $info($m).$m -side left
    pack $info($m).e$m -side left
  }

  set n 0
  foreach m $motors {
    set r [expr $n % 20]
    set c [expr $n / 20]
    grid $info($m) -row $r -column $c
    incr n
  }
  pack .w.top
}
