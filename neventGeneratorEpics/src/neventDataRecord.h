#ifndef NEVENTDATARECORD_H
#define NEVENTDATARECORD_H

#ifdef epicsExportSharedSymbols
#   define neventDataRecordEpicsExportSharedSymbols
#   undef epicsExportSharedSymbols
#endif

#include <pv/pvDatabase.h>
#include <pv/pvTimeStamp.h>

#ifdef neventDataRecordEpicsExportSharedSymbols
#   define epicsExportSharedSymbols
#	undef neventDataRecordEpicsExportSharedSymbols
#endif

#include <shareLib.h>
/* #include "random_event_generator.h" */
#include "event_producer.h"

namespace epics { namespace nevent { 

    class epicsShareClass neventDataRecord : public epics::pvDatabase::PVRecord{
    public:
        POINTER_DEFINITIONS(neventDataRecord);
        static shared_pointer create(const std::string &recordName);
        void update(char*);
        EventProducer* prod;
    private:
        // EPICS Record TimeStamp
        /* epics::pvData::PVTimeStamp pvTimeStamp; */
        /* epics::pvData::TimeStamp timeStamp; */
        // Access to the Record fields
        epics::pvData::PVULongPtr eventTag;
        epics::pvData::PVULongPtr nCount;
        epics::pvData::PVLongArrayPtr nDetectorId;
        epics::pvData::PVIntArrayPtr nTimeStamp;
        // Other
        unsigned int eventID = 0/* , oldID = 0 */;
#ifdef DEBUG
        unsigned int oldID = 0;        
#endif
        neventDataRecord(const std::string &recordName, const epics::pvData::PVStructurePtr &pvStructure);
        bool init();
    };
    
}}

#endif  /* NEVENTDATARECORD_H */
