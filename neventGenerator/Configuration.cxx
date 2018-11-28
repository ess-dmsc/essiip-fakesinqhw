#include "Configuration.hpp"

#include <fstream>
#include <getopt.h>
#include <iostream>
#include <regex>
#include <sstream>

std::string get_protocol(const std::string &s, const std::string &deft = "") {
  std::smatch m;
  if (std::regex_search(s, m, std::regex("^[A-Za-z]+"))) {
    return std::string(m[0]);
  }
  return std::move(deft);
}

std::string get_broker(const std::string &s, const std::string &deft = "") {
  std::smatch m;
  if (std::regex_search(s, m, std::regex("//.*/"))) {
    auto result = std::string(m[0]).substr(2);
    result.pop_back();
    return result;
  }
  return std::move(deft);
}

std::string get_topic(const std::string &s, const std::string &deft = "") {
  std::smatch m;
  if (std::regex_search(s, m, std::regex("/[A-Za-z0-9-_:.]*$")))
    return std::move(std::string(m[0]).erase(0, 1));
  return std::move(deft);
}

bool broker_topic_is_valid(const std::string &broker,
                           const std::string &topic) {
  if (topic.empty() || broker.empty() || broker.front() == ':' ||
      broker.back() == ':') {
    return false;
  }
  if (broker.find(":,") != std::string::npos ||
      broker.find(",:") != std::string::npos) {
    return false;
  }

  return true;
}

SINQAmorSim::KafkaConfiguration
SINQAmorSim::ConfigurationParser::parse_string_uri(const std::string &uri,
                                                   const bool use_defaults) {
  KafkaConfiguration configuration;
  if (use_defaults) {
    configuration.broker = get_broker(uri, "//localhost:9092/");
    configuration.topic = get_topic(uri, "empty-topic");
  } else {
    configuration.broker = get_broker(uri);
    configuration.topic = get_topic(uri);
    if (!broker_topic_is_valid(configuration.broker, configuration.topic)) {
      throw ConfigurationParsingException();
    }
  }
  return configuration;
}

void SINQAmorSim::ConfigurationParser::parse_configuration_file(
    const std::string &input) {
  std::ifstream ifs(input, std::ifstream::in);
  if (ifs.fail()) {
    throw std::runtime_error("Configuration file doesn't exist");
  }
  std::stringstream buffer;
  buffer << ifs.rdbuf();
  nlohmann::json Configuration = nlohmann::json::parse(buffer.str());

  parse_configuration_file_impl(Configuration);
}
void SINQAmorSim::ConfigurationParser::parse_configuration_file_impl(
    nlohmann::json &Configuration) {
  {
    auto x = find<std::string>("producer_uri", Configuration);
    if (x) {
      config.producer = parse_string_uri(x.inner());
    }
  }
  {
    auto x = find<std::string>("source", Configuration);
    if (x) {
      config.source = x.inner();
    }
  }
  {
    auto x = find<std::string>("source_name", Configuration);
    if (x) {
      config.source_name = x.inner();
    }
  }
  {
    auto x = find<int>("rate", Configuration);
    if (x) {
      config.rate = x.inner();
    }
  }
  {
    auto x = find<int>("bytes", Configuration);
    if (x) {
      config.bytes = x.inner();
    }
  }
  {
    auto x = find<int>("multiplier", Configuration);
    if (x) {
      config.multiplier = x.inner();
    }
  }
  {
    auto x = find<int>("num_threads", Configuration);
    if (x) {
      config.num_threads = x.inner();
    }
  }
  {
    auto x = find<std::string>("timestamp_generator", Configuration);
    if (x) {
      config.timestamp_generator = x.inner();
    }
  }
  {
    auto x = find<int>("report_time", Configuration);
    if (x) {
      config.report_time = x.inner();
    }
  }
  auto x = find<nlohmann::json>("kafka", Configuration);
  if (x) {
    nlohmann::json kafka = x.inner();
    get_kafka_options(kafka);
  }
}

void SINQAmorSim::ConfigurationParser::get_kafka_options(
    nlohmann::json &kafka) {
  for (nlohmann::json::iterator it = kafka.begin(); it != kafka.end(); ++it) {
    if (it.value().is_number()) {
      int value = it.value();
      config.options.push_back({it.key(), std::to_string(value)});
      continue;
    }
    if (it.value().is_string()) {
      std::string value = it.value();
      config.options.push_back({it.key(), value});
      continue;
    }
  }
}

int SINQAmorSim::ConfigurationParser::parse_configuration(int argc,
                                                          char **argv) {
  int error = ConfigurationError::error_no_configuration_error;
  std::map<std::string, std::string> CommandLineOptions;
  try {
    if (argc > 1) {
      CommandLineOptions = parse_command_line(argc, argv);
    }
    if (CommandLineOptions.find("config-file") == CommandLineOptions.end()) {
      parse_configuration_file("config.json");
    } else {
      parse_configuration_file(CommandLineOptions["config-file"]);
    }
  } catch (const std::exception &e) {
    throw std::runtime_error(e.what());
  }

  if (error == ConfigurationError::error_no_configuration_error) {
    override_configuration_with(CommandLineOptions);
    validate();
  }
  return error;
}

