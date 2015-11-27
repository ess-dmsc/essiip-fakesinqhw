#!/usr/bin/env tclsh

# Author: Ferdi Franceschini (ffr@ansto.gov.au)

# Load troubleshooting setup
source dmc2280_util.tcl
source troubleshoot_setup.tcl
source motorinfo.tcl

if { $argc > 0 } {
  set configFileName [lindex $argv 0]
}

# Use this to create an array of named parameters to initialise motors.
proc params {args} {
  upvar 1 "" x;
  if [info exists x] {unset x}
  foreach {k v} $args {set x([string tolower $k]) $v}
}

namespace eval sics_config {
proc loadConfig {fName} {
  variable ContList
  if [info exists ContList] {unset ContList}
# Temporarily define unknown proc to skip undefined procs
  rename ::unknown _unknown
  proc ::unknown {args} {}
  if [catch {uplevel #0 source $fName} errMsg] {
    rename ::unknown ""
    rename _unknown ::unknown
    error $errMsg
  } else {
    rename ::unknown ""
    rename _unknown ::unknown
  }
  if [catch {set ContList [uplevel #0 info vars dmc2280_controller*]} result] {error $result}
  if {[llength $ContList] == 0} {error "Error: There are no dmc2280_controllerN(host/port) arrays in the $fName configuration file"}
  #Add the controller to the sics_config namespace
  foreach c $ContList {upvar #0 $c cont; puts "$c IP:port = $cont(host):$cont(port)"}
}

proc subExists {contName sub} {
  upvar #0 $contName controller
  if [catch {::dmc_sendCmd $controller(socket) "LS $sub,0"} errMsg] {
    error "Subroutine $sub does not exist on controller $contName"
  }
  ::dmc_receive $controller(socket)
}

# Returns -1 if thread is not running, line number if it is
proc checkThread {contName thnum} {
  upvar #0 $contName controller
  ::dmc_sendCmd $controller(socket) "MG _XQ$thnum"
  set reply [::dmc_receive $controller(socket) ]
  if {$reply == -1} {
  error "Thread $thnum not running on controller $contName"
  }
  return $reply
}

# GUI STUFF
  package require Tk
  variable ContList
  global ldFrame
  set ldFrameName ".loadFile"
  set ldFrame(button) $ldFrameName.ldConf
  set ldFrame(entry) $ldFrameName.ldEntry


  proc ::guiLoadC {} {
    ::sics_config::loadConfig [eval $::sics_config::ldFrame(entry) get]
  }

  proc ::guiConnect {w cont} {
  ::dmc_connect $cont
  $w configure -activebackground green
  $w configure -background green
  }

  proc ::guiCheckSubs {w cont} {
    global contSubs
    foreach sub $contSubs($cont) {
      ::sics_config::subExists $cont $sub
    }
    $w configure -activebackground green
    $w configure -background green
  }

  proc ::guiCheckThreads {w cont} {
    global contThreads
    foreach thr $contThreads($cont) {
      ::sics_config::checkThread $cont $thr
    }
    $w configure -activebackground green
    $w configure -background green
  }

  frame $ldFrameName
  pack $ldFrameName
  button $ldFrame(button) -text "Load config" -command {guiLoadC; ::sics_config::mkGui}
  entry $ldFrame(entry) -textvariable configFileName -width -1
  pack $ldFrame(button) -side left
  pack $ldFrame(entry) -side left


  proc mkGui {} {
  variable ContList
  lappend Headings $ContList
  frame .t -bg black
  table .t $ContList
  pack .t
  testgui
  }
  proc table {w headings args} {
    set r 0

        foreach name $headings {
            lappend Header [label $w.$name -text $name]
        }
        foreach name $headings {
          lappend Connect [button $w.connect$name -text connect -command "guiConnect $w.connect$name $name"]
          lappend CheckSubs [button $w.chkSubs$name -text "Check subs" -command "guiCheckSubs $w.chkSubs$name $name"]
          lappend CheckThreads [button $w.chkThrs$name -text "Check threads" -command "guiCheckThreads $w.chkThrs$name $name"]
        }
        eval grid $Header -sticky news -padx 1 -pady 1
        eval grid $Connect -sticky news -padx 1 -pady 1
        eval grid $CheckSubs -sticky news -padx 1 -pady 1
        eval grid $CheckThreads -sticky news -padx 1 -pady 1

}
}

