#!/usr/bin/env tclsh
# @file Generate a motor configuration file from CSV files of name value pairs.
#
# Input: List of CSV files.
# Output files:
#  generated_motor_configuration.tcl
#  genmotconf_report.log
#  genmotconf_errors.log: Lists missing attributes if a spec is incomplete.
#  missing_attlist.csv
#
# TODO
# Optionally split configuration accross multiple files for cases where
# axes are swapped out, eg Eulerian cradles, sample-stick rotation.
# This could be done by supplying a file which contains lines as follows,
# CFG_NAME1,m1 m2 m3
# CFG_NAME2,m4 m5 m6
# Where CFG_NAMEn is the name of a config file and mn's are motor names.
# In this case generated_motor_configuration.tcl will define the header and asyncqueues.
# The motor_configuration.tcl file would then be hand-coded to fileeval the CFG_NAMEn files as required.
#
source [file dirname $argv0]/genmotconf_procs.tcl

set ERRCNT 0
set MOTCFG_CNT 0
set CANCFG_CNT 0
set FAILED_MOTCFG_CNT 0
# MOT_ATTLIST: Attributes required to configure an axis without an encoder
# ENC_ATTLIST: Attributes required to describe an encoder.
#              NOTE Encoder readings for the limit switch positions are required.
#                   If the encoder "absenchome" reading is not supplied it is set equal to rev_enc_lim
# ENCMOT_ATTLIST: Attributes which describe an axis which has both a motor and encoder.
# OPT_ATTLIST: Optional attributes which may define recommended settings as well as descriptive information.
# REQ_ATTLIST: List of attributes required to generate a configuration for a motor object.
# SICS_CFG_MOTATTLIST: Extra attributes required to configure a motor object in SICS.
# SICS_CFG_ENCMOTATTLIST: Extra attributes required to configure a motor object with an encoder in SICS.
# ALL_ATTRIBUTES: List of all possible attributes recognised by this program.
#
# Attributes which are not in these lists are assumed to define the encoder
# readings for each position on an axis which has a set of meaningful positions
# such as apertures or multi-sample tables.
set MOT_ATTLIST [lsort {axis mc steps_per_x}]
set ENC_ATTLIST [lsort {cnts_per_x fwd_enc_lim rev_enc_lim}]
set ENCMOT_ATTLIST [lsort [concat $MOT_ATTLIST $ENC_ATTLIST]]
set OPT_ATTLIST [lsort {axis_number dflt_accel_steps dflt_decel_steps dflt_speed_steps description speed accel decel}]
set SICS_CFG_MOTATTLIST [lsort {home fwd_lim rev_lim maxspeed maxaccel maxdecel part units}]
set SICS_CFG_ENCMOTATTLIST [lsort [concat absenchome $SICS_CFG_MOTATTLIST]]
set REQ_ATTLIST [lsort [concat $MOT_ATTLIST $SICS_CFG_MOTATTLIST]]
set ALL_ATTRIBUTES [lsort [concat $ENCMOT_ATTLIST $SICS_CFG_ENCMOTATTLIST $OPT_ATTLIST]]

set arg0 [lindex $argv 0]
if {[string match $arg0 "help"] || [string match $arg0 "--help"] || [string match $arg0 "-h"]} {
  puts "\nUsage: $argv0 file1.csv file2.csv ..."
  puts "\nThe following parameters must be provided in the CSV files,"
  puts "   $MOT_ATTLIST"
  puts "\nA motor with an encoder must also provide these parameters,"
  puts "   $ENC_ATTLIST"
  puts "\nOptionally these parameters may also be provided"
  puts "   $OPT_ATTLIST"
  puts "\nIf these motor parameters are not provided they will be generated,"
  puts "   $SICS_CFG_MOTATTLIST"
  puts "\nIf an axis has an encoder these parameters will be generated,"
  puts "   $SICS_CFG_ENCMOTATTLIST"
  exit 0
}

array set autogen_attarr {}
set scriptname [file tail [file rootname $argv0]]
set file_list $argv

set fhr [open ${scriptname}_report.log "w"]
set fhe [open ${scriptname}_errors.log "w"]

