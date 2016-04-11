TOP=..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE

CXXFLAGS = -Wall -std=c++11 -I$(EPICS_BASE)/include -I$(EPICS_BASE)/include/compiler/clang -I$(EPICS_BASE)/include/os/Darwin -O3

SHRLIB_SEARCH_DIRS += /usr/local/lib $(EPICS_BASE)/lib/$(EPICS_HOST_ARCH) $(HOME)/work/neventGeneratorEpics/lib/$(EPICS_HOST_ARCH)

LIBRARY += neventGenerator neventListener

#neventGenerator_SRCS += neventGeneratorRegister.cpp
neventGenerator_SRCS += neventStats.cpp
neventGenerator_SRCS += neventDataRecord.cpp
#neventGenerator_SRCS += nevent.cpp
neventGenerator_SRCS += event_producer.cpp
neventGenerator_SRCS += neventArray.c
neventGenerator_SRCS += nexus2event.c

neventGenerator_LIBS += pvDatabase
neventGenerator_LIBS += pvAccess
neventGenerator_LIBS += pvData
neventGenerator_LIBS += Com
neventGenerator_LIBS += $(EPICS_BASE_IOC_LIBS)


neventListener_SRCS += neventRequest.cpp
neventListener_SRCS += neventMonitor.cpp
neventListener_SRCS += uri.cpp
neventListener_SRCS += listenerUtils.cpp
neventListener_SRCS += neventStats.cpp


PROD_HOST += neventGeneratorEpics neventListenerEpics
neventGeneratorEpics_SRCS += neventGeneratorEpics.cpp # neventArray.c nexus2event.c

neventListenerEpics_SRCS += neventListenerEpics.cpp

neventGeneratorEpics_LIBS += neventGenerator
neventGeneratorEpics_LIBS += pvDatabase
neventGeneratorEpics_LIBS += pvAccess
neventGeneratorEpics_LIBS += pvData
neventGeneratorEpics_LIBS += Com
neventGeneratorEpics_LIBS += NeXus

neventListenerEpics_LIBS += neventListener
neventListenerEpics_LIBS += pvAccess
neventListenerEpics_LIBS += pvData



#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE


