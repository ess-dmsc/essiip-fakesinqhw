# utility functions like basename/dirname in bash (dcl)
  proc basename {node} {
    set point [string last "/" $node]
    if { $point < 0 } {
      return $node
    } else {
      incr point
      return "[string range $node $point end]"
    }
  }
  proc pathname {node} {
    set point [string last "/" $node]
    if { $point < 0 } {
      return ""
    } else {
      incr point -1
      return "[string range $node 0 $point]"
    }
  }

# Many of these functions are also useful in test and debug code
# running on an external Tcl interpreter.
set errorInfo ""
set errorCode NONE
set errorContext ""
set callStack ""

proc callinfo {args} {
  if {$args == "errors"} {
    set msg "ERROR CONTEXT\n$::errorContext\n\nCALLSTACK\n$::callStack"
  } else {
    set msg "CALLSTACK\n$::callStack"
  }
  return $msg
}
publish callinfo user

# @brief Reset error information variables when entering a catch command
proc entercatch {args} {
  uplevel {
    global errorCode errorContext callStack
    if {[info level] > 0} {
      set errorCode NONE
#      set errorContext ""
#      set callStack ""
    }
  }
}

# @brief Set the errorContext and build the callStack when leaving a catch command
#
# ::errorContext is set to ::errorInfo
# ::callStack is a stack of command calls showing the argument values
proc leavecatch {args} {
  uplevel {
    global callStack errorContext errorCode errorInfo
    if {[info level] > 0} {
      if {$errorCode=="NONE"} {
        set callStack ""
        set errorContext ""
      } else {
      append callStack "\t[info level 0]\n"
   }
    }
  }
}

# @brief Set the ::errorCode to "ERROR" when ::errorInfo is modified.
#
# NOTE\n
# Tcl always sets errorCode=NONE when there is no additional information\n
# about an error, as well as when there is no error! However when a command\n
# returns with an error it always writes to errorInfo.
proc errorInfowrite {args} {
  uplevel {
    global errorContext errorCode errorInfo
    if {[info level] > 0} {
      if {$errorInfo != ""} {
        append errorContext $errorInfo
        set errorCode ERROR
      }
    }
  }
}

proc callStack {enable} {
  if {$enable} {
    set trace_opt "add"
  } else {
    set trace_opt "remove"
  }
  trace $trace_opt variable errorInfo write errorInfowrite
  trace $trace_opt execution catch enter entercatch
  trace $trace_opt execution catch leave leavecatch
}
publish callStack mugger
callStack false


# LIST FUNCTIONS
proc head {args} {lindex [join $args] 0}
proc tail {args} {join [lrange [join $args] 1 end]}

# SET FUNCTIONS

# Set membership
proc setmem {el A} {
  expr {[lsearch $A $el] >= 0}
}

# Set difference: A\B, members of A that are not in B
proc setdiff {A B} {
  foreach el $A {
    if {[lsearch -exact $B $el] == -1} {
      lappend missing $el;
    }
  }
  if {[info exists missing]} {
    return $missing;
  }
}

proc _intersection {lista listb} {
  set result {}
  foreach elem [join $listb] {
    if { [lsearch -exact $lista $elem] >= 0} {
      lappend result $elem
    }
  }
  return $result
}

proc intersection {lista args} {
  if {[llength $args] == 0} {return $lista}
  if {[llength $args] == 1} {return [_intersection $lista $args]}
  return [intersection [_intersection $lista [head $args]] [tail $args]];
}


# TYPE CHECKING
# This is an enhanced set membership function.
# It can check that an element is a member of a list or
# of a named type
proc isoneof {element setb} {
  global simpleType;
  set result 0;

  foreach elb $setb {
    switch $elb {
      alpha {set result [string is alpha $element]}
      text {set result [string is wordchar $element]}
      print {set result [string is print $element]}
      float {set result [string is double $element]}
      int {set result [string is integer $element]}
      default {set result [expr {$element == $elb}]}
    }
    if {$result == 1} {return 1}
  }
  return 0;
}

# Returns 'sicslist' output in lower case, this may be useful in macros.
# This function is used a lot in the hdbbuilder
proc tolower_sicslist {args} {
  if [ catch {
  set result [eval sicslist $args]
  return [string tolower $result];
  } message ] {
    if {$::errorCode=="NONE"} {return $message}
    return -code error $message
  }
}

# \brief Enables or disables the debug_msg command
#
# \param mode on turns on debugging, off turns off debugging
#
# \see debug_msg
# TODO Set a callstack global variable
proc debug_mode {mode} {
  switch $mode {
    on {
      proc debug_msg {args} {
        switch [info level] {
          0 {
            # This happens when debug_msg is used with trace
            clientput $args
          }
          1 {
            # This probably only occurs if you debug_msg directly. Why would you do that?
            set cmdinfo [info level 0]
            set cmd [lindex $cmdinfo 0]
            set nscmd [namespace origin $cmd]
            clientput "DEBUG, ${nscmd}::$cmdinfo]$args"
          }
          2 {
            set cmdinfo [info level -1]
            set cmd [lindex $cmdinfo 0]
            set nscmd [namespace origin $cmd]
            clientput "DEBUG, ${nscmd}::$cmdinfo]$args"
          }
          3 - default {
            set cmdinfo [info level -1]
            set cmd [lindex $cmdinfo 0]
            set nscmd [namespace origin $cmd]
            set callerinfo [info level -2]
            set caller [lindex $callerinfo 0]
            set nscaller [namespace origin $caller]
            clientput "DEBUG, ${nscaller}::$callerinfo\n\t${nscmd}::$cmdinfo]$args"
          }
        }
      }
    }
    off {
      proc debug_msg {args} {};
    }
  }
}

## \brief You can use debug_msg in place of 'puts' for debug info in Tcl macros.
#
# Add debug messages on the fly with
# strace add execution <proc> enter debug_msg
proc debug_msg {args} {};
publish debug_mode mugger

proc todo_msg {args} {
  set cmdinfo [info level -1]
  set cmd [lindex $cmdinfo 0]
  clientput "TODO <$cmd> $args"
}

proc error_msg {args} {
  set cmdinfo [info level -1]
  set cmd [lindex $cmdinfo 0]
  set arglist [lrange $cmdinfo 1 end]
  error "ERROR: [namespace origin $cmd] $arglist: $args"
}

# Use this function if you expect a decimal number which might be
# padded with zeroes.
# \brief Strips leading zeroes from decimal numbers.
# NOTE: It's up to you to check if the unpadded string is a valid number.
#
# Handles 0 and numbers prefixed with - or +.
proc unpad {n} {
  return [regsub {([+-])?0*(\d+)} $n {\1\2}]
}
