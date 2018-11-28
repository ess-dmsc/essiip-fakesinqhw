#include "Errors.hpp"

#include <map>

static std::map<int, const std::string> error_map{
    // std::pair<int,std::string>
    {0, "no_error"},
    {-10, "error_input_file"},
    {-11, "error_parsing_json"},
    {-12, "error_parsing_command_line"},
    {-13, "error_configuration_invalid"}};

const std::string SINQAmorSim::Err2Str(const int &id) {
  auto error = error_map.find(id);
  if (error != error_map.end()) {
    return error->second;
  }
  return std::string("Unknown error");
}
