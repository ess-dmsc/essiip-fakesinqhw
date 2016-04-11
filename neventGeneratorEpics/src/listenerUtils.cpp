#include "listenerUtils.h"
#include <memory>
#include <thread>             // std::thread, std::this_thread::yield
#include <mutex>              // std::mutex, std::unique_lock
#include <condition_variable> // std::condition_variable


namespace utils {
  
  unsigned int getULong(std::string const & channelName,
                        PVStructure::shared_pointer const & pv,
                        const std::string& fieldname) {
  
    PVField::shared_pointer v = pv->getSubField(fieldname);
    if (v.get() == 0) {
      std::cerr << "no " << fieldname << " field" << std::endl;
      return 1;
    }
    
    return pv->getSubField<PVULong>(fieldname)->get();
  }


  
  std::vector<uint64_t>& getArrayContent(std::string const & channelName,
                                         PVStructure::shared_pointer const & pv,
                                         const std::string& field, std::vector<uint64_t>& container) {
  
    PVField::shared_pointer v = pv->getSubField(field);
    if (v.get() == 0) {
      std::cerr << "no " << field << " field" << std::endl;
      return container;
    }

    PVScalarArray::shared_pointer a = pv->getSubField<PVScalarArray>(field);
    shared_vector<const double> cvalues;
    a->getAs(cvalues);

    if( container.size() != a->getLength() ) {
      container.resize(a->getLength());
    }
      
    std::copy(cvalues.begin(), cvalues.end(), container.begin());
    return container;
  }

}
// void do_something(Channel::shared_pointer const & channel,
//                   shared_ptr<ChannelGetRequesterImpl> const& getRequesterImpl,
//                    PVStructure::shared_pointer const& pvRequest) {

//   int oldPulseID = -1;

//   std::vector<uint64_t> detectorID, timestamp;

//   std::mutex mtx;
//   std::condition_variable cv;
//   std::unique_lock<std::mutex> lck(mtx);

//   int pulseID = -1, pulseCount = 0;
//   uint64_t nCount;

//   int statTime = time(NULL);
  
//   while(true) {

        
//     while( oldPulseID == pulseID ) {

//       pulseID = getULong(channel->getChannelName(),
//                          getRequesterImpl->getPVStructure(),
//                          "eventTag");
//       //        std::cout << oldPulseID << "\t" << pulseID << std::endl;
      
//     }
//     if(pulseID - oldPulseID > 1) {
//       printf("Missed pulse at pulseID %ld\n", pulseID);
//     }
//     oldPulseID = pulseID;
//     nCount = getULong(channel->getChannelName(),
//                       getRequesterImpl->getPVStructure(),"count");
//     getArrayContent(channel->getChannelName(),
//                     getRequesterImpl->getPVStructure(),
//                     "detectorId", detectorID);
//     getArrayContent(channel->getChannelName(),
//                     getRequesterImpl->getPVStructure(),
//                     "nTimeStamp", detectorID);

//     pulseCount++;
    
//     if(time(NULL) >= statTime + 10) {
      
//       printf("Received %f MB/sec , %f n* 10^6/sec, %u pulses\n", pulseCount*2*nCount*sizeof(uint64_t)/(1024.*1024.*10.), pulseCount*nCount/1.e6, pulseCount);
  
//       pulseCount = 0;
//       nCount = 0;
//       statTime = time(NULL);
      
//     }
    
    
    
//   }
// }
// uint64_t& getContent(std::string const & channelName,
//                      PVStructure::shared_pointer const & pv,
//                      const std::string& field,
//                      uint64_t& container) {
    
//   PVField::shared_pointer v = pv->getSubField(field);
//   if (v.get() == 0) {
//     throw std::runtime_error("no " + field + " field");
//   }
    
//   container = pv->getSubField<PVULong>(field)->get();
//   return container;
// }
  
// std::vector<uint64_t>& getContent(std::string const & channelName,
//                                   PVStructure::shared_pointer const & pv,
//                                   const std::string& field,
//                                   std::vector<uint64_t>& container) {
    
//   PVField::shared_pointer v = pv->getSubField(field);
//   if (v.get() == 0) {
//     throw std::runtime_error("no " + field + " field");
//   }
    
//   PVScalarArray::shared_pointer a = pv->getSubField<PVScalarArray>(field);
//   shared_vector<const double> cvalues;
//   a->getAs(cvalues);
    
//   if( container.size() != a->getLength() ) {
//     container.resize(a->getLength());
//   }
    
//   std::copy(cvalues.begin(), cvalues.end(), container.begin());
//   return container;
// }
