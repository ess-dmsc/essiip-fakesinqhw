#include <iostream>

#include "generator.hpp"
#include "mcstas_reader.hpp"
#include "nexus_reader.hpp"

using StreamFormat = SINQAmorSim::ESSformat;

using Instrument = SINQAmorSim::Focus;
using Source = SINQAmorSim::NeXusSource<Instrument, StreamFormat>;
using Control = SINQAmorSim::CommandlineControl;

using Serialiser = SINQAmorSim::FlatBufferSerialiser;
using Communication = SINQAmorSim::KafkaTransmitter<Serialiser>;

int main(int argc, char **argv) {

  SINQAmorSim::ConfigurationParser parser;
  int err;
  try {
    err = parser.parse_configuration(argc, argv);
  } catch (const std::exception &Error) {
    std::cout << Error.what() << "\n";
    return -1;
  }
  if (err) {
    std::cout << SINQAmorSim::Err2Str(err) << "\n";
    return -1;
  }
  parser.print();

  auto &config = parser.config;

  if ((config.bytes > 0) && (config.multiplier > 1)) {
    throw std::runtime_error(
        "Conflict between parameters `bytes` and `multiplier`");
  }

  std::vector<StreamFormat::value_type> data;

  try {
    Source stream(config.source, config.multiplier);
    data = stream.get();
  } catch (std::exception &e) {
    std::cout << e.what() << "\n";
    return -1;
  }
  if (config.bytes > 0) {
    data.resize(config.bytes / sizeof(StreamFormat::value_type));
  }

  try {
    Generator<Communication, Control, Serialiser> g(config);
    g.run<StreamFormat::value_type>(data);
  } catch (std::exception e) {
    std::cout << e.what() << "\n";
  }
  return 0;
}
