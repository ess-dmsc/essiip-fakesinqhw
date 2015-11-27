# Some useful functions for SICS configuration.

# Author: Ferdi Franceschini (ffr@ansto.gov.au)

source util/extra_utility.tcl
source util/eventutil.tcl
source util/motor_utility.tcl
source util/command.tcl
source util/write_tree.tcl

namespace eval environment { }
  # @brief Return the number of sensors for a given environment object
  proc ::environment::getnumsensors {sobj} {
    if [ catch {
      if {[SplitReply [environment_simulation]]=="true"} {
        set ns [getatt $sobj numsensors]
        return $ns
      } else {
        set ns [SplitReply [$sobj numsensors]]
        return $ns
      }
    } message ] {
      if {$::errorCode=="NONE"} {return $message}
      return -code error $message
    }
  }

  # @brief Return the list of sensor names for the given environment object
  proc ::environment::getsensorlist {sobj} {
    if [ catch {
      if {[SplitReply [environment_simulation]]=="true"} {
        set sl [ split [getatt $sobj sensorlist] , ]
        return $sl
      } else {
        set sl [ split [SplitReply [$sobj sensorlist]] , ]
        return $sl
      }
    } message ] {
      if {$::errorCode=="NONE"} {return $message}
      return -code error $message
    }
  }

  # @brief Create SICS variables for the environment controller
  # sensor readings which we use for feedback in the GumTree interface.
  #
  # These sensor-reading variables will be attached to the hdb tree
  # and updated at regular intervals
  #
  # @param sobj, SICS environment controller object name.
  # @return A space separated list of the sensor-reading variable names.
proc ::environment::mkSensors {sobj} {
  if [ catch {
    set sim_mode [SplitReply [environment_simulation]]
    set sensors [::environment::getsensorlist $sobj]
    foreach sensor $sensors {
      proc ::environment::${sobj}_${sensor} {} [ subst -nocommands {
        if {$sim_mode == "true"} {
          return [expr rand()]
        } else {
          return [SplitReply [$sobj $sensor]]
        }
      }]
      set ss_script ::environment::${sobj}_${sensor}
      publish $ss_script user
      sicslist setatt $ss_script  access read_only
      sicslist setatt $ss_script  privilege internal
      sicslist setatt $ss_script  long_name value
      sicslist setatt $ss_script  dtype float
      sicslist setatt $ss_script  dlen 1
      sicslist setatt $ss_script  data true
      sicslist setatt $ss_script  nxsave true
      sicslist setatt $ss_script  mutable true
      sicslist setatt $ss_script  control true
      sicslist setatt $ss_script  units [getatt $sobj units]
      sicslist setatt $ss_script  klass sensor
      sicslist setatt $ss_script  kind script
      append sensorlist [subst {
        $sensor {
          macro { $ss_script }
        }
      }]
    }
    return $sensorlist
  } message ] {
    if {$::errorCode=="NONE"} {return $message}
    return -code error $message
  }
}

