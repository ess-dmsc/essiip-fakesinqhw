  namespace eval ::utility {}
  proc ::utility::writeNode {tc_root { do_props 0 } { level 0 }} {
    if [ catch {
      set space [string repeat "  " $level]
      if [ catch {
        set val [hval $tc_root]
      } message ] {
        clientput "Error in writeNode/hval for $tc_root : $message"
        return
      }
      set nam [lindex [split $tc_root "/"] end]
      if [ catch {
        if {"$val" == ""} {
          set line "$nam ([hinfo $tc_root])"
        } else {
          set line "$nam ([hinfo $tc_root]) = $val"
        }
        clientput "$space* $line"
      } message ] {
        clientput "Error in writeNode/hinfo for $tc_root : $message"
      }
      if {"[string tolower "$do_props"]" == "-prop"} {
        if [ catch {
          set props [lsort [hlistprop $tc_root]]
          #clientput "<<$props>>"
          foreach prop $props {
            if [ catch {
              # guard against embedded spaces producing false properties
              #clientput "prop: $prop"
              set flds [split $prop "="]
              #clientput "flds: $flds"
              if {[llength $flds] > 1} {
                set nam [lindex $flds 0]
                if {[hpropexists $tc_root $nam]} {
                  set rst [hgetpropval $tc_root $nam]
                  clientput "$space    - $nam=$rst"
                }
              }
            } message ] {
              clientput "Error in writeNode/hlistprop for $tc_root : $message"
            }
          }
        } message ] {
          clientput "Error in writeNode/hlistprop for $tc_root : $message"
        }
      }
      foreach node [lsort [hlist $tc_root]] {
        ::utility::writeNode $tc_root/$node "$do_props" [expr {$level + 1}]
      }
    } message ] {
      clientput "Error in writeNode for $tc_root : $message"
    }
  }

  proc writeTree {tc_root {do_props 0}} {
    clientput "$tc_root"
    ::utility::writeNode $tc_root $do_props 1
    return "Done"
  }
publish writeTree user

