# neventGeneratorPy

Python implementation of neventGenerator. Works with both non triggered generator/reader:

(server side)   `zmqGenerator.py <NeXus file> <port>`
(receiver side) `zmqReader.py tcp://<ip>:<port>`

and triggered:

(server side)   `el737generator.py <port (default=62001)>`
(receiver side) `el737counter_recv.py <port  (default=62000)>`
(trigger)       `telnet <ip> <port> -> run/pause`

(or any combination)

`el737generator.py` requires to be initiliased and executed with the followings:

`init <NeXus file> <port> <multiplier>`
`run`

`el737counter_recv.py` requires to be initiliased and executed with the followings:

`init tcp://<address>:<port>`
`run`