# @brief Create the information structure
#
# @param sobj, name of SICS environment controller object
# @param paramlist a nested list of parameters and their attributes\n
# eg,  {heateron {priv user} range {priv manager}}\n
# this adds the heateron and range parameters with their access privilege.\n
# Note: The priv attribute is mandatory.
#
# eg ::environment::mkenvinfo tc1 {heateron {priv user} range {priv manager}}
proc ::environment::mkenvinfo {sobj paramlist} {
  lappend paramlist controlsensor {priv user}
  if [ catch {
    # Create polling procedure to update hdb sensor data nodes.
#    proc ::environment::${sobj}_poll [subst {{sobj $sobj}}] {
#      set sim_mode [SplitReply [environment_simulation]]
#      set sensors [::environment::getsensorlist $sobj]
#      if {$sim_mode == "true"} {
#        foreach ss  $sensors {
#          ${sobj}_${ss} [expr rand()]
#        }
#      } else {
#        foreach ss  $sensors {
#          ${sobj}_${ss} [SplitReply [$sobj $ss]]
#        }
#      }
#    }

    set setpoint_script ::environment::${sobj}_setpoint

::utility::macro::getset float $setpoint_script {args} {
	if {$args == ""} {
		return [tc1 setpoint]
	} else {
		tc1 setpoint $args
	}
}
sicslist setatt $setpoint_script klass @none
sicslist setatt $setpoint_script long_name setpoint
sicslist setatt $setpoint_script mutable true


    lappend env_macrolist $setpoint_script

    foreach {param attlist} $paramlist {
      array set atthash $attlist
      proc ::environment::${sobj}_${param} [subst {{val "@none"} {_sobj $sobj} {_param $param}}] {
        if {[SplitReply [environment_simulation]]=="true"} {
          if {$val=="@none"} {
            return [getatt ${_sobj} ${_param}]
          } else {
            sicslist setatt ${_sobj} ${_param} $val
          }
        } else {
          if {$val=="@none"} {
            return [SplitReply [${_sobj} ${_param}]]
          } else {
            ${_sobj} ${_param} $val
          }
        }
      }
      set ctrlss_script ::environment::${sobj}_${param}
      publish $ctrlss_script user
      sicslist setatt $ctrlss_script long_name ${param}
      sicslist setatt $ctrlss_script kind script
      sicslist setatt $ctrlss_script privilege $atthash(priv)
      sicslist setatt $ctrlss_script klass @none
      sicslist setatt $ctrlss_script data false
      sicslist setatt $ctrlss_script control true
      sicslist setatt $ctrlss_script nxsave false
      sicslist setatt $ctrlss_script dtype "text"
      sicslist setatt $ctrlss_script dlen 10
      sicslist setatt $ctrlss_script access rw
      lappend env_macrolist $ctrlss_script
    }

    # Create environment information structure for hdb
    set env_name [getatt $sobj environment_name]
    eval [subst {
      proc ::${sobj}_dict {} {
        return {
          NXenvironment {
            $env_name {
              macro {$env_macrolist}
              NXsensor {
                [::environment::mkSensors $sobj]
              }
            }
          }
        }
      }
    } ]
    publish ::${sobj}_dict mugger
    sicslist setatt ::${sobj}_dict kind hdb_subtree
    sicslist setatt ::${sobj}_dict klass environment
    sicslist setatt ::${sobj}_dict privilege user
    sicslist setatt ::${sobj}_dict long_name tempone
    sicslist setatt ::${sobj}_dict data true
    sicslist setatt ::${sobj}_dict control true
    sicslist setatt ::${sobj}_dict nxsave true
    sicslist setatt ::${sobj}_dict sdsinfo ::nexus::environment_controller::sdsinfo
    sicslist setatt ::${sobj}_dict savecmd ::nexus::environment_controller::save
  } message ] {
    if {$::errorCode=="NONE"} {return $message}
    return -code error $message
  }
}

## TODO put all the utility macros in the utility namespace
namespace eval utility {
  variable instrument_names [list bilby dingo echidna emu kookaburra kowari lyrebird pelican platypus quokka taipan wombat]
  variable sics_port
  set base_port 60000
  set currbase $base_port
  set valbase_port 60010
  set currvalbase $valbase_port
  foreach inst $instrument_names {
    array set sics_port [list\
      sics-telnet-$inst $currbase\
      sics-interrupt-$inst [expr {$currbase+1}]\
      sics-server-$inst [expr {$currbase+2}]\
      sics-quieck-$inst [expr {$currbase+3}]\
      sics-telnet-val-$inst $currvalbase\
      sics-interrupt-val-$inst [expr {$currvalbase+1}]\
      sics-server-val-$inst [expr {$currvalbase+2}]\
      sics-quieck-val-$inst [expr {$currvalbase+3}]\
    ]
    set currbase [expr {$currbase+100}]
    set currvalbase [expr {$currvalbase+100}]
  }
  namespace export instname;
  namespace export get_portnum;
  variable instrument_name;
  set instrument_name "";

# Convenience command for getting unadorned instrument name
  proc instname {} {
    variable instrument_name;
    set instrument_name [SplitReply [instrument]];
    proc ::utility::instname {} {
      variable instrument_name;
      return $instrument_name;
    }
    return $instrument_name;
  }

# Initialise the attributes of sobj
# to make it ready for adding to the hdb tree.
proc mkData {sobj name aklass args} {
  sicslist setatt $sobj long_name $name
  sicslist setatt $sobj nxalias $sobj
  sicslist setatt $sobj klass $aklass
  switch [getatt $sobj type] {
    "sicsvariable" {
      sicslist setatt $sobj kind hobj
      sicslist setatt $sobj data true
      sicslist setatt $sobj control true
      sicslist setatt $sobj nxsave true
      sicslist setatt $sobj privilege internal
      sicslist setatt $sobj mutable false
    }
    default {
      error "ERROR [info level -1] -> [info level 0]"
    }
  }
  array set attval $args
  foreach att {kind data control nxsave privilege nxalias mutable} {
    if {[info exists attval($att)]} {
      sicslist setatt $sobj $att $attval($att)
    }
  }
}
# Sets the privilege attribute when making a SICS variable
# access = spy, user, manager, internal, readonly
  proc mkVar {name type access {along_name x} {anxsave false} {aklass @none} {acontrol false} {adata false}} {
    array set sicsAccess {spy spy user user manager mugger internal internal readonly internal}
    VarMake $name $type $sicsAccess($access);
    sicslist setatt $name privilege $access;
    sicslist setatt $name kind hobj;
    sicslist setatt $name mutable false
    if {$access != "internal"} {
      sicslist setatt $name data $adata
      sicslist setatt $name control $acontrol
      sicslist setatt $name nxsave $anxsave
      sicslist setatt $name klass $aklass
      sicslist setatt $name long_name $along_name
    }
  }

