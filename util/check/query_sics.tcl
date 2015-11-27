proc query_nameval {query nameval_list} {
  if {[lindex $query 0] == "-not"} {
    return [expr { ! [_query_nameval [lrange $query 1 end] $nameval_list] }]
  } else {
    return [_query_nameval  $query $nameval_list]
  }
}
proc _query_nameval {query nameval_list} {
  array set proparr $nameval_list
  foreach {prop val} $query {
    if {[lindex $val 0] == "-not"} {
      set test 0
      set val [lrange $val 1 end]
    } else {
      set test 1
    }
    if {[info exists proparr($prop)]} {
      if {$val == "@missing"} {
        return 0
      }
      if {$val == "@any"} {
        continue
      }
    } else {
      if {$val == "@missing"} {
        continue
      } else {
        return 0
      }
    }
    switch $val {
      "alpha" {
        if {[string is alpha $proparr($prop)] == $test} {
          continue
        } else {
          return 0
        }
      }
      "text" {
        if {[string is wordchar $proparr($prop)] == $test} {
          continue
        } else {
          return 0
        }
      }
      "print" {
        if {[string is print $proparr($prop)] == $test} {
          continue
        } else {
          return 0
        }
      }
      "float" {
        if {[string is double $proparr($prop)] == $test} {
          continue
        } else {
          return 0
        }
      }
      "int" {
        if {[string is integer $proparr($prop)] == $test} {
          continue
        } else {
          return 0
        }
      }
      default {
          if {([lsearch $val $proparr($prop)] >= 0) == $test} {
            continue
          } else {
            return 0
          }
      }
    }
  }
  return 1
}

proc query_propval {hp query} {
    return [ query_nameval $query [hlistprop $hp tcllist] ]
}
proc query_attval {sobj query} {
    return [ query_nameval $query [attlist $sobj] ]
}
##
# prop_list list of property name value pairs
# value can be a @any @missing a single value or a list optionally preceded by -not
# listnode / {data true sicsdev @missing  type {-not part instrument nxvgroup}}
proc listnode {hpath prop_list} {
  if {$hpath == "/"} {
    foreach hp [hlist /] {
      if [query_propval /$hp $prop_list] {
        clientput "/$hp"
      }
      listnode /$hp $prop_list
    }
  } else {
    foreach hp [hlist $hpath] {
      if [query_propval $hpath/$hp $prop_list] {
        clientput "$hpath/$hp"
      }
      listnode $hpath/$hp $prop_list
    }
  }
}

proc listsobj {sicstype att_list} {
  foreach sobj [sicslist type $sicstype] {
      if [query_attval $sobj $att_list] {
        clientput "$sobj"
      }
  }
}

publish query_propval user
publish query_attval user
publish listnode user
publish listsobj user
