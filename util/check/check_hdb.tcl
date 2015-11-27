## \file
#  Must be loaded into an instance of SICS with fileeval
# eg
#    fileeval tests/query_sics.tcl
fileeval util/check/query_sics.tcl
set hdb_prop_list {
  {control data} {true false}
}
proc checknode {node} {
  global hdb_prop_list
  foreach {att v} $hdb_prop_list {
    foreach a $att {
    set query "$a @missing"
    if {[query_propval $node $query]} {
      clientput "$node: $a is missing"
        continue
    }
    set query "$a \{$v\}"
    if {![query_propval $node $query]} {
      clientput "$node: $a should be one of ($v) not [::utility::hgetplainprop $node $a]"
    }
  }
  }
}
proc checkhdb {{hpath "/"}} {
  global hdb_prop_list
  if {$hpath == "/"} {
    foreach hp [hlist /] {
      checknode /$hp
      checkhdb /$hp
    }
    clientput OK
  } else {
    foreach hp [hlist $hpath] {
      checknode $hpath/$hp
      checkhdb $hpath/$hp
    }
  }
}
publish checkhdb user