  proc about {option args} {
    return [info $option $args];
  }
}
# Returns attribute name and value
proc getatt {sicsobj att} {
  if [catch {
    lindex [split [tolower_sicslist $sicsobj $att] =] 1
    } reply ] {
      return -code error "([info level 0]) $reply"
    } else {
      return $reply
    }
}

proc normalgetatt {sicsobj att} {
  if [catch {
    lindex [split [sicslist $sicsobj $att] =] 1
    } reply ] {
      return -code error $reply
    } else {
      return $reply
    }
}

proc ::utility::normalattlist {sicsobj} {
  if [ catch {
    foreach att [sicslist $sicsobj] {
      lappend atts [split [string range $att 0 end-1] =]
    }
    return [join $atts]
  } message ] {
    if {$::errorCode=="NONE"} {return $message}
    return -code error $message
  }
}
# @brief Determine if a SICS object implements the drivable interface.
#
# @param sicsobj, Name of a SICS object
# @return 1 if drivable, otherwise 0
proc is_drivable {sicsobj} {
  if [catch {
    getatt $sicsobj drivable
  } reply] {
    return -code error $reply
  }
  if {$reply == "true"} {
    return 1
  } else {
    return 0
  }
}

# Utility fucntion for setting the home and upper and lower
# limits for a motor
proc setHomeandRange {args} {
set usage "
Usage: setHomeandRange -motor motName -home homeVal -lowrange low -uprange high
eg
setHomeandRange -motor mchi -home 90 -lowrange 5 -uprange 7
this sets the home position to 90 degreess for motor mchi
with the lower limit at 85 and the upper limit at 97
"
if {$args == ""} {clientput $usage; return}
  array set params $args
  set motor $params(-motor)
  set home $params(-home)
  set lowlim [expr $home - $params(-lowrange)]
  set uplim [expr $home + $params(-uprange)]

  uplevel 1 "$motor softlowerlim $lowlim"
  uplevel 1 "$motor softupperlim $uplim"
  uplevel 1 "$motor home $home"
}

# Use this to create an array of named parameters to initialise motors.
proc params {args} {
  upvar #0 "" x;
  if [info exists x] {unset x}
  foreach {k v} $args {set x([string tolower $k]) $v}
}

# Parse motor readings for virtual motor scripts.
proc SplitReply { text } {
     set val_index [string first "=" $text]
     incr val_index
     return [string trim [string range $text $val_index end]]
}

# Sets motor position reading to pos by adjusting the softzero
proc setpos {motor pos args} {
    if {$args == ""} {
      set currPos [SplitReply [$motor]]
      set newPos $pos
    } else {
      set currPos $pos
      set newPos [lindex $args 0]
    }
    set oldZero [SplitReply [$motor softzero]]
    set newZero [expr $currPos - $newPos + $oldZero]
    uplevel #0 "$motor softzero $newZero"
}

proc getinfo {object} {
  set wc [format "%s_*" $object];
  set objlist [sicslist match $wc];
  foreach v $objlist {
    if { [SplitReply [sicslist $v type]]== "SicsVariable"} {
      clientput [$v];
    }
  }
}


