# Author: Ferdi Franceschini (ffr@ansto.gov.au)

# globals controller, channel

# Open a communications channel to a dmc2280 motor controller
# contName: controller name, eg dmc2280_controller1
# The host and port in the SICS configuration file will be used by default
proc dmc_connect {contName {host ""} {port ""}} {
  upvar #0 $contName controller;
  global channel;

  if {$host == ""} {set host $controller(host)}
  if {$port == ""} {set port $controller(port)}

  if [catch {socket $host $port} con] {
    error "Failed to connect to $contName IP($host) port($port)\n\
    $con\n
    Is the motor controller switched on? Are the network cables plugged in?\n
    NOTE: You can only have a maximum of eight connections per motor controller.\n
    If there are other programs (eg SICS) connected to the controller then all\n
    of the available connections may have been used up."
  }
  set controller(socket) $con
  set channel($contName) $con
  set channel($con) $contName
  set channel($controller(host)) $con
  fconfigure $con -buffering line -translation crlf -blocking true
}

proc dmc_close {dmc_socket} {
  close $dmc_socket;
}

# Send a dmc2280 command
proc dmc_sendCmd {dmc_socket cmd} {
  global channel
  set contName $channel($dmc_socket);
  upvar #0 $contName controller
  puts $dmc_socket $cmd
  set status [read $dmc_socket 1]
  if {$status == "?"} {
    puts $dmc_socket "TC 1"
    set status [read $dmc_socket 1]
    if {$status == "?"} {
      error "error: dmc command $cmd failed"
    } else {
      set dmcError [dmc_receive $dmc_socket]
      set errInfo "DM2280 controller $contName
      host $controller(host)
      port $controller(port)"
      error "DMC2280 ERROR $dmcError: when running command $cmd\n$errInfo"
    }
  } else {
    return $status
  }
}

# Receive a dmc2280 command
proc dmc_receive {dmc_socket} {
  global channel
  set contName $channel($dmc_socket);
  upvar #0 $contName controller
  gets $dmc_socket line
  # Consume the following colon
  read $dmc_socket 1
  return $line
}

