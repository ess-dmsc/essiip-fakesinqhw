#include "neventMonitor.h"
#include "listenerUtils.h"
#include <typeinfo>

std::string MonitorRequesterImpl::getRequesterName() { return "MonitorRequesterImpl"; };

void MonitorRequesterImpl::message(std::string const & message,epics::pvData::MessageType messageType) {
  std::cerr << "[" << getRequesterName()
            << "] message(" << message
            << ", " << getMessageTypeName(messageType)
            << ")"
            << std::endl;
}

void MonitorRequesterImpl::monitorConnect(const epics::pvData::Status& status,
                                          epics::pvData::Monitor::shared_pointer const & monitor,
                                          epics::pvData::StructureConstPtr const & /*structure*/) {

  //  std::cout << "MonitorRequesterImpl::monitorConnect -> " << m_channelName << std::endl;
  if (status.isSuccess()) {

    
    epics::pvData::Status startStatus = monitor->start();
    stats->start();

    // show error
    // TODO and exit
    if (!startStatus.isSuccess()) {
      std::cerr << "[" << m_channelName << "] channel monitor start: " << startStatus << std::endl;
    }
    
  }
  else {
    std::cerr << "monitorConnect(" << status << ")" << std::endl;
  }
}

void MonitorRequesterImpl::monitorEvent(epics::pvData::Monitor::shared_pointer const & monitor) {

  //  std::cout << "MonitorRequesterImpl::monitorEvent" << std::endl;

  epics::pvData::MonitorElement::shared_pointer element;

    
  while ( (element = monitor->poll()) ) {
    
    //    uint64_t tmp = (*(element->pvStructurePtr->getSubField<PVULong>("eventTag"))).get();
    //    PulseID = (*(element->pvStructurePtr->getSubField<PVInt>("eventTag"))).get();

    //    std::cout << tmp << std::endl;
    epics::pvData::PVField::shared_pointer value = element->pvStructurePtr->getSubField("eventTag");
    if (value.get() == 0) {
      std::cerr << "no 'eventTag' field" << std::endl;
      std::cout << m_channelName << std::endl;
      // std::cout << *(element->pvStructurePtr.get()) << std::endl << std::endl;
      // pvutil_ostream myos(std::cout.rdbuf());
      // myos << *(element->pvStructurePtr.get()) << std::endl << std::endl;
    }

    PulseID = value->getParent()->getSubField<PVULong>("eventTag")->get();
    
    std::vector<uint64_t> detectorID;
    std::vector<uint64_t> timestamp;

    utils::getContent(m_channelName ,
                      element->pvStructurePtr,
                      "count",
                      nCount);

    utils::getContent(m_channelName ,
                      element->pvStructurePtr,
                      "detectorId", detectorID);
    
    // nCount = utils::getULong(m_channelName ,
    //                          element->pvStructurePtr,
    //                          "count");

    // utils::getArrayContent(m_channelName ,//channel->getChannelName(),
    //                        element->pvStructurePtr,//                           getRequesterImpl->getPVStructure(),
    //                        "detectorId", detectorID);
    
    // utils::getArrayContent(m_channelName , //channel->getChannelName(),
    //                        element->pvStructurePtr,//                           getRequesterImpl->getPVStructure(),
    //                        "nTimeStamp", timestamp);

    stats->stop();
    
    monitor->release(element);
  }
  
}

// void MonitorRequesterImpl::monitorEvent(epics::pvData::Monitor::shared_pointer const & monitor, epics::pvData::PVStructure::shared_pointer const & pv_) {
//   pv(pv_);
//   monitorEvent(monitor);
// }


void MonitorRequesterImpl::unlisten(epics::pvData::Monitor::shared_pointer const & /*monitor*/) {
  std::cerr << "unlisten" << std::endl;
}