# Convenience function for setting klass group and name attributes
# on sics object metadata
proc set_sicsobj_atts {sobj aklass agroup aname acontrol adata} {
  sicslist setatt $sobj klass $aklass;
  if {$agroup != "@none"} {
    sicslist setatt $sobj group $agroup;
  }
  sicslist setatt $sobj long_name $aname;
  sicslist setatt $sobj control $acontrol;
  sicslist setatt $sobj data $adata;
}


proc debug {args} {
  clientput $args
}
proc echo {args} {
  clientput $args
}

# @brief Check if a SICS object or Tcl object exists.
#
# @param obj, name of a SICS or Tcl object
# @return 1 if obj exists otherwise 0
proc ::utility::obj_exists {obj} {
  if { [string trim [sicslist match $obj ]] != "" || [info exists $obj] } {
    return 1
  } else {
    return 0
  }
}

proc ::utility::set_sobj_attributes {} {
  sicslist setatt getinfo privilege internal
  sicslist setatt setpos privilege internal
  sicslist setatt SplitReply privilege internal
  sicslist setatt instname privilege internal
}

proc ::utility::set_histomem_attributes {} {
  foreach hm [sicslist type histmem] {
    sicslist setatt $hm nxalias $hm
    sicslist setatt $hm mutable true
  }
}
proc ::utility::set_sct_object_attributes {} {
  foreach sobj [sicslist type SCT_OBJECT] {
    sicslist setatt $sobj data true
    sicslist setatt $sobj control true
    sicslist setatt $sobj nxsave true
    sicslist setatt $sobj mutable true
    sicslist setatt $sobj privilege user
    sicslist setatt $sobj kind scobj
  }
}
proc ::utility::set_motor_attributes {} {
# Bug: SICS-57 on Jira
# The first entry in [sicslist type motor] is 'motor' when
# we run the sicslist command on initialisation.  This is because
# The 'Motor' command has type motor, so we skip it with lrange.
  foreach m [lrange [sicslist type motor] 1 end] {
    sicslist setatt $m kind hobj
    sicslist setatt $m data true
    sicslist setatt $m control true
    sicslist setatt $m nxsave true
    sicslist setatt $m mutable true
    catch {
      # This block is specific to the dmc2280 driver.
      # Skip it for "tclmot" motors which don't
      # have 'units', 'part' or 'long_name' parameters
      sicslist setatt $m units [SplitReply [$m units]]
      sicslist setatt $m long_name [SplitReply [$m long_name]]
      set mpart [split [SplitReply [$m part] ] .]
      sicslist setatt $m klass [lindex $mpart 0]
      if {[llength $mpart] == 2} {
        sicslist setatt $m group [lindex $mpart 1]
      }
    }
    sicslist setatt $m nxalias $m
    switch [expr int([SplitReply [$m accesscode]])] {
      0 {sicslist setatt $m privilege internal}
      1 {sicslist setatt $m privilege manager}
      2 {sicslist setatt $m privilege user}
      3 {sicslist setatt $m privilege spy}
    }
  }
  foreach m [sicslist type configurablevirtualmotor] {
    sicslist setatt $m kind hobj
    sicslist setatt $m data true
    sicslist setatt $m control true
    sicslist setatt $m nxsave true
    sicslist setatt $m privilege user
    sicslist setatt $m nxalias $m
    sicslist setatt $m mutable true
  }
  foreach m [sicslist type TasMot] {
    sicslist setatt $m klass sample
    sicslist setatt $m long_name $m
    sicslist setatt $m kind hobj
    sicslist setatt $m data true
    sicslist setatt $m control true
    sicslist setatt $m nxsave true
    sicslist setatt $m privilege user
    sicslist setatt $m nxalias $m
    sicslist setatt $m mutable true
  }
}
proc ::utility::set_chopper_attributes {} {
  foreach ch [lrange [sicslist type chopperadapter] 1 end] {
    sicslist setatt $ch kind hobj
    sicslist setatt $ch data true
    sicslist setatt $ch control true
    sicslist setatt $ch nxsave true
    sicslist setatt $ch privilege user
    sicslist setatt $ch nxalias $ch
    sicslist setatt $ch long_name $ch
    sicslist setatt $ch mutable true
    sicslist setatt $ch klass disk_chopper
  }
}
proc ::utility::set_envcontrol_attributes {} {
  if [ catch {
    foreach ec [sicslist type environment_controller] {
    #TODO call mk
      array unset sobjatt
      array set sobjatt [attlist $ec]
      sicslist setatt $ec kind hobj
      sicslist setatt $ec data true
      sicslist setatt $ec control false
      sicslist setatt $ec nxsave true
      sicslist setatt $ec privilege user
      sicslist setatt $ec nxalias $ec
      sicslist setatt $ec mutable true
      if {[info exists sobjatt(klass)] == 0} {
        sicslist setatt $ec klass environment
      }
    }
  } message ] {
    if {$::errorCode=="NONE"} {return $message}
    return -code error $message
  }
}

