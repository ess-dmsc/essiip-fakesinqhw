#include <random>
#include <algorithm>
#include <type_traits>


#include "event_producer.h"

unsigned int EventProducer::multiplier = 1;

EventProducer::EventProducer() : eID(0) { }

void EventProducer::GenerateEvents(char* filename) {
  std::call_once(nEventData_flag,[&] {GenerateEvents_impl(filename);});
}

void EventProducer::GenerateEvents_impl(char* filename) {
  nEventData = loadNeXus2Events(filename);
  if(multiplier > 1) {
    nEventData = multiplyNEventArray(nEventData, multiplier);
  }
  count = nEventData->count;
}

nevent EventProducer::GetEvent(const int eventId) {
  struct nevent ev;
  ev.detectorID = nEventData->detectorID[eventId];
  ev.timeStamp = nEventData->timeStamp[eventId];
  return ev;
}

unsigned int EventProducer::GetEventCount() { return count; }


void keep_pulling(EventProducer* prod) {
  while(true) {
    std::this_thread::sleep_for(std::chrono::milliseconds((int)round(1000./frequency)));    
    prod->next();
  }
}
