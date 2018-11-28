#pragma once

#include <map>
#include <string>
#include <vector>

namespace SINQAmorSim {

template <typename T> struct StreamFormat { using value_type = T; };
using PSIformat = StreamFormat<uint64_t>;
using ESSformat = StreamFormat<uint32_t>;

using KafkaOptions = std::vector<std::pair<std::string, std::string>>;

} // namespace SINQAmorSim
