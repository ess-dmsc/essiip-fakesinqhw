#ifndef _NEVENTMONITOR_H
#define _NEVENTMONITOR_H

#include <iostream>
#include <stdexcept>

#include <epicsExport.h>
#include <epicsExit.h>
#include <pv/event.h>
#include <pv/caProvider.h>
#include <pv/logger.h>
#include <pv/clientFactory.h>

#include "neventStats.h"
#include "neventRequest.h"

class ChannelGetRequesterImpl;

class MonitorRequesterImpl : public epics::pvData::MonitorRequester {
 private:
  
  std::string m_channelName;
  uint64_t PulseID;
  uint64_t nCount;
  std::shared_ptr<ChannelGetRequesterImpl> getRequesterImpl;
  epics::pvData::PVStructure::shared_pointer pv;
  std::unique_ptr<getStats> stats;

 public:
  
 MonitorRequesterImpl(std::string channelName) :
  m_channelName(channelName),
    getRequesterImpl(new ChannelGetRequesterImpl(m_channelName)),
    pv(epics::pvData::CreateRequest::create()->createRequest("field()")),
    stats(new getStats(0,PulseID,nCount)) {};
  
  virtual std::string getRequesterName();

  virtual void message(std::string const &,epics::pvData::MessageType);
  
  virtual void monitorConnect(const epics::pvData::Status&,
                              epics::pvData::Monitor::shared_pointer const &,
                              epics::pvData::StructureConstPtr const &);
  
  virtual void monitorEvent(epics::pvData::Monitor::shared_pointer const &);

  virtual void unlisten(epics::pvData::Monitor::shared_pointer const &);

};


#endif //NEVENTMONITOR_H
