#ifndef _NEVENTREQUEST_H
#define _NEVENTREQUEST_H

#include <iostream>
#include <stdexcept>

#include <epicsExport.h>
#include <epicsExit.h>
#include <pv/event.h>
#include <pv/caProvider.h>
#include <pv/logger.h>
#include <pv/clientFactory.h>

#include "uri.h"

struct RequesterImpl : public epics::pvData::Requester {
  RequesterImpl(std::string const&);
  std::string getRequesterName();
  void message(std::string const&, epics::pvData::MessageType);
private:
  std::string requesterName;
};


class ChannelRequesterImpl :
public epics::pvAccess::ChannelRequester {
 private:
  epics::pvData::Event m_event;
  bool printOnlyErrors;
  bool showDisconnectMsg;

 public:
  
  ChannelRequesterImpl(bool _printOnlyErrors = false);
  
  virtual std::string getRequesterName();
  virtual void message(std::string const &, epics::pvData::MessageType);
  
  virtual void channelCreated(const epics::pvData::Status& status,
                              epics::pvAccess::Channel::shared_pointer const &);
  virtual void channelStateChange(epics::pvAccess::Channel::shared_pointer const &,
                                  epics::pvAccess::Channel::ConnectionState);
    
  bool waitUntilConnected(double timeOut);
  void showDisconnectMessage(bool show = true);
};






class ChannelGetRequesterImpl : public epics::pvAccess::ChannelGetRequester
{
private:
  epics::pvData::PVStructure::shared_pointer m_pvStructure;
  epics::pvData::BitSet::shared_pointer m_bitSet;
  epics::pvData::Mutex m_pointerMutex;
  epics::pvData::Event m_event;
  std::string m_channelName;

  bool m_done;

public:
    
  ChannelGetRequesterImpl(std::string);
    
  virtual std::string getRequesterName();

  virtual void message(std::string const &, epics::pvData::MessageType);

  virtual void channelGetConnect(const epics::pvData::Status&, epics::pvAccess::ChannelGet::shared_pointer const&,
                                 epics::pvData::Structure::const_shared_pointer const& /*structure*/);
  
  virtual void getDone(const epics::pvData::Status& , 
                       epics::pvAccess::ChannelGet::shared_pointer const& /*channelGet*/,
                       epics::pvData::PVStructure::shared_pointer const &, 
                       epics::pvData::BitSet::shared_pointer const&);
  
  epics::pvData::PVStructure::shared_pointer getPVStructure();

  bool waitUntilGet(double);
  
};


class GetFieldRequesterImpl : public epics::pvAccess::GetFieldRequester
{
 private:
  epics::pvAccess::Channel::shared_pointer m_channel;
  epics::pvData::FieldConstPtr m_field;
  epics::pvData::Event m_event;
  epics::pvData::Mutex m_pointerMutex;
  
 public:
  
  GetFieldRequesterImpl(epics::pvAccess::Channel::shared_pointer);
  
  virtual std::string getRequesterName();
  virtual void message(std::string const &, epics::pvData::MessageType);
  
  virtual void getDone(const epics::pvData::Status&, epics::pvData::FieldConstPtr const &);
  
  epics::pvData::FieldConstPtr getField();
  
  bool waitUntilFieldGet(double);

};




#endif //NEVENTREQUEST_H