# Retuns plain value of hdb node property
proc ::utility::hgetplainprop {hpath prop} {
  if [ catch {
    set propStr [string trim [lindex [split [hgetprop $hpath $prop] =] 1] ]
  } message ] {
    return -code error "([info level 0]) $message"
  }
  return $propStr
}

proc ::utility::GetUID {userName} {
  if [ catch {
  set fh [open /etc/passwd r]
    while {[gets $fh tmpName] != -1} {
      if {1 == [regexp "^$userName:" $tmpName]} {
        close $fh
          return [lindex [split $tmpName :] 2]
      }
    }
  close $fh
  error "\"$userName\" not found in /etc/passwd"
} message ] {
  if {$::errorCode=="NONE"} {return $message}
  return -code error $message
}
}

##\brief Determine if list l1 begins with list l2
proc lstarts_with {l1 l2} {
  foreach {e2} $l2 {e1} $l1 {
    if {$e2 == ""} {return 1}
    if {$e1 != $e2} {
      return 0
    }
  }
  return 1
}

##\brief Useful for converting port names to numbers for configuration parameters.
#
#\param port this can either be a port name or number
#\return always returns the port number
proc ::utility::get_portnum {port} {
  global env tcl_platform
  variable sics_port
  if [ catch {
  if [string is integer $port] {
    return $port
  } else {
    set home_path_list [split [string trim $env(HOME) /] /]
    set pwd_path_list [split [string trim $env(PWD) /] /]
    if [lstarts_with $pwd_path_list $home_path_list] {
      return [expr $sics_port($port) + 10*([::utility::GetUID $tcl_platform(user)]-999)]
    } else {
      return [portnum $port]
    }
  }
} message] {
  if {$::errorCode=="NONE"} {return $message}
  return -code error $message
}
}

##
# @brief Print callstack
proc ::utility::callstack {} {
  uplevel {
    for {set i 0} {$i > -[info level]} {incr i -1} {
      clientput [info level $i]
    }
  }
}

##
# @brief Raises an error if any options in arglist are not in the list of valid_options
# or if an option is missing a value
#
# @param arglist, is the list of name value pairs passed to you procedure
# @param valid_options, is a list of valid options eg [list "-opt1" "-opt2"]
proc ::utility::check_valid_options {arglist valid_options} {
  array set param ""

  if [ catch {
    foreach {opt val} $arglist {
      if { [string index $val 0] == "-" || $val == "" } {
        error "ERROR: argument for $opt is missing"
      }
      if [info exists param($opt)] {
        error "ERROR: duplicate option $opt"
      }
      set opt_valid "false"
      foreach valid_opt $valid_options {
        if {$opt == $valid_opt} {
          set opt_valid "true"
          set param($opt) $val
          break
        }
      }
      if {$opt_valid == "false"} {
        error "ERROR: $opt is an invalid option. It should be one of $valid_options"
      }
    }
  } message ] {
    if {$::errorCode=="NONE"} {return $message}
    return -code error "([info level 0]) $message"
  }
}

