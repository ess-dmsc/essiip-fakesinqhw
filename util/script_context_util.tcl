namespace eval ::scobj { }
proc ::scobj::set_required_props {hpath} {
  foreach child [hlist $hpath] {
    hsetprop $hpath/$child data false
    ::scobj::set_required_props $hpath/$child
  }
}

proc ::scobj::hinit_nodeprops {node hpath} {
  hsetprop $hpath nxalias $node
  foreach {prop propval} [subst {
    control true
    data true
    nxsave true
    mutable true
    klass parameter
    sdsinfo ::nexus::scobj::sdsinfo
    long_name $node
  }] {
    if {[hpropexists $hpath $prop] == false} {
      hsetprop $hpath $prop $propval
    }
  }
}
proc ::scobj::hinit_scobjprops {scobj hpath} {
  if {[hpropexists $hpath klass]} {
    sicslist setatt $scobj klass [hgetpropval $hpath klass]
  }
  if {[hpropexists $hpath long_name]} {
    sicslist setatt $scobj long_name [hgetpropval $hpath long_name]
  } else {
    sicslist setatt $scobj long_name $scobj
  }
  if [sicslist exists $scobj "argtype"] {
    hsetprop $hpath argtype [SplitReply [sicslist $scobj argtype]]
  }
  if [sicslist exists $scobj "values"] {
    hsetprop $hpath values [SplitReply [sicslist $scobj values]]
  }
  hsetprop $hpath sicsdev $scobj
  ::scobj::hinit_nodeprops $scobj $hpath
}
##
# @brief Initialise the hdb properties required for generating the GumTree interface and
# saving data for script context objects
# @param scobj, name of script context object
# @param par, optional parameter
proc ::scobj::hinitprops {scobj args} {
  if {$args == ""} {
    set hpath /sics/$scobj
    ::scobj::hinit_scobjprops $scobj $hpath
  } else {
    set hpath /sics/$scobj
    ::scobj::hinit_scobjprops $scobj $hpath
    foreach p $args {
      set hpath /sics/$scobj/$p
      set idPath [string map {/ _} $p]
      ::scobj::hinit_nodeprops ${scobj}_$idPath $hpath
    }
  }
}

##
# @brief find the node with property 'sicsdev' matching the given name
# start at top (or path) and work down
# @param name, the name of the device we are looking for (e.g. 'tc1')
# @param path, optional starting path (e.g. '/sample')
proc ::scobj::find_sicsdev {name {path "/"}} {
  foreach node [hlist ${path}] {
    if { [hpropexists ${path}/${node} sicsdev] } {
      if { [string match -nocase "${name}" "[hgetpropval ${path}/${node} sicsdev]" } {
        return [string map {// /} ${path}/${node}]
      }
    }
    set result [find_dev ${name} ${path}/${node}]
    if { ${result} != "" } {
      return [string map {// /} ${result}]
    }
  }
  return ""
}

##
# @brief find the node with the property 'type' matching 'sct_object'
# start at the bottom and work up
# @param path, the path of the node where we start looking (e.g. '[sct]')
proc ::scobj::find_myobject {{path ""}} {
  if { [string length "${path}"] == 0 } {
    if { [catch {
      set path "[sct]"
    } catch_message] } {
      set path ""
    }
  }
  while { [string length ${path}] > 1 } {
    if { [hpropexists ${path} type] } {
      if { [string match -nocase "sct_object" "[hgetpropval ${path} type]"] } {
        return [string map {// /} ${path}]
      }
    }
    set path [pathname ${path}]
  }
  return ""
}
