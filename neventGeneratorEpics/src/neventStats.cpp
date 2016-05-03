#include "neventStats.h"
#include <stdio.h>

getStats::getStats(const uint64_t old, uint64_t& pid, uint64_t& nCount_) : oldPulseID(old), pulseCount(0),
                                                                           pulseID(pid), nCount(nCount_) { }

void getStats::start() { statTime = time(NULL); }

void getStats::stop() {

  if(pulseID - oldPulseID > 1) {
    printf("Missed pulse at pulseID %d\n", pulseID);
  }
  oldPulseID = pulseID;
  pulseCount++;
  
  if(time(NULL) >= statTime + 10) {      
    dump();
  }
}

bool getStats::keepPolling() { return (oldPulseID == pulseID); }
  
void getStats::dump() {
  printf("Received %f MB/sec , %f n* 10^6/sec, %llu pulses\n", pulseCount*2*nCount*sizeof(uint64_t)/(1024.*1024.*10.), pulseCount*nCount/1.e6, pulseCount);
  
  pulseCount = 0;
  nCount = 0;
  statTime = time(NULL);
}
