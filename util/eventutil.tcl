# TODO Maybe add ::event::onstart and ::event::onfinish commands to execute some
# code when an object starts or finishes
# eg
# onstart hmm { do something }

namespace eval event {
  variable sobjBusy
  variable END_EVENT

  set sobjBusy 0
  array set END_EVENT {Motor MOTEND HistMem COUNTEND SingleCounter COUNTEND}
  namespace export waitfor
}

proc ::event::waitCB {args} {
  variable sobjBusy
  set sobjBusy 0
}
publish ::event::waitCB user

##
# @brief Wait for a sics object to finish what it's doing.
# waitfor hmm {histmem start}
# waitfor {samx samz} {run samx 3 samz 4}
proc ::event::waitfor {sobj args} {
  variable END_EVENT
  variable sobjBusy

  if [ catch {
    set valid_sobjType [array names END_EVENT]
    set sobjType [SplitReply [sicslist $sobj type] ]
    if {[lsearch $valid_sobjType $sobjType ] == -1} {
      error "ERROR: You can only wait for the following types of objects $valid_sobjType"
    }
    set CBID [SplitReply [scriptcallback connect $sobj $END_EVENT($sobjType) ::event::waitCB ] ]
    set sobjBusy 1
    set oldStatus [lindex [SplitReply [status]] 0]
    eval $args
    while {$sobjBusy == 1} {
      wait 1
    }
    scriptcallback remove $sobj $CBID
    SetStatus $oldStatus
  } message ] {
    scriptcallback remove $sobj $CBID
    SetStatus $oldStatus
    if {$::errorCode=="NONE"} {return "Return: $message"}
    return -code error "Caught $message"
  }
}

namespace import ::event::waitfor

publish waitfor user

namespace eval ::batch::call_cleanup { }
proc ::batch::cleanup {} {}
##
# @brief Calls a user defined cleanup script when a batch file ends or is aborted
# The cleanup script must be called ::batch::call_cleanup
proc ::batch::call_cleanup {} {
  ::batch::cleanup
  proc ::batch::cleanup {} {}
}
publish ::batch::call_cleanup user
scriptcallback connect exe BATCHEND ::batch::call_cleanup

##
# @brief Call a command assigned to an hdb property when the given event occurs.
# This is meant to be called from the read command on an hdb node. It must be
# called everytime the node is polled so that the oneshot callback can be
# removed if the given event fails to occur within the allowed time.
# NOTE: set event parameter to 'fatal_error' to signal an error and remove the callback.
# @param hpath hdb path to a node which regularly calls this procedure.
# @param event an event which may trigger a callback.
# @param args is a list of arguments which will be passed to the callback.
# @return state: -3 = callback cleared/removed by user, -2 = fatal error,
#                -1 = timer expired, 0 = callback triggered, 1 = waiting for event
# remaining before expiry.
proc call_oneshot {hpath event args} {
  if [hpropexists $hpath oneshot_cb] {
    set start_time [hgetpropval $hpath oneshot_start_time]
    set timeout [hgetpropval $hpath oneshot_timeout]
    set useby [expr {$start_time + $timeout}]
    set currtime [hgetpropval $hpath read_time]
    set trigger [hgetpropval $hpath oneshot_trigger]

    if {$event == $trigger} {
      set oneshot_cmd [hgetpropval $hpath oneshot_cb]
      hdelprop $hpath oneshot_cb
      hsetprop $hpath oneshot_state 0
      eval "$oneshot_cmd $hpath $args"
      return 0
    } elseif {$event == "fatal_error"} {
      hdelprop $hpath oneshot_cb
      hsetprop $hpath oneshot_state -2
      return -2
    } elseif {$timeout >= 0} {
      if {$currtime > $useby} {
        hdelprop $hpath oneshot_cb
        hsetprop $hpath oneshot_state -1
        return -1
      }
    } else {
      hsetprop $hpath oneshot_state 1
      return 1
    }
  }
}

##
# @brief Assign a oneshot callback to which is triggered by the given event.
# 
# @param hpath hdb path to a node which regularly calls "call_oneshot"
# @param cb_proc name of the callback procedure
# @param trigger event for callback
# @param timeout the callback is removed when the timeout expires.
# If timeout < 0 then the callback won't timeout but you can force it to be
# removed by calling set_oneshot again with timeout = 0.
# If timeout = 0 the callback will only be called if the trigger event occurs
# the first time the node is polled.  If there is no trigger event then the
# callback is simply removed.
# TODO Maybe. Allow registering a callback for each event on hpath.
proc set_oneshot {hpath cb_proc event {cb_timeout 60}} {
  set catch_status [ catch {
    if {$cb_timeout == "clear"} {
      hdelprop $hpath oneshot_cb
      hsetprop $hpath oneshot_state -3
      return
    }
    if {![string is integer $cb_timeout]} {
      error "Valid values for the timeout are 'clear' or an integer"
    }
    hsetprop $hpath oneshot_cb $cb_proc
    hsetprop $hpath oneshot_timeout $cb_timeout
    hsetprop $hpath oneshot_start_time [hgetpropval $hpath read_time]
    hsetprop $hpath oneshot_trigger $event
    hsetprop $hpath oneshot_state 1
  } catch_message ]
  handle_exception ${catch_status} ${catch_message}
}
publish set_oneshot user
