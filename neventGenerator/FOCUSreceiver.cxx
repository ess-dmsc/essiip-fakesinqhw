#include <iostream>

#include "Configuration.hpp"
#include "generator.hpp"
#include "mcstas_reader.hpp"
#include "nexus_reader.hpp"

using Instrument = SINQAmorSim::Focus;
using Source = SINQAmorSim::NeXusSource<Instrument, SINQAmorSim::PSIformat>;
using Control = SINQAmorSim::NoControl;
using Serialiser = SINQAmorSim::FlatBufferSerialiser;
using Communication = SINQAmorSim::KafkaListener<Serialiser>;

int main(int argc, char **argv) {

  SINQAmorSim::ConfigurationParser parser;
  auto err = parser.parse_configuration(argc, argv);
  if (!err) {
    parser.print();
  } else {
    std::cout << SINQAmorSim::Err2Str(err) << "\n";
    return -1;
  }
  auto &config = parser.config;

  Generator<Communication, Control, Serialiser> g(config);

  std::vector<Source::value_type> stream;
  g.listen(stream);

  return 0;
}
