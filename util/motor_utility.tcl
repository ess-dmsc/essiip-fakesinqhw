# Some useful functions for SICS motor configuration.

# Author: Douglas Clowes (dcl@ansto.gov.au)

proc relmove {runcmd args} {
  if [ catch {
    if {[llength $args] == 1} {
      set arguments [lindex $args 0]
    } else {
      set arguments $args
    }

    array set motoffset $arguments
    foreach motor [array names motoffset] {
      set currpos [SplitReply [$motor]]
      lappend motdest $motor [expr $currpos + $motoffset($motor)]
    }
    switch $runcmd {
      "relrun" {
        eval "run $motdest"
      }
      "reldrive" {
        eval "drive $motdest"
      }
    }
  } message ] {
    if {$::errorCode=="NONE"} {return }
    return -code error $message
  }
}

proc relrun {args} {
  if [ catch {
    relmove "relrun" $args
  } message ] {
    if {$::errorCode=="NONE"} {return }
    return -code error $message
  }
}
publish relrun user

proc reldrive {args} {
  if [ catch {
    relmove "reldrive" $args
  } message ] {
    if {$::errorCode=="NONE"} {return }
    return -code error $message
  }
}
publish reldrive user

# \brief Posit run command for positional motors
# \parameter List of motor names and position names
proc prun {args} {
  if [ catch {
    foreach {mot pname} $args {
      set posnames [SplitReply [$mot position_names]]
      if {([llength $posnames] == 0) && [string is double $pname]} {
        lappend drlist $mot $pname
      } else {
        if {[lsearch $posnames $pname] == -1} {
          error "$pname must be one of $posnames for $mot"
        }
        lappend drlist $mot [SplitReply [$mot posit2unit $pname]]
      }
    }
    clientput run {*}$drlist
    anstocapture run {*}$drlist
  } message ] {
    set msg_list [split $message \n]
    set start [lsearch $msg_list ERROR*]
    if {$start == -1} {
      return $message
    } else {
      return [join [lrange $msg_list $start end-1] \n]
    }
  }
}
publish prun user

# \brief Posit drive command for positional motors
# \parameter List of motor names and position names
proc pdrive {args} {
  if [ catch {
    foreach {mot pname} $args {
      set posnames [SplitReply [$mot position_names]]
      if {([llength $posnames] == 0) && [string is double $pname]} {
        lappend drlist $mot $pname
      } else {
        if {[lsearch $posnames $pname] == -1} {
          error "$pname must be one of $posnames for $mot"
        }
        lappend drlist $mot [SplitReply [$mot posit2unit $pname]]
      }
    }
    clientput drive {*}$drlist
    anstocapture drive {*}$drlist
  } message ] {
    set msg_list [split $message \n]
    set start [lsearch $msg_list ERROR*]
    if {$start == -1} {
      return $message
    } else {
      return [join [lrange $msg_list $start end-1] \n]
    }
  } else {
    foreach {mot pname} $args {
      lappend ret New $mot position:    $pname
    }
    lappend ret Driving finished successfully
    return $ret
  }
}
publish pdrive user

##
# @brief  A convenience command for fetching motor parameter values
#
# This convenience command is useful for avoiding command
# substitution problems when defining hdb node read scripts.
proc getmotpar {motor par} {
  return  [SplitReply [$motor $par]]
}

# Functions for the slit motors (echidna, wombat, platypus, ...)
#
# functions used by the generated functions
proc get_gap_width {m1 m2} {
  return [expr [SplitReply [$m1]] - [SplitReply [$m2]]]
}

proc set_gap_width {m1 m2 val} {
  set currentWidth [expr [SplitReply [$m1]] - [SplitReply [$m2]]]
  set diff [expr $val - $currentWidth]
  set newD1R [expr [SplitReply [$m1]] + $diff/2]
  set newD1L [expr [SplitReply [$m2]] - $diff/2]
  return "$m1=$newD1R,$m2=$newD1L"
}

proc get_gap_offset {m1 m2} {
  set S1 [SplitReply [$m1]]
  set S2 [SplitReply [$m2]]
  return [ expr ($S1 + $S2)/2.0 ]
}

proc set_gap_offset {m1 m2 val} {
  set S1 [SplitReply [$m1]]
  set S2 [SplitReply [$m2]]
  set currentoffset [expr ($S1 + $S2)/2.0 ]
  set diff [expr $val - $currentoffset]
  set newD1R [expr $S1 + $diff]
  set newD1L [expr $S2 + $diff]
  return "$m1=$newD1R,$m2=$newD1L"
}