##
# @brief Raises an error if any of the required_options are not in the argument list arglist
proc ::utility::check_required_options {arglist required_options} {
  if [ catch {
    if {$arglist == ""} {
      error "ERROR: You must provide the following options: [join $required_options {, }]"
    }

    foreach req_opt $required_options {
      set option_missing "true"
      foreach {opt val} $arglist {
        if {$req_opt == $opt} {
          set option_missing "false"
          break
        }
      }
      if {$option_missing} {
        error "ERROR: Required option $req_opt is missing"
      }
    }
  } message ] {
    if {$::errorCode=="NONE"} {return $message}
    return -code error "([info level 0]) $message"
  }
}
##
# @brief Splits "args" list into a head and tail, useful for scripts
# where the first argument is a subcommand followed by an argument list.
#
# Usage: foreach {opt arglist} [::utility::get_opt_arglist $args] {}
proc ::utility::get_opt_arglist {args} {
  if [ catch {
    if {[llength $args] == 1} {
      set arguments [lindex $args 0]
    } else {
      set arguments $args
    }
    set opt [lindex $arguments 0]
    set arglist [lrange $arguments 1 end]
    return [list $opt $arglist]
  } message ] {
    if {$::errorCode=="NONE"} {return $message}
    return -code error $message
  }
}
# These functions handle a special nested list of name value pairs
# which can be represented as an XML element.
# Examples
# To make a new table you can just create an empty list, eg
# set newtable [list ]
# You can then fill your new table using tabset, eg
# ::utility::tabset newtable a/b/c {values {1 2 3}}
# newtable looks like this
# a {b {c {values {1 2 3}}}}
#
# NOTE you can generate the previous table anonymously with
# ::utility::tabmktable {a b c values {1 2 3}}
# -> a {b {c {values {1 2 3}}}}
#
# ::utility::tabmktable {NXgeometry geometry NXshape sicsvariable {shape size}}
# returns
# NXgeometry {geometry {NXshape {sicsvariable {shape size}}}}
# ::utility::tabxml hmm_table SAT
# ::utility::tabset hmm_table SAT/SPLIT/_ATTLIST_/MIDPOINT 256
# ::utility::tabget hmm_table SAT/SPLIT/_ATTLIST_/MIDPOINT
# ::utility::tabxml hmm_table SAT
# ::utility::tabget hmm_table OAT/_DATA_/T_MAX


# @brief Create a keyed list from a flat list.
# This is useful for inserting a subtable for a new branch.
# The branchpath is expressed as a list, ie a/b/c -> {a b c}
#
# @param flatlist eg {a b c values {1 2 3}}
# @return a keyed list, eg a {b {c {values {1 2 3}}}}
proc ::utility::tabmktable {flatlist} {
  if [ catch {
    if {[llength $flatlist] <= 2} {
      return $flatlist
    }
    set el [lindex $flatlist 0]
    set table [list $el \$subtable ]
    foreach el [lrange $flatlist 1 end-2] {
      set subtable [list $el \$subtable]
      set table [subst $table]
    }
    set subtable [lrange $flatlist end-1 end]
    set table [subst $table]
    return $table
  } message ] {
    if {$::errorCode=="NONE"} {return $message}
    return -code error $message
  }
}

# If some component of the path doesn't exist then return
# a list of indices up to the invalid step. Note if the
# first step doesn't exist this returns nothing which is a
# valid argument to lset and lindex representing the entire list
proc ::utility::tabindices {itable tpath} {
  if [ catch {
    upvar $itable table
    set pathlist [split $tpath /]
    set subtable $table
    set indices ""
    foreach element $pathlist {
      set datindex [expr 1+[lsearch $subtable $element]]
      if {$datindex==0} { break }
      lappend indices $datindex
      set subtable [lindex $subtable $datindex]
    }
    return $indices
  } message ] {
    if {$::errorCode=="NONE"} {return $message}
    return -code error $message
  }
}

proc ::utility::tabdel {itable tpath} {
  if [ catch {
    upvar $itable table
    set indices [::utility::tabindices table $tpath]
    if {[llength $indices] != [llength [split $tpath "/"]]} {
      return
    }
    set subtabpos [lrange $indices 0 end-1]
    set subtable [lindex $table $subtabpos]
    set datindex [lindex $indices end]
    set subtable [lreplace $subtable $datindex $datindex]
    incr datindex -1
    set subtable [lreplace $subtable $datindex $datindex]
    lset table $subtabpos $subtable
  } message ] {
    if {$::errorCode=="NONE"} {return $message}
    return -code error $message
  }
}

proc ::utility::tabget {itable tpath} {
  upvar $itable table
  set indices [::utility::tabindices table $tpath]
  if {[llength $indices] == [llength [split $tpath "/"] ]} {
    return [lindex $table $indices]
  } else {
    return
  }
}

