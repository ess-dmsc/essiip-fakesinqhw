#ifndef _URI_H
#define _URI_H

#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <stdexcept>

struct URI {
public:
  static bool parse(const std::string& uri, URI& result);
public:
  std::string protocol, host, path, query, fragment;
  bool query_indicated;
};

#endif //URI_H
