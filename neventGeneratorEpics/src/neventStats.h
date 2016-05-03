#ifndef _NEVENTSTATS_H
#define _NEVENTSTATS_H

#include "neventStats.h"

#include <ctime>


struct getStats {
  getStats(const uint64_t,uint64_t&, uint64_t&);
getStats(const getStats& other) :
  oldPulseID(other.oldPulseID), pulseID(other.pulseID), nCount(other.nCount) { };
    
  
  void start();
  void stop();
  bool keepPolling();

private:
  uint64_t oldPulseID;
  uint64_t pulseCount;
  uint64_t& pulseID;
  int statTime;
  uint64_t& nCount;
  
  void dump();
  
};

#endif //NEVENTSTATS_H
