#ifndef EVENTPRODUCER_H
#define EVENTPRODUCER_H

#include <queue>
#include <random>
#include <string>
#include <iostream>
#include <mutex>


#include "nevent.h"
#include "nexus2event.h"

static const double frequency = 14.; // Hz

struct EventProducer {

  EventProducer();
  unsigned int next() { return (++eID);  }

  void GenerateEvents(char*);

  nevent GetEvent(const int);
  unsigned int GetEventCount();
  const pNEventArray get_ptr() { return nEventData; }
  const int64_t* id() { return nEventData->detectorID; }
  const int32_t* ts() { return nEventData->timeStamp; }
  
  unsigned int* getID() { return &eID; }
  static unsigned int multiplier;
private:
  unsigned int count;
  unsigned int eID;
  pNEventArray nEventData;

  std::once_flag nEventData_flag;

  void GenerateEvents_impl(char*);
};


void keep_pulling(EventProducer*);

#endif  /* EVENTPRODUCER_H */
