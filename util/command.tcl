set cmd_prop_list {kind command data false control true klass command nxsave false}
set cmd_par_prop_list {kind hobj data false control true nxsave false klass command}

#Useful for selecting arguments passed to a mapped function

# type = one of hipadaba types
# range restricts type values, maps to the argtype hlist property
# command {type:range p1 type:range p2} { ... }
proc command {acmdName arglist body} {
  global cmd_prop_list cmd_par_prop_list
  set NS [uplevel namespace current]
  set cmdName ${NS}::$acmdName
  variable ${cmdName}_param_list
  variable ${cmdName}_feedback_list
  if {[info exists ${cmdName}_param_list]} {
    unset ${cmdName}_param_list
  }
  if {[info exists ${cmdName}_feedback_list]} {
    unset ${cmdName}_feedback_list
  }
 # puts "cmdName: $cmdName"
    set params ""
    foreach {type_spec var} $arglist {
      lappend params $var
      foreach {type domain} [split $type_spec "="] {}
        lappend ${cmdName}_param_list $var ${cmdName}_par_$var
        set sicsvar [lindex [set ${cmdName}_param_list] end]
        # Make var with priv=user so we can use sicslist on it
        VarMake $sicsvar $type user
        # Set privilege internal to stop hdb builder adding it to hdb tree
        sicslist setatt $sicsvar privilege internal
        #FIXME Can argtype be replace with 'domain' then we setatt domain $domain
        if {$domain == ""} {
          sicslist setatt $sicsvar argtype $type
        } else {
          if {$type == "text"} {
            if {[string first , $domain] == -1} {
              sicslist setatt $sicsvar argtype $domain
            } else {
              sicslist setatt $sicsvar argtype $type
              sicslist setatt $sicsvar values $domain
            }
          } else {
            sicslist setatt $sicsvar argtype $type
            if [string match -nocase {*:*} $domain] {
              foreach {min max} [split $domain :] {}
              sicslist setatt $sicsvar min $min
              sicslist setatt $sicsvar max $max
            } else {
              sicslist setatt $sicsvar values $domain
            }
          }
        }
        sicslist setatt $sicsvar long_name $var
        foreach {att val} $cmd_par_prop_list {
          sicslist setatt $sicsvar $att $val
        }
    }
    set options {
      set __cmdinfo [info level 0]
      set __cmd [lindex $__cmdinfo 0]
      variable ${__cmd}_param_list
      switch -- [lindex $args 0] {
        -map {
          switch [lindex $args 1] {
            "param" {
              foreach {__var __param} [set ${__cmd}_param_list] {
                  eval [lindex $args 2] [lrange $args 3 end] $__param $__var
              }
              return
            }
            "feedback" {
              if {[info exists ${__cmd}_feedback_list] != 1} {
                return
              }
              foreach {__var __fbvar} [set ${__cmd}_feedback_list] {
                  eval [lindex $args 2] [lrange $args 3 end] $__fbvar $__var
              }
              return
            }
          }
        }
        -list {
          switch [lindex $args 1] {
            "param" {
              return [set ${__cmd}_param_list]
            }
            "feedback" {
              return [set ${__cmd}_feedback_list]
            }
          }
        }
        -set - -get {
          if {[lindex $args 1] == "feedback"} {
            set __vname [lindex $args 2]
            set __ptype fb
            if {[llength $args] > 3} {
              set __val [lindex $args 3]
            }
          } else {
            set __vname [lindex $args 1]
            set __ptype par
            if {[llength $args] > 2} {
              set __val [lindex $args 2]
            }
          }
          if {[llength [sicslist ${__cmd}_${__ptype}_${__vname}]] == 0} {
            error_msg "${__cmd}_${__ptype}_${__vname} doesnt exist"
            return
          }
          if {[info exists __val]} {
            ${__cmd}_${__ptype}_${__vname} $__val
            return
          } else {
            return [SplitReply [${__cmd}_${__ptype}_${__vname}]]
          }
        }
        -addfb {
          foreach {__type __var} [lrange $args 1 end] {
            set __sicsvar ${__cmd}_fb_${__var}
            VarMake $__sicsvar $__type user
            sicslist setatt $__sicsvar privilege internal
            sicslist setatt $__sicsvar control true
            sicslist setatt $__sicsvar data false
            sicslist setatt $__sicsvar nxsave false
            sicslist setatt $__sicsvar klass @none
            lappend ${__cmd}_feedback_list $__var $__sicsvar
          }
          return
        }
      }
    }
    # The foreach loop initialises the parameters for the command body
    # The 'if' statement makes sure that the SICS 'parameter' variables are only
    # updated if they change.
    proc $cmdName {args} [subst -nocommands {$options foreach n {$params} v \$args {set \$n \$v; if {\$v != [SplitReply [${cmdName}_par_\$n]]} {debug_msg "set ${cmdName}_par_\$n \$v"; ${cmdName}_par_\$n \$v}}; $body }]
    publish $cmdName user
    sicslist setatt $cmdName long_name $acmdName
    sicslist setatt $cmdName privilege user
    sicslist setatt $cmdName group [string map {:: ""} $NS]
    foreach {att val} $cmd_prop_list {
      sicslist setatt $cmdName $att $val
    }
}
