#include "uri.h"

// TODO invalid characters check, etc.
bool URI::parse(const std::string& uri, URI& result) {

  const std::string prot_end("://");
  std::string::const_iterator prot_i = search(uri.begin(), uri.end(),
                                              prot_end.begin(), prot_end.end());


  if( prot_i == uri.end() || prot_i == uri.begin() ) {
    // throw std::runtime_error("invalid protocol");
    return false;
  }

  result.protocol.reserve(distance(uri.begin(), prot_i));
  transform(uri.begin(), prot_i,
            back_inserter(result.protocol),
            ::tolower); // protocol is icase

  advance(prot_i, prot_end.length());
  if ( prot_i == uri.end() ) {
    return false;
  }
  
  std::string::const_iterator path_i = find(prot_i, uri.end(), '/');
  result.host.assign(prot_i, path_i);
  
  std::string::const_iterator fragment_i = find(path_i, uri.end(), '#');
  if ( fragment_i != uri.end() )
    result.fragment.assign(fragment_i+1, uri.end());
  
  std::string::const_iterator query_i = find(path_i, fragment_i, '?');
  result.path.assign(path_i, query_i);
  result.query_indicated = (query_i != fragment_i);
  if ( result.query_indicated )
    result.query.assign(++query_i, fragment_i);

  return true;
}

bool starts_with(const std::string& s1, const std::string& s2) {
  return s2.size() <= s1.size() && s1.compare(0, s2.size(), s2) == 0;
}