# Generator functions
proc make_gap_motors {vm1 vm1_name vm2 vm2_name m1 m2 aunits agroup} {
  eval "proc get_$vm1 {} { get_gap_width $m1 $m2 }"
  set v {$var}
  eval "proc set_$vm1 {var} { set_gap_width $m1 $m2 $v }"
  MakeConfigurableMotor $vm1
  $vm1 readscript get_$vm1
  $vm1 drivescript set_$vm1
#publish get_$vm1 user
#publish set_$vm1 user

  eval "proc get_$vm2 {} { get_gap_offset $m1 $m2 }"
  set v {$var}
  eval "proc set_$vm2 {var} { set_gap_offset $m1 $m2 $v }"
  MakeConfigurableMotor $vm2
  $vm2 readscript get_$vm2
  $vm2 drivescript set_$vm2
#publish get_$vm2 user
#publish set_$vm2 user

sicslist setatt $vm1 units $aunits
sicslist setatt $vm1 klass slits
sicslist setatt $vm1 long_name $vm1_name
sicslist setatt $vm1 group $agroup
sicslist setatt $vm1 hdbchain $m1,$m2
sicslist setatt $vm2 units $aunits
sicslist setatt $vm2 klass slits
sicslist setatt $vm2 long_name $vm2_name
sicslist setatt $vm2 group $agroup
sicslist setatt $vm2 hdbchain $m1,$m2
}

# Functions for motors with defined positions (quokka, platypus)
#
# functions used by the generated functions
proc set_virtual_1 { phys1 posit } {
  set units [expr [SplitReply [$phys1 posit2unit $posit]]]
  return "$phys1=$units"
}

proc set_virtual_2 { phys1 phys2 posit } {
  set unit1 [expr [SplitReply [$phys1 posit2unit $posit]]]
  set unit2 [expr [SplitReply [$phys2 posit2unit $posit]]]
  return "$phys1=$unit1,$phys2=$unit2"
}

proc get_virtual_1 { phys1 } {
  set p1 [expr [SplitReply [$phys1 posit]]]
  return $p1
}

proc get_virtual_2 { phys1 phys2 } {
  set p1 [expr [SplitReply [$phys1 posit]]]
  set p2 [expr [SplitReply [$phys2 posit]]]
  return [expr ($p1 + $p2) / 2.0]
}
#publish set_virtual_1 user
#publish set_virtual_2 user
#publish get_virtual_1 user
#publish get_virtual_2 user

# Generator functions
proc make_vmot { vm1 pm1 aunits } {
  eval "proc get_$vm1 {} { get_virtual_1 $pm1 }"
  set v {$var}
  eval "proc set_$vm1 {var} { set_virtual_1 $pm1 $v }"
  MakeConfigurableMotor $vm1
  $vm1 readscript get_$vm1
  $vm1 drivescript set_$vm1
  sicslist setatt $vm1 units $aunits
  sicslist setatt $vm1 klass [SplitReply [sicslist klass $pm1]]
  sicslist setatt $vm1 long_name $vm1
  sicslist setatt $vm1 hdbchain $pm1
}

proc make_coll_motor_1 { vm1 vm1_name pm1 aunits } {
  eval "proc get_$vm1 {} { get_virtual_1 $pm1 }"
  set v {$var}
  eval "proc set_$vm1 {var} { set_virtual_1 $pm1 $v }"
  MakeConfigurableMotor $vm1
  $vm1 readscript get_$vm1
  $vm1 drivescript set_$vm1
  sicslist setatt $vm1 units $aunits
  sicslist setatt $vm1 klass collimator
  sicslist setatt $vm1 long_name $vm1_name
  sicslist setatt $vm1 hdbchain $pm1
}

proc make_coll_motor_2 { vm1 vm1_name pm1 pm2 aunits } {
  eval "proc get_$vm1 {} { get_virtual_2 $pm1 $pm2 }"
  set v {$var}
  eval "proc set_$vm1 {var} { set_virtual_2 $pm1 $pm2 $v }"
  MakeConfigurableMotor $vm1
  $vm1 readscript get_$vm1
  $vm1 drivescript set_$vm1
  sicslist setatt $vm1 units $aunits
  sicslist setatt $vm1 klass collimator
  sicslist setatt $vm1 long_name $vm1_name
  sicslist setatt $vm1 hdbchain $pm1,$pm2
}

# Report limit switch status for a given list of motors
proc limswi {args} {
  foreach m $args {
    if { [SplitReply [sicslist $m type]] == "Motor" } {
      set lims [$m send MG _LF`,_LR`]
      if { [lindex $lims 0 ] == 0 } {
         set FL "on "
      } else {
         set FL "off"
      }
      if { [lindex $lims 1 ] == 0 } {
        set RL on
      } else {
        set RL off
      }
    }
    clientput $m FL=$FL RL=$RL
  }
}
publish limswi user
