/**
 * This is a litte data structure to hold n-events for the n-event generator.
 *
 * Mark Koennecke, June 2015
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "neventArray.h"

pNEventArray createNEventArray(unsigned long count)
{
  pNEventArray result = NULL;

  result = malloc(sizeof(neventArray));
  if(result == NULL){
    return result;
  }
  memset(result,0,sizeof(neventArray));
  result->count = count;
  result->detectorID = malloc(count*sizeof(int64_t));
  result->timeStamp = malloc(count*sizeof(int32_t));
  if(result->detectorID == NULL || result->timeStamp == NULL){
    killNEventArray(&result);
    return NULL;
  }

  return result;
}
/*--------------------------------------------*/
void killNEventArray(pNEventArray *pself)
{
  pNEventArray self = *pself;
  if(self != NULL){
    if(self->detectorID != NULL){
      free(self->detectorID);
    }
    if(self->timeStamp != NULL){
      free(self->timeStamp);
    }
    free(*pself);
  }
}

/*-----------------------------------------------------------*/
/////////////////
// hack
pNEventArray multiplyNEventArray(pNEventArray source, unsigned int factor)
{
  pNEventArray result;
  result = createNEventArray(source->count*factor);
  if(result == NULL){
    return NULL;
  }
  return result;
}
