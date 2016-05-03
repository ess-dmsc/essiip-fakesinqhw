#include "neventRequest.h"

using namespace epics::pvData;
using namespace epics::pvAccess;

using namespace std;

struct dump_stack_only_on_debug {
    const epics::pvData::Status &status;
    dump_stack_only_on_debug(const epics::pvData::Status &s) : status(s) {}
};

std::ostream& operator<<(std::ostream& o, const dump_stack_only_on_debug& d) {
  const Status &s = d.status;
  o << '[' << Status::StatusTypeName[s.getType()] << "] ";
  string msg = s.getMessage();
  if (!msg.empty()) {
    o << msg;
  }
  else {
    o << "(no error message)";
  }
  return o;
}


/***********************************************/

RequesterImpl::RequesterImpl(std::string const & requesterName) : requesterName(requesterName) { }

std::string RequesterImpl::getRequesterName() { return requesterName; }

void RequesterImpl::message(std::string const & message, MessageType message_t) {
  std::cerr << "[" << getRequesterName() << "] message(" << message << ", " << getMessageTypeName(message_t) << ")" << std::endl;
}




/**********************************************/




ChannelRequesterImpl::ChannelRequesterImpl(bool _printOnlyErrors) : printOnlyErrors(_printOnlyErrors),
                                                                    showDisconnectMsg(false) { }

string ChannelRequesterImpl::getRequesterName() { return "ChannelRequesterImpl"; }

void ChannelRequesterImpl::message(std::string const & message, epics::pvData::MessageType messageType) {
  if (!printOnlyErrors || messageType > warningMessage)
    std::cerr << "[" << getRequesterName()
              << "] message(" << message
              << ", " << getMessageTypeName(messageType) << ")"
              << std::endl;
}

void ChannelRequesterImpl::channelCreated(const epics::pvData::Status& status,
                                          Channel::shared_pointer const & channel) {
  if (status.isSuccess()) {
    // show warning
    if (!status.isOK()) {
      std::cerr << "[" << channel->getChannelName() << "] channel create: "
                << dump_stack_only_on_debug(status) << std::endl;
    }
  }
  else {
    throw std::runtime_error("[" +
                             channel->getChannelName() +
                             "] failed to create a channel: ");
  }
}

void ChannelRequesterImpl::channelStateChange(Channel::shared_pointer const & channel,
                                              Channel::ConnectionState connectionState) {
  if (connectionState == Channel::CONNECTED) {
    m_event.signal();
  }
  else if (showDisconnectMsg && connectionState == Channel::DISCONNECTED) {
    std::cerr << std::setw(30) << std::left << channel->getChannelName()
              << ' ' << "*** disconnected" << std::endl;
  }
  else
    if (connectionState != Channel::DESTROYED) {
      std::cerr << "[" << channel->getChannelName() << "] channel state change: "  << Channel::ConnectionStateNames[connectionState] << std::endl;
    }
}

bool ChannelRequesterImpl::waitUntilConnected(double timeOut) {
  if(!m_event.wait(timeOut)) {
    throw std::runtime_error("'ChannelRequesterImpl' unable to connect: timeout");
  }
  return true;
}

void ChannelRequesterImpl::showDisconnectMessage(bool show) {
  showDisconnectMsg = show;
}










/***************************************************/


ChannelGetRequesterImpl::ChannelGetRequesterImpl(std::string channelName) : m_channelName(channelName), m_done(false) {}
    
std::string ChannelGetRequesterImpl::getRequesterName() { return "ChannelGetRequesterImpl"; }

void ChannelGetRequesterImpl::message(std::string const & message, MessageType messageType) {
  std::cerr << "["          << getRequesterName()
            << "] message(" << message
            << ", "         << getMessageTypeName(messageType)
            << ")"          << std::endl;
}

void ChannelGetRequesterImpl::channelGetConnect(const epics::pvData::Status& status,
                                                        ChannelGet::shared_pointer const & channelGet,
                                                        epics::pvData::Structure::const_shared_pointer const & /*structure*/) {
  if (status.isSuccess()) {
    // show warning
    if (!status.isOK()) {
      std::cerr << "[" << m_channelName << "] channel get create: " << status << std::endl;
    }
    
    channelGet->lastRequest();
    channelGet->get();
  }
  else {
    std::cerr << "[" << m_channelName << "] failed to create channel get: " << status << std::endl;
    m_event.signal();
  }
}

void ChannelGetRequesterImpl::getDone(const epics::pvData::Status& status, 
                                              ChannelGet::shared_pointer const & /*channelGet*/,
                                              epics::pvData::PVStructure::shared_pointer const & pvStructure, 
                                              epics::pvData::BitSet::shared_pointer const & bitSet) {
  if (status.isSuccess()) {
    // show warning
    if (!status.isOK()) {
      std::cerr << "[" << m_channelName << "] channel get: " << status << std::endl;
    }
    
    // access smart pointers
    {
      Lock lock(m_pointerMutex);
      
      m_pvStructure = pvStructure;
      m_bitSet = bitSet;
      
      m_done = true;
      
    }
  }
  else {
    std::cerr << "[" << m_channelName << "] failed to get: " << status << std::endl;
  }
  
  m_event.signal();
}

PVStructure::shared_pointer ChannelGetRequesterImpl::getPVStructure() {
  Lock lock(m_pointerMutex);
  return m_pvStructure;
}

bool ChannelGetRequesterImpl::waitUntilGet(double timeOut) {
  bool signaled = m_event.wait(timeOut);
  if (!signaled) {
    std::cerr << "[" << m_channelName << "] get timeout" << std::endl;
    return false;
  }
  
  Lock lock(m_pointerMutex);
  return m_done;
}




/***************************************************/



GetFieldRequesterImpl::GetFieldRequesterImpl(epics::pvAccess::Channel::shared_pointer channel) :
  m_channel(channel) { }

string GetFieldRequesterImpl::getRequesterName() { return "GetFieldRequesterImpl"; }

void GetFieldRequesterImpl::message(std::string const & message, MessageType messageType) {
  std::cerr << "[" << getRequesterName() << "] message(" << message << ", " << getMessageTypeName(messageType) << ")" << std::endl;
}

void GetFieldRequesterImpl::getDone(const epics::pvData::Status& status, epics::pvData::FieldConstPtr const & field) {
  if (status.isSuccess()) {
    // show warning
    if (!status.isOK()) {
      std::cerr << "[" << m_channel->getChannelName()
                << "] getField: " << dump_stack_only_on_debug(status)
                << std::endl;
    }
    
    // assign smart pointers
    {
      Lock lock(m_pointerMutex);
      m_field = field;
    }
  }
  else {
    // do not complain about missing field
    std::cerr << "[" << m_channel->getChannelName()
              << "] failed to get channel introspection data: "
              << dump_stack_only_on_debug(status) << std::endl;
  }
  
  m_event.signal();
}

bool GetFieldRequesterImpl::waitUntilFieldGet(double timeOut) {
  //  return m_event.wait(timeOut);
  if(!m_event.wait(timeOut)) {
    throw std::runtime_error("'GetFieldRequesterImpl' unable to connect: timeout");
  }
  return true;
}

epics::pvData::FieldConstPtr GetFieldRequesterImpl::getField() {
  Lock lock(m_pointerMutex);
  return m_field;
}
