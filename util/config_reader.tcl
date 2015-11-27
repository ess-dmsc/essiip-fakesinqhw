# Configuration (*.ini) file reader for SICS
# author Douglas Clowes (dcl@ansto.gov.au)
namespace eval config_reader {
  variable version 2.0
}

# return a list of section names from the dict
proc config_reader::get_sections {the_dict} {
  upvar 1 $the_dict db
  return [dict keys $db]
}

# return a list of variables in the named section of the dict
proc config_reader::get_variables {the_dict section} {
  upvar 1 $the_dict db
  return [dict keys [dict get $db $section]]
}

# return the value of the named variable in the named section
proc config_reader::get_var {the_dict section varname} {
  upvar 1 $the_dict db
  set varname [string tolower $varname]
  if {![dict exists $db $section]} {
    error "Section not found: $section"
  }
  if {![dict exists [dict get $db $section] $varname]} {
    error "Variable not found: $varname"
  }
  return [dict get $db $section $varname]
}

# add a new section to the dictionary
proc config_reader::add_section {the_dict section} {
  upvar 1 $the_dict db

  if {![dict exists $db $section]} {
    dict set db $section [dict create]
  }
}

# add a new section/variable and set its value
proc config_reader::set_var {the_dict section varname value} {
  upvar 1 $the_dict db
  if {![dict exists $db $section]} {
    config_reader::add_section db $section
  }
  set varname [string tolower $varname]
  dict set db $section $varname $value
}

# Load the named configuration file and return the dict
proc config_reader::parse_file {filename} {
  variable dictionary [dict create]
  variable cursection
  set line_no 1
  set fd [open $filename "r"]
  while {![eof $fd]} {
    set line [string trim [gets $fd] " "]
    if {$line == ""} continue
    switch -regexp -- $line {
      ^#.* { }
      ^\\[.*\\]$ {
        set cursection [string trim $line \[\]]
        config_reader::add_section dictionary $cursection
      }
      .*=.* {
        # split on the '=' and trim leading and trailing spaces
        set pair [split $line =]
        set name [string trim [lindex $pair 0] " "]
        set value [string trim [lindex $pair 1] " "]
        # Remove matching quotes on both ends (single, double and braces)
        if { [string index $value 0] == "'" && [string index $value end] == "'" } {
          set value [string range $value 1 end-1]
        } elseif { [string index $value 0] == "\"" && [string index $value end] == "\"" } {
          set value [string range $value 1 end-1]
        } elseif { [string index $value 0] == "{" && [string index $value end] == "}" } {
          set value [string range $value 1 end-1]
        }
        config_reader::set_var dictionary $cursection $name $value
      }
      default {
        error "Error parsing $filename (line: $line_no): $line"
        }
      }
      incr line_no
  }
  close $fd
  return $dictionary
}

# Load the named file with parse_file print and return the dict for testing
proc config_reader::dump {{the_config startup.ini}} {
  set my_dict [config_reader::parse_file $the_config]
  puts "Dict: $my_dict"
  foreach s [config_reader::get_sections my_dict] {
    set section "$s"
    puts "\n\[$section\]"
    foreach n [config_reader::get_variables my_dict $s] {
      set name "$n"
      set value "[config_reader::get_var my_dict $section $n]"
      puts "  $name = $value"
    }
  }
  return $my_dict
}

# This code is for i=unit testing in the tclsh executable
if { "[lindex [split [info nameofexecutable] "/"] end]" == "tclsh"} {
  set filename "/tmp/test_[pid].ini"
  set sects [list]
  lappend sects "\[Section_1\]"
  lappend sects "\[Section_2\]"
  lappend sects "\[Section_3\]"
  set vrbls [list]
  lappend vrbls "var1 = val1"
  lappend vrbls "var2 = val2 with multiple words"
  lappend vrbls "Var3 = Val3 with multiple words"
  set fd [open $filename "w"]
  foreach sect $sects {
    puts $fd $sect
    foreach vrbl $vrbls {
      puts $fd $vrbl
    }
  }
  close $fd
  set the_dict [config_reader::dump $filename]
  set v1 [config_reader::get_var the_dict "Section_1" "var1"]
  set v2 [config_reader::get_var the_dict "Section_2" "var2"]
  set v3 [config_reader::get_var the_dict "Section_3" "Var3"]
  puts "v1 = $v1"
  puts "v2 = $v2"
  puts "v3 = $v3"
}
