#include <iostream>
#include <epicsThread.h>

#include "neventRequest.h"
#include "neventMonitor.h"
#include "listenerUtils.h"

using namespace std;
using namespace epics::pvData;
using namespace epics::pvAccess;

const bool default_monitor = false;

static const double default_timeout = 3.0;

#define DEFAULT_REQUEST "eventTag"
#define DEFAULT_PROVIDER "pva"

double timeOut = default_timeout;
string request(DEFAULT_REQUEST);
string defaultProvider(DEFAULT_PROVIDER);
const string noAddress;

void usage() {
  std::cout << "neventListenerEpics <opt> pv_list\n\n"
            << " == <opt> ==\n"
            << "-m : enable monitor (default false)\n"
            << "-h : this help\n"
            << std::endl;
}



int main (int argc, char *argv[]) {

  int opt;
  bool monitor = default_monitor;

  if(monitor) {
    request = "eventTag";
  }
  
  while ((opt = getopt(argc, argv, ":hr:m")) != -1) {
    switch (opt) {
    case 'h':               /* Print usage */
      usage();
      return 0;
    case 'r':               /* Set PVA timeout value */
      request = optarg;
      break;
    case 'm':               /* Monitor mode */
      monitor = true;
      break;
    default :
      usage();
      return 1;
    }
  }



  
  int nPvs = argc - optind;       /* Remaining arg list are PV names */
  if (nPvs < 1) {
    throw std::runtime_error("pv name(s) required");
  }

  vector<string> pvs;     /* Array of PV structures */

  // copy PV names from command line
  for (int n = 0; optind < argc; n++, optind++) {
    pvs.push_back(argv[optind]);
    // std::cout << "pvs = " << pvs[n] << std::endl;          
  }
  
  std::cout << std::boolalpha;
  bool allOK = true;

  PVStructure::shared_pointer pvRequest;
  {
    //    Requester::shared_pointer requester(new RequesterImpl("neventListenerEpics"));
    try {
      pvRequest = CreateRequest::create()->createRequest(request);
    }
    catch (std::bad_alloc& ba) {
      std::cerr << "bad_alloc caught: " << ba.what() << '\n';
    }
    if(pvRequest.get()==NULL) {
      throw std::runtime_error("failed to parse " + request + " string\n");
    }
  }
  std::vector<std::string> pvNames;
  std::vector<std::string> pvAddresses;
  std::vector<std::string> providerNames;
  
  for (int n = 0; n < nPvs; n++) {
    URI uri;
    bool validURI = URI::parse(pvs[n], uri);
    
    std::string providerName(defaultProvider);
    std::string pvName(pvs[n]);
    std::string address(noAddress);
    bool usingDefaultProvider = true;

    if (validURI) {
      
      if (uri.path.length() <= 1) {
        throw std::runtime_error("invalid URI '"+ pvName +"', empty path");
        //        return 1;
      }
      providerName = uri.protocol;
      pvName = uri.path.substr(1);
      address = uri.host;
      usingDefaultProvider = false;
    }
    
    if ((providerName != "pva") && (providerName != "ca")) {
      throw std::runtime_error("invalid " + providerName + "', only 'pva' and 'ca' are supported");
    }
    pvNames.push_back(pvName);
    pvAddresses.push_back(address);
    providerNames.push_back(providerName);
    
    std:: cout << "pvNames "       << pvNames[n]       << "\n"
               << "pvAddresses "   << pvAddresses[n]   << "\n"
               << "providerNames " << providerNames[n] << "\n"
               << std::endl;
  }
  
  // start both the pva and ca client providers
  ClientFactory::start();
  epics::pvAccess::ca::CAClientFactory::start();
  
  // first connect to all, this allows resource (e.g. TCP connection) sharing
  vector<Channel::shared_pointer> channels(nPvs);
  for (int n = 0; n < nPvs; n++) {
    shared_ptr<ChannelRequesterImpl> channelRequesterImpl(new ChannelRequesterImpl(true));
    if (pvAddresses[n].empty())
      channels[n] = getChannelProviderRegistry()->getProvider(
                                                              providerNames[n])->createChannel(pvNames[n],
                                                                                               channelRequesterImpl);
    else
      channels[n] = getChannelProviderRegistry()->getProvider(
                                                              providerNames[n])->createChannel(pvNames[n],
                                                                                               channelRequesterImpl,
                                                                                               ChannelProvider::PRIORITY_DEFAULT,
                                                                                               pvAddresses[n]);
  }

  // for now a simple iterating sync implementation, guarantees order
  for (int n = 0; n < nPvs; n++) {
    Channel::shared_pointer channel = channels[n];
    shared_ptr<ChannelRequesterImpl> channelRequesterImpl = dynamic_pointer_cast<ChannelRequesterImpl>(channel->getChannelRequester());

    if (channelRequesterImpl->waitUntilConnected(timeOut)) {
      shared_ptr<GetFieldRequesterImpl> getFieldRequesterImpl;
      
      // probe for value field
      getFieldRequesterImpl.reset(new GetFieldRequesterImpl(channel));
      // get all to be immune to bad clients not supporting selective getField request
      channel->getField(getFieldRequesterImpl, "");
      
        
      if (getFieldRequesterImpl.get() == 0 ||
          getFieldRequesterImpl->waitUntilFieldGet(timeOut)) {
        // check probe
        if (getFieldRequesterImpl.get()) {
          Structure::const_shared_pointer structure =
            dynamic_pointer_cast<const Structure>(getFieldRequesterImpl->getField());
          if (structure.get() == 0 || structure->getField("value").get() == 0) {
            // fallback to structure
            pvRequest = CreateRequest::create()->createRequest("field()");
          }
        }
      }


      std::vector<uint64_t> detectorID, timestamp;
      
      uint64_t pulseID = 0;
      uint64_t nCount;
      
      getStats stats(0,pulseID,nCount);                                
      stats.start();

      if(!monitor) {

        std::cout << "\t= getRequesterImpl poller =" << std::endl;
        
        while(true) {
          shared_ptr<ChannelGetRequesterImpl> getRequesterImpl(new ChannelGetRequesterImpl(channel->getChannelName()));
          while( stats.keepPolling() ) {
            
            ChannelGet::shared_pointer channelGet = channel->createChannelGet(getRequesterImpl,
                                                                              pvRequest);
            allOK &= getRequesterImpl->waitUntilGet(timeOut);
            pulseID = utils::getULong(channel->getChannelName(),
                                      getRequesterImpl->getPVStructure(),
                                      request);
            //          std::cout << oldPulseID << "\t" << pulseID << std::endl;
            
          }

          // getContent(channel->getChannelName(),
          //            getRequesterImpl->getPVStructure(),"count", nCount);

          nCount = utils::getULong(channel->getChannelName(),
                            getRequesterImpl->getPVStructure(),"count");

          
          // getContent(channel->getChannelName(),
          //            getRequesterImpl->getPVStructure(),
          //            "detectorId",
          //            detectorID);

          // getContent(channel->getChannelName(),
          //            getRequesterImpl->getPVStructure(),
          //            "nTimeStamp",
          //            timestamp);

          utils::getArrayContent(channel->getChannelName(),
                          getRequesterImpl->getPVStructure(),
                          "detectorId", detectorID);
          utils::getArrayContent(channel->getChannelName(),
                          getRequesterImpl->getPVStructure(),
                          "nTimeStamp", timestamp);

          stats.stop();
            
        } // infinite loop

      } // pulseID poll approach
      else {

        std::cout << "\t= monitor =" << std::endl;
        
        shared_ptr<ChannelRequesterImpl> channelRequesterImpl = dynamic_pointer_cast<ChannelRequesterImpl>(channel->getChannelRequester());
        channelRequesterImpl->showDisconnectMessage();

        shared_ptr<MonitorRequesterImpl> monitorRequesterImpl(new MonitorRequesterImpl(channel->getChannelName()));

        //        std::cout << monitorRequesterImpl->getRequesterName() << std::endl;
        
        Monitor::shared_pointer monitorGet = channel->createMonitor(monitorRequesterImpl, pvRequest);
        allOK &= true;

        if (allOK && monitor)
          {
            while (true)
              //epicsThreadSleep(timeOut);
        allOK &= true;
              
          }
        
        
      } // pulseID monitor approach
      
    }   
    
  }
    

    epics::pvAccess::ca::CAClientFactory::stop();
    ClientFactory::stop();
    //       epicsThreadSleep ( 3.0 );
    
    return allOK ? 0 : 1;
    return 0;
  }
