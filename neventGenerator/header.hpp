#pragma once

#include "json.h"

std::pair<int, int> parse_header(const std::string &Header) {
  std::pair<int, int> Result;

  nlohmann::json Document(Header);
  {
    auto x = find<int>("value", Document);
    if (x) {
      Result.first = x.inner();
    }
  }
  {
    auto x = find<int>("ds", Document);
    if (x) {
      Result.second = x.inner();
    }
  }
  return Result;
}