void usage(const std::string &executable);

std::map<std::string, std::string>
SINQAmorSim::ConfigurationParser::parse_command_line(int argc, char **argv) {
  std::map<std::string, std::string> CommandLineOptions;

  static struct option long_options[] = {
      {"help", no_argument, nullptr, 'h'},
      {"config-file", required_argument, nullptr, 0},
      {"producer-uri", required_argument, nullptr, 0},
      {"status-uri", required_argument, nullptr, 0},
      {"use-signal-handler", required_argument, nullptr, 0},
      {"source", required_argument, nullptr, 0},
      {"source-name", required_argument, nullptr, 0},
      {"multiplier", required_argument, nullptr, 0},
      {"num-threads", required_argument, nullptr, 0},
      {"bytes", required_argument, nullptr, 0},
      {"rate", required_argument, nullptr, 0},
      {"timestamp-generator", required_argument, nullptr, 0},
      {nullptr, 0, nullptr, 0},
  };
  std::string cmd;
  int option_index = 0;
  bool getopt_error = false;
  while (true) {
    int c = getopt_long(argc, argv, "h", long_options, &option_index);
    if (c == -1)
      break;
    if (c == '?') {
      getopt_error = true;
    }
    switch (c) {
    case 'h':
      usage(std::string(argv[0]));
      break;
    case 0:
      auto lname = long_options[option_index].name;
      CommandLineOptions[lname] = optarg;
      break;
    }
  }

  if (getopt_error) {
    throw std::runtime_error("Error parsing command line options");
  }

  return CommandLineOptions;
}

const std::string findMap(std::string Key,
                          std::map<std::string, std::string> &Map) {
  auto It = Map.find(Key);
  if (It != Map.end()) {
    return Map[Key];
  }
  return "";
}

int to_int(const std::string &Text) {
  std::stringstream Stream(Text);
  int Value;
  Stream >> Value;
  return Value;
}

void SINQAmorSim::ConfigurationParser::override_configuration_with(
    std::map<std::string, std::string> &CommandLineOptions) {
  std::string Value = findMap("producer-uri", CommandLineOptions);
  if (!Value.empty()) {
    config.producer = parse_string_uri(Value, true);
  }
  Value = findMap("source", CommandLineOptions);
  if (!Value.empty()) {
    config.source = Value;
  }
  Value = findMap("source-name", CommandLineOptions);
  if (!Value.empty()) {
    config.source_name = Value;
  }
  Value = findMap("multiplier", CommandLineOptions);
  if (!Value.empty()) {
    config.multiplier = to_int(Value);
  }
  Value = findMap("num-threads", CommandLineOptions);
  if (!Value.empty()) {
    config.num_threads = to_int(Value);
  }
  Value = findMap("rate", CommandLineOptions);
  if (!Value.empty()) {
    config.rate = to_int(Value);
  }
  Value = findMap("bytes", CommandLineOptions);
  if (!Value.empty()) {
    config.bytes = to_int(Value);
  }
  Value = findMap("timestamp-generator", CommandLineOptions);
  if (!Value.empty()) {
    config.timestamp_generator = Value;
  }
}

void SINQAmorSim::ConfigurationParser::validate() {
  if (config.producer.broker.empty()) {
    throw std::runtime_error("Error: empty broker");
  }
  if (config.producer.topic.empty()) {
    throw std::runtime_error("Error: empty producer");
  }
  if (config.source_name.empty()) {
    throw std::runtime_error("Error: empty source name");
  }
  if (config.source.empty()) {
    throw std::runtime_error("Error: empty source");
  }
  if (config.multiplier <= 0) {
    throw std::runtime_error("Error: multiplier <= 0");
  }
  if (config.num_threads <= 0) {
    throw std::runtime_error("Error: num threads <= 0");
  }
  if (config.rate <= 0) {
    throw std::runtime_error("Error: rate <= 0");
  }
  if (config.bytes <= 0) {
    throw std::runtime_error("Error: bytes <= 0");
  }
}

void SINQAmorSim::ConfigurationParser::print() {
  std::cout << "producer:\n"
            << "\tbroker: " << config.producer.broker << "\n"
            << "\ttopic: " << config.producer.topic << "\n";
  std::cout << "source: " << config.source << "\n"
            << "source_name: " << config.source_name << "\n"
            << "multiplier: " << config.multiplier << "\n"
            << "num-threads: " << config.num_threads << "\n"
            << "bytes: " << config.bytes << "\n"
            << "rate: " << config.rate << "\n"
            << "timestamp_generator: " << config.timestamp_generator << "\n";
  std::cout << "kafka:\n";
  for (auto &o : config.options) {
    std::cout << "\t" << o.first << ": " << o.second << "\n";
  }
  std::cout << "\n";
}

void usage(const std::string &exe) {
  std::cout << "Usage: " << exe << " [OPTIONS]\n"
            << "\t--config-file:\n"
            << "\t--producer-uri:\n"
            << "\t--source:\n"
            << "\t--source-name:\n"
            << "\t--multiplier:\n"
            << "\t--threads:\n"
            << "\t--rate:\n"
            << "\t--bytes:\n"
            << "\t--timestamp-generator\n"
            << "\n";
  exit(0);
}
