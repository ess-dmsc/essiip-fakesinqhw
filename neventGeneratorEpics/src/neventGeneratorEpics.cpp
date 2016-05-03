#include <stddef.h>
#include <stdlib.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>

#include <thread>         // std::this_thread::sleep_until
#include <chrono>         // std::chrono::system_clock
#include <ctime>          // std::time_t, std::tm, std::localtime, std::mktime

#include <pv/serverContext.h>

#include <epicsExport.h>

#include <pv/channelProviderLocal.h>
#include <neventDataRecord.h>

using namespace std;
using std::tr1::static_pointer_cast;
using namespace epics::pvData;
using namespace epics::pvAccess;
using namespace epics::pvDatabase;
using namespace epics::nevent;

unsigned int to_num(char* in) {
  stringstream ss(in);
  unsigned int value;
  ss >> value;
  return value;
}

int main(int argc,char *argv[]) {
  PVDatabasePtr master = PVDatabase::getMaster();
  ChannelProviderLocalPtr channelProvider = getChannelProviderLocal();

  if(argc > 2) {
    EventProducer::multiplier = to_num(argv[2]);
  }
  
  std::cout << "Creating PV(s)" << std::endl;
    
  neventDataRecord::shared_pointer ned = neventDataRecord::create("nevent1");
  master->addRecord(ned);

  std::cout << "Done creating PV(s)" << std::endl;
    
  ServerContext::shared_pointer ctx =
    startPVAServer(PVACCESS_ALL_PROVIDERS,0,true,true);
  PVStringArrayPtr pvNames = master->getRecordNames();
  cout << "Record Names:" << endl << *pvNames << endl;
  string str;

  
  std::thread pull_event(keep_pulling, ned->prod);
  pull_event.detach();

  int pauseValue = (int)round(1.e3/(frequency));

  int pulseCount = 0;
  int statTime = time(NULL);
  
  while(true) {

    auto now = std::chrono::system_clock::now();
    
    ned->update(argv[1]);         

    pulseCount++;
    
    if(time(NULL) >= statTime + 10) {
      
      printf("Sent %f MB/sec , %f n* 10^6/sec, %u pulses\n",
             pulseCount*2*ned->prod->GetEventCount()*sizeof(uint64_t)/(1024.*1024.*10.),
             pulseCount*ned->prod->GetEventCount()/1.e6,
             pulseCount);
      
      pulseCount = 0;
      statTime = time(NULL);
      
    }

    std::this_thread::sleep_until(now + std::chrono::milliseconds(pauseValue));
    
  }


  
  ctx->destroy();
  epicsThreadSleep(1.0);
  channelProvider->destroy();

  return 0; 
}






