/**
 * This is a utility component which creates a n-event array from 
 * the content of a NeXus file. 
 *
 * Supported: AMOR
 *
 * Mark Koennecke, June 2015
 */

#ifndef __NEXUS2EVENT
#define __NEXUS2EVENT
#include "neventArray.h"

pNEventArray loadNeXus2Events(char *filename);


#endif
