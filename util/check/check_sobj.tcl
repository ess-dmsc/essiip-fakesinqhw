fileeval util/check/query_sics.tcl
proc checksobj {} {
  global sobj_sicstype_list

  foreach sicstype $sobj_sicstype_list {
    global ${sicstype}_attlist
    clientput "Check $sicstype"
    foreach sobj [tolower_sicslist type $sicstype] {
      array unset sobj_attarray
      array set sobj_attarray [attlist $sobj]

      # Skip it if privilege is missing or set to "internal"
      if {[info exists sobj_attarray(privilege)]} {
        if {$sobj_attarray(privilege) == "internal"} {
          continue
        }
      } else {
          continue
      }

      foreach {att v} [set ${sicstype}_attlist] {
        foreach a $att {
        set attlist "$a @missing"
        if {[query_attval $sobj $attlist]} {
          clientput "$sobj: $a is missing"
          continue
        }
        set attlist "$a \{$v\}"
        if {![query_attval $sobj $attlist]} {
          clientput "$sobj: $a should be one of ($v) not [getatt $sobj $a]"
        }
      }
      }
    }
  }
}

publish checksobj user
