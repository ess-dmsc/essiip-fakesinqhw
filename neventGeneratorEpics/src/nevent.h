#ifndef NEVENT_H
#define NEVENT_H

#include <chrono>
#include <thread>

#include <stdint.h>

#include "neventArray.h"


struct nevent {
  nevent() { };
  int64_t detectorID;
  int32_t timeStamp;
  nevent(int64_t detector, int32_t timestamp);
};

#endif  /* NEVENT_H */