proc ::utility::tabset {itable tpath val} {
  if [ catch {
    upvar $itable table
    set pathlist [split $tpath /]
    set indices [::utility::tabindices table $tpath]
    if {[llength $indices] == [llength $pathlist]} {
      lset table $indices $val
    } else {
      set subtable [lindex $table $indices]
      if {[llength $val] > 1} {
        set val [list $val]
      }
      set plist [ concat [lrange $pathlist [llength $indices] end] $val ]
      set subtable [concat $subtable [::utility::tabmktable $plist]]
      lset table $indices $subtable
    }
  } message ] {
    if {$::errorCode=="NONE"} {return $message}
    return -code error $message
  }
}

proc ::utility::tabxml {itable tag} {
  if [ catch {
    upvar $itable table
    set subtable [::utility::tabget table $tag]
    set attributes [::utility::tabget table $tag/_ATTLIST_]
    set att_text ""
    foreach {att attval} $attributes {
        append att_text "\n$att=\"$attval\""
    }
    set elements [::utility::tabget table $tag/_ELEMENTS_]
    foreach el $elements {
      append content "\n[::utility::tabxml subtable $el]"
    }
    append content [::utility::tabget table $tag/_CONTENT_]
    if {[string trim $att_text] == "" && [string trim $content] == ""} {
      return
    } else {
      return "<$tag $att_text>\n$content\n</$tag>"
    }
  } message ] {
    if {$::errorCode=="NONE"} {return $message}
    return -code error $message
  }
}

namespace eval ::utility::macro {}
##
# @brief Construct a 'getset' kind of macro. A getset macro
# will be added automatically to the hdb tree and its return
# value will be available for saving.
proc ::utility::macro::getset {type name arglist body} {
  proc ::$name $arglist [subst {
    $body
  }]

  publish $name spy
  if {$arglist == ""} {
    sicslist setatt $name  access read_only
  } else {
    sicslist setatt $name  access user
  }
  sicslist setatt $name  privilege user
  sicslist setatt $name  dtype $type
  sicslist setatt $name  dlen 1
  sicslist setatt $name  data true
  sicslist setatt $name  nxsave true
  sicslist setatt $name  mutable true
  sicslist setatt $name  control true
  sicslist setatt $name  klass @none
  sicslist setatt $name  kind getset
  sicslist setatt $name  savecmd ::nexus::macro::getset_save
  sicslist setatt $name  sdsinfo ::nexus::macro::getset_sdsinfo
}
proc hparPath {} {
  set hpath [sct]
  return [file dirname $hpath]
}
proc hsibPath {sibling} {
  set hpath [sct]
  return [file dirname $hpath]/$sibling
}

##
# @brief Handle exceptions caught by a 'catch' command.
# Note: You must use 'error' not 'return -code error' to
# raise errors from within a catch block.
#
# @param status, the status returned by the 'catch' command.
# @param message, the message set by the 'catch' command.
# @param args, optional info which gets appended to the error message.
#
# Call this as the LAST COMMAND in the command block or
# for loop which encloses the 'catch'
# Eg,
# set catch_status [ catch { ... code ...} message ]
# handle_exception $catch_status $message
proc handle_exception {status message args} {
  switch $status {
    0 {
      # TCL_OK, This is raised when you just drop out of the
      # bottom of a 'catch' command.
      return -code ok
    }
    1 {
      # TCL_ERROR
      return -code error "([info level -1]) $message: $args"
    }
    2 {
      # TCL_RETURN
      return -code return "$message"
    }
    3 {
      # TCL_BREAK
      return -code break
    }
    4 {
      # TCL_CONTINUE
      return -code continue
    }
    default {
    # Propogate user defined return codes with message
      return -code $status "$message"
    }
  }
}

proc hupdateif {path new_value {cmp_format ""}} {
  if { ${cmp_format} == "" } {
    if { [hpropexists ${path} compare_format] } {
      set compare_format [hgetpropval ${path} compare_format]
    } else {
      set compare_format ""
    }
  } else {
    set compare_format ${cmp_format}
  }
  if { ${compare_format} == "" } {
    if { [hval ${path}] != ${new_value} } {
      hupdate ${path} ${new_value}
    }
  } else {
    if { [format ${compare_format} [hval ${path}]] != [format ${compare_format} ${new_value}] } {
      hupdate ${path} ${new_value}
    }
  }
}

namespace import ::utility::*;
Publish getinfo spy
Publish setpos user
Publish SplitReply user
Publish instname user

