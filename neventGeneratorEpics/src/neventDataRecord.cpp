#include <cstddef>
#include <cstdlib>
#include <cstddef>
#include <string>
#include <cstdio>
//#include <string.h>
#include <memory>
#include <vector>
#include <iostream>
#include <fstream>

#include <pv/standardField.h>
#include <pv/standardPVField.h>

#define epicsExportSharedSymbols

#include <pv/channelProviderLocal.h>
#include <pv/traceRecord.h>

#include "nevent.h"

#include <neventDataRecord.h>


using namespace std;
using std::tr1::static_pointer_cast;
using namespace epics::pvData;
using namespace epics::pvAccess;
using namespace epics::pvDatabase;
using namespace epics::nevent;

neventDataRecord::shared_pointer neventDataRecord::create(const std::string &recordName)
{
    // Structure is:
    //  unsigned long count;
    //  long *detectorID;
    //  int *nTimeStamp;
    
    FieldCreatePtr fieldCreate = getFieldCreate();
    StandardFieldPtr standardField = getStandardField();
    PVDataCreatePtr pvDataCreate = getPVDataCreate();
    StandardPVFieldPtr standardPVField = getStandardPVField();
    
    epics::pvData::PVStructurePtr pvStructure = pvDataCreate->createPVStructure(
        fieldCreate->createFieldBuilder()->
        add("count", pvULong) ->
        add("eventTag", pvULong) ->
        addArray("detectorId", pvLong)->
        addArray("nTimeStamp", pvInt)->
        createStructure()
    );
    
    neventDataRecord::shared_pointer pvRecord(new neventDataRecord(recordName, pvStructure));
	
    if (pvRecord && !pvRecord->init())
	        pvRecord.reset();

    return pvRecord;    
}

neventDataRecord::neventDataRecord(const std::string &recordName, const epics::pvData::PVStructurePtr &pvStructure)
  : epics::pvDatabase::PVRecord(recordName, pvStructure) {
    std::cout << "Constructor" << std::endl;
    prod = new EventProducer;
}


bool neventDataRecord::init() {
  initPVRecord();
  // if (!pvTimeStamp.attach(getPVStructure()->getSubField("timeStamp")))
  //   return false;
    
  nCount = getPVStructure()->getSubField<PVULong>("count");
  if (nCount.get() == NULL)
    return false;

  eventTag = getPVStructure()->getSubField<PVULong>("eventTag");
  if (eventTag.get() == NULL)
    return false;
    
  nDetectorId = getPVStructure()->getSubField<PVLongArray>("detectorId");
  if (nDetectorId.get() == NULL)
    return false;
    
  nTimeStamp = getPVStructure()->getSubField<PVIntArray>("nTimeStamp");
  if (nTimeStamp.get() == NULL)
    return false;

  return true;
}

void neventDataRecord::update(char* filename) {

  prod->GenerateEvents(filename);

#ifdef DEBUG
  if(eventID % 140 == 0) {

    oldID = *(prod->getID());

    if( oldID - eventID > 0) {
      std::cout << "Lost " << oldID - eventID
                << " events"<< std::endl;
      
      // reset counter
      eventID = 0;
      *(prod->getID()) = 0;
    }
  }
#endif
  
  ++eventID;
  unsigned int size = prod->GetEventCount();
  
  // Need to put queued events into arrays
  PVLongArray::svector id_data(size);
  PVIntArray::svector ts_data(size);

  std::copy(prod->id(), prod->id()+size, &id_data[0]);
  std::copy(prod->ts(), prod->ts()+size, &ts_data[0]);

  beginGroupPut();
   
  nCount->put(size);
  eventTag->put(eventID);
  nDetectorId->replace(freeze(id_data));
  nTimeStamp->replace(freeze(ts_data));
  
  // EPICS timestamp updated last
  // timeStamp.getCurrent();
  // pvTimeStamp.set(timeStamp);
  // pvTimeStamp.set(eventID);    // fills with "our" timestamp 

  endGroupPut();
  
}