# @brief Generate a default value for missing attributes.
# @param mot motor name
# @param att attribute name
# @return value for attribute or NOATT if no attribute should be generated.
proc gen_attval {mot att} {

  if {[set ::${mot}_attarr(steps_per_x)] < 0} {
    set sign -1.0
  } else {
    set sign 1.0
  }
  if { [info exists ::${mot}_encatts(cnts_per_x)] } {
    set cnts_per_x_val [expr double([set ::${mot}_encatts(cnts_per_x)])]
  }
  if { [info exists ::${mot}_encatts(rev_enc_lim)]} {
    set rev_enc_lim_val [expr double([set ::${mot}_encatts(rev_enc_lim)])]
  }
  if { [info exists ::${mot}_encatts(fwd_enc_lim)]} {
    set fwd_enc_lim_val [expr double([set ::${mot}_encatts(fwd_enc_lim)])]
  }
  if [info exists ::${mot}_attarr(absenchome)] {
    set enc_home_val [expr double([set ::${mot}_attarr(absenchome)])]
  } else {
    if {$sign < 0} {
      set enc_home_val [expr double([set ::${mot}_encatts(fwd_enc_lim)])]
    } else {
      set enc_home_val [expr double([set ::${mot}_encatts(rev_enc_lim)])]
    }
  }
  if [info exists ::${mot}_attarr(home)] {
    set home_val [expr double([set ::${mot}_attarr(home)])]
  } else {
    set home_val 0
  }
  switch $att {
    "absenchome" {
      if [info exists ::${mot}_encatts(rev_enc_lim)] {
        return $enc_home_val
      } else {
        return "NOATT"
      }
    }
    "maxspeed" {return 1}
    "maxaccel" {return 1}
    "maxdecel" {return 1}
    "rev_lim" {
      if { [info exists ::${mot}_encatts(rev_enc_lim)] && [info exists ::${mot}_encatts(cnts_per_x)] } {
        if {$sign < 0} {
          return [expr {($fwd_enc_lim_val - $enc_home_val) / $cnts_per_x_val + $home_val}]
        } else {
          return [expr {($rev_enc_lim_val - $enc_home_val) / $cnts_per_x_val + $home_val}]
        }
      } else {
        return 0
      }
    }
    "home" {return 0}
    "fwd_lim" {
      if { [info exists ::${mot}_encatts(fwd_enc_lim)] && [info exists ::${mot}_encatts(cnts_per_x)] } {
        if {$sign < 0} {
          return [expr {($rev_enc_lim_val - $enc_home_val) / $cnts_per_x_val + $home_val}]
        } else {
          return [expr {($fwd_enc_lim_val - $enc_home_val) / $cnts_per_x_val + $home_val}]
        }
      } else {
        return 1
      }
    }
    "part" {return "instrument"}
    "units" {return "xxx"}
  }
}

################################################################################
# Parse all files and generate ::mn(matt) and ::controllers(cn)
foreach f $file_list {
  parse_file $f $fhr $fhe
}

################################################################################
# GENERATE MOTOR CONFIGURATION FILE
puts $fhr "GENERATE MOTOR CONFIGURATIONS"
puts $fhe "GENERATE MOTOR CONFIGURATIONS"
puts $fhe "Required attributes: $REQ_ATTLIST"

