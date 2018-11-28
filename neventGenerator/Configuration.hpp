#pragma once

#include "Errors.hpp"
#include "json.h"
#include "utils.hpp"
#include <map>

namespace SINQAmorSim {

class KafkaConfiguration {
public:
  std::string broker{""};
  std::string topic{""};
};

class Configuration {

public:
  KafkaConfiguration producer;
  std::string configuration_file{""};
  std::string source{""};
  std::string source_name{"AMOR.event.stream"};
  std::string timestamp_generator{"none"};
  int multiplier{0};
  int bytes{0};
  int rate{0};
  int report_time{10};
  int num_threads{0};
  bool valid{true};
  KafkaOptions options;
};

class ConfigurationParser {
  // Parse the content of the configuration file and the command line options
public:
  int parse_configuration(int argc, char **argv);

  void print();

  Configuration config;

private:
  std::map<std::string, std::string> parse_command_line(int argc, char **argv);

  void parse_configuration_file(const std::string &input);

  void parse_configuration_file_impl(nlohmann::json &);

  KafkaConfiguration parse_string_uri(const std::string &uri,
                                      const bool use_defaults = false);
  void get_kafka_options(nlohmann::json &);

  void override_configuration_with(std::map<std::string, std::string> &);

  void validate();
};
} // namespace SINQAmorSim
