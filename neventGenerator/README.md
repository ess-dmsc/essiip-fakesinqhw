# kafkaGenerator

## Features:

* Convert a NeXus data file in an event stream
* Serialise the event stream using FlatBuffers
* Send the serialised event stream via Kafka
* Data size can be configured to be a multiple of the original data
* Transmission rate can be adjusted in real time

## Installation

### Requirements:

* jsonformoderncpp
* RdKafka
* Flatbuffers
* HDF5
* StreamingDataTypes
* Googletest [optional]
* ZeroMQ [optional]

### Conan repositories

he following remote repositories are required to be configured:

- https://api.bintray.com/conan/ess-dmsc/conan
- https://api.bintray.com/conan/conan-community/conan

You can add them by running

```
conan remote add <local-name> <remote-url>
```

where `<local-name>` must be substituted by a locally unique name. Configured
remotes can be listed with `conan remote list`.

### Build

```shell
cmake [-DCMAKE_CXX_COMPILER=<> -DCMAKE_INCLUDE_PATH=<> \
-DCMAKE_LIBRARY_PATH=<> -DCMAKE_PROGRAM_PATH=<path to flatc> \
-DGOOGLETEST_REPOSITORY_DIR=<path to googletest repo>] <path to source>

make
```

## Usage

```shell
./AMORgenerator -h
```

For example:

```shell
./AMORgenerator --config-file config.json --producer-uri //localhost:9092/AMOR.area.detector
```

Command line options are:


| Option | Description | 
| ---         |     ---|
| `config-file`  | Name of the configuration file to use |
|  `producer-uri`    | Name/address of the producer, port and topic in the form`//<broker>:<port>/<topic>` |
| `source`   | NeXus file to convert into an event stream | 
| `source-name`   | String tagging the data source in the FlatBuffer buffer | 
| `multiplier`  | number of repetition of the original data in the event stream  | 
| `bytes`  | number of bytes in the event stream  | 
| `rate`   | Number of packets/second to transmit  | 
| `timestamp-generator`   | Update policy for the timestamp of the events  | 

Warning The parameters `multiplier` and `bytes` conflicts: if the
latter is specified the message size will be changed according to the specified
value.

Notes
* Command line options override the corresponding configuration file option
* `producer-uri` can consist a list of brokers comma separated:
```
//broker1:port1, broker2:port2, .../topic
```
* `timestamp-generator` must be one among
``"const_timestamp"``,``"random_timestamp"``, ``"none"``

### Configuration File

The configuration file must be in JSON format. Here an example:

```js
{
    "producer_uri" : "//129.129.188.59:9092/AMOR.area.detector",
    "source" : "files/amor2015n001774.hdf",
    "multiplier" : 1,
	[OPTIONAL]"bytes" : 1000,
    "rate" : 10,
    "source_name": "AMOR.event.stream",
    "timestamp_generator" : "const_timestamp",
    "report_time" : 1,
	"kafka_options" : {
		"any-valid-rdkafka-option" : "string-value",
		"further-valid-rdkafka-option" : "string-value"
	}
}
```
* ``report_time`` defines the time in seconds between log messages


### Run-time commands

The following commands change the runtime behaviour:
* ``run/pause/stop``: restore/pause/interrupt the simulation
* ``rate``: change the transmission rate

### FlatBuffer format

The messages are serialised according the schema "ev42":

```shell
{
    source_name : string;    # producer type, for example detector type
    message_id : ulong;      # sequential number of the message
    pulse_time : ulong;      # time of source pulse, nanoseconds since Unix epoch (1 Jan 1970)
    time_of_flight : [uint]; # nanoseconds measured from pulse time
    detector_id : [uint];    # detector id
    facility_specific_data : FacilityData;  # not used
}
```

## Running in the counterbox

The file ``el737counter.py`` is a simulation of the el737 counterbox. To run the
generator as part of the el737 counterbox protocol:
```shell
python el737counter.py [port (default is 62000)]
```
In a different shell
```shell
telnet <host> <port>
rmt 1
echo 2 [optional parameters to the generator]
```
where <host> and <port> must match those there the counterbox is running.

Other useful commands to control the execution:

| Option | Description | 
| ---         |     ---|
| **mp <number>** | start the counting/event generation |
| **st** | stop the event generation (kill the process) |
| **ps** | pause the generation |
| **co** | un-pause the generation |

## Issues

A failure is reported with Conan trying to buld hdf5. This is connected with https://bugzilla.redhat.com/show_bug.cgi?format=multiple&id=1170339 . A workaround required to change the ``~/.conan/data/hdf5/1.10.1/ess-dmsc/testing/export/conanfile.py`` with the following

```python
        tools.download(
            "https://www.hdfgroup.org/package/gzip/?wpdmdl=4301",
            "hdf5-1.10.1.tar.gz",
            verify=False
        )
```