set fhmc [open "generated_motor_configuration.tcl" "w"]
# Write configuration file header and make asyncqueues
mk_cfg_header $fhmc
puts $fhmc ""
foreach mn [lsort -dictionary [array names motor_attcnt]] {
  set encmot_attlist [lsort [array names ${mn}_encatts]]
  set mot_attlist [lsort [concat [array names ${mn}_attarr] [array names ${mn}_encatts]]]
  set num_encatts_defined [llength $encmot_attlist]
  set posnum 0

  # Decide if a motor configuration should be generated.
  if [subset $ALL_ATTRIBUTES $mot_attlist] {
    set mk_config 1
  } elseif [subset $REQ_ATTLIST $mot_attlist] {
    set mk_config 1
  } else {
    set mk_config 0
  }

  # Does this motor have an absolute encoder?
  if {$num_encatts_defined > 0} {
    set absenc 1
  } else {
    set absenc 0
  }

  # Decide if a list missing attributes with default values should be written.
  if [subset $ENCMOT_ATTLIST $mot_attlist] {
    set mk_missing_atts 1
  } elseif [subset $MOT_ATTLIST $mot_attlist] {
    set mk_missing_atts 1
  } else {
    set mk_missing_atts 0
  }

  if [info exists ${mn}_encatts(cnts_per_x)] {
  # Assume that the values of any attributes we don't recognise are encoder
  # readings for a "posit" motor.
    set posit_list {}
    #TODO Sort posits by value can we take into acount if cnts_per_x is -ve or +ve?
    set posit_nameval_list {}
    foreach att [setdiff $mot_attlist $ALL_ATTRIBUTES] {
      if [regexp {^pos\d\d*$} $att] {
        lappend posit_nameval_list "$att [set ${mn}_attarr($att)]"
      }
    }
    if {[llength $posit_nameval_list] > 0} {
      set posnum 0
      if { [set ${mn}_encatts(cnts_per_x)] > 0} {
        set sorted_nv_list [join [lsort -integer -increasing -index 1 $posit_nameval_list]]
      } else {
        set sorted_nv_list [join [lsort -integer -decreasing -index 1 $posit_nameval_list]]
      }
      foreach {att v} $sorted_nv_list {
        incr posnum
        lappend posit_list "posit_${posnum} \$${mn}_$att"
        # puts "posit_${posnum} \$${mn}_$att = $v"
      }
    }
  }

  # Generate a motor configuration and/or a list of missing attributes.
  if ${mk_config} {
    mk_motconf $mn $fhmc $absenc $posnum posit_list
    puts $fhr "Configured $mn"
    incr MOTCFG_CNT
  } else {
    set missing_motatts [setdiff $MOT_ATTLIST $mot_attlist]
    set missing_encatts [setdiff $ENC_ATTLIST $encmot_attlist]
    set num_missing_motatts [llength $missing_motatts]
    set num_missing_encatts [llength $missing_encatts]
    if { $num_missing_encatts > 0 && $absenc} {
      puts $fhe "$mn: found partial config for an axis with an absolute encoder,"
      puts $fhe "    need: ([concat $missing_motatts $missing_encatts]) to configure the $mn motor with an encoder"
    } elseif { $num_missing_motatts > 0 } {
      puts $fhe "$mn: found partial config for an axis,"
      puts $fhe "    need: ($missing_motatts) to configure $mn motor"
      puts $fhe "    also need: ($missing_encatts) if $mn has an encoder"
    }
    incr FAILED_MOTCFG_CNT
    incr ERRCNT
    if {$mk_missing_atts} {
      set undef_atts [setdiff [lsort "absenchome $SICS_CFG_MOTATTLIST"] $mot_attlist]
      foreach att $undef_atts {
        set attval [gen_attval $mn $att]
        if {$attval != "NOATT"} {
          if [string is double $attval] {
            set attval [format "%.4f" $attval]
          }
          lappend autogen_attarr($mn) "${mn}_$att,$attval"
        }
      }
    }
  }
  if {[info exists ::${mn}_attarr(dflt_speed_steps)] && ![info exists ${mn}_attarr(speed)]} {
    set speed_phys_units [ expr abs(double([set ::${mn}_attarr(dflt_speed_steps)]) / [set ::${mn}_attarr(steps_per_x)]) ]
    lappend ::autogen_attarr($mn) "${mn}_speed,[format "%.4f" $speed_phys_units]"
  }
  if {[info exists ::${mn}_attarr(dflt_accel_steps)] && ![info exists ${mn}_attarr(accel)]} {
    set accel_phys_units [ expr abs(double([set ::${mn}_attarr(dflt_accel_steps)]) / [set ::${mn}_attarr(steps_per_x)]) ]
    lappend ::autogen_attarr($mn) "${mn}_accel,[format "%.4f" $accel_phys_units]"
  }
  if {[info exists ::${mn}_attarr(dflt_decel_steps)] && ![info exists ${mn}_attarr(decel)]} {
    set decel_phys_units [ expr abs(double([set ::${mn}_attarr(dflt_decel_steps)]) / [set ::${mn}_attarr(steps_per_x)]) ]
    lappend ::autogen_attarr($mn) "${mn}_decel,[format "%.4f" $decel_phys_units]"
  }
}

# If there are any autogenerated attributes then write them to a file.
puts ""
if {[array size autogen_attarr] > 0} {
  set fh [open "missing_attlist.csv" "w"]
  puts "The attributes with default values needed to complete the configuration of the following motors has been written to missing_attlist.csv,"
  foreach n [lsort [array names autogen_attarr]] {
    puts -nonewline "$n "
    foreach attval [lsort $autogen_attarr($n)] {
      puts $fh $attval
    }
  }
  close $fh
  puts "\n"
  puts "Rename missing_attlist.csv and redo to generate a configuration file which also includes the motors listed above."
  puts "Eg,"
  puts "   mv missing_attlist.csv sicsmot_attlist.csv"
  puts ""
}

# The SICS init code calls motor_set_sobj_attributes. It can be redefined in
# the motor_configuration.tcl file.
puts $fhmc "proc motor_set_sobj_attributes {} {}"
puts stderr "Generated $MOTCFG_CNT motor driver configurations"
puts $fhr "Generated $MOTCFG_CNT motor driver configurations"
puts stderr "Found $FAILED_MOTCFG_CNT incomplete motor configurations. See ${scriptname}_errors.log and ${scriptname}_report.log"
puts $fhe "Found $FAILED_MOTCFG_CNT incomplete motor configurations"

close $fhmc
close $fhr
close $fhe

if {$ERRCNT > 0} {
  puts stderr "Finished with $::ERRCNT errors"
}
