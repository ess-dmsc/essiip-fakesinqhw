/**
 * This is a utility component which creates a n-event array from 
 * the content of a NeXus file. 
 *
 * Supported: AMOR
 *
 * Mark Koennecke, June 2015
 */
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <napi.h>
#include <assert.h>
#include <math.h>
#include "neventArray.h"

static unsigned long countNeutrons(int32_t *data, unsigned int size)
{
  unsigned long count = 0;
  int i;

  for(i = 0; i < size; i++){
    count += data[i];
  }
  return count;
}
/*------------------------------------------------------------------------*/
static pNEventArray loadAMOR(char *filename)
{
  NXhandle handle;
  int32_t dim[3];
  int status, i, j, k, l, nCount, rank, type;
  unsigned int size, offset;
  int32_t *data = NULL;
  float *tof = NULL;
  int32_t iTof;
  unsigned long nEvents;
  pNEventArray evData = NULL;
  unsigned int detID = -1;

  status = NXopen(filename,NXACC_READ,&handle);
  if(status != NX_OK){
    printf("Failed to open NeXus file %s\n", filename);
    return NULL;
  }

  status = NXopenpath(handle,"/entry1/AMOR/area_detector/data");
  if(status != NX_OK){
    printf("NeXus file %s in wrong format\n", filename);
    return NULL;
  }
  NXgetinfo(handle,&rank,dim,&type);
  for(i = 1, size = dim[0]; i < 3; i++){
    size *= dim[i];
  }
  data = malloc(size*sizeof(int32_t));
  tof = malloc(dim[2]*sizeof(float));
  if(data == NULL || tof == NULL ){
    printf("failed to allocate memory for NeXus data\n");
    return NULL;
  }
  NXgetdata(handle,data);

  status = NXopenpath(handle,"/entry1/AMOR/area_detector/time_binning");
  if(status != NX_OK){
    printf("NeXus file %s in wrong format\n", filename);
    return NULL;
  }
  NXgetdata(handle,tof);
  
  NXclose(&handle);

  nEvents = countNeutrons(data,size);
  evData = createNEventArray(nEvents);
  if(evData == NULL){
    return NULL;
  }
  printf("%s contains %ld neutrons\n",filename,nEvents);

  nEvents = 0;
  for(i = 0; i < dim[0]; i++){
    for(j = 0; j < dim[1]; j++){
      detID++;
      offset = i*dim[1]*dim[2] + j*dim[2];
      for(k = 0; k < dim[2]; k++){
	nCount = data[offset+k];
	iTof = round(tof[k]/10.);
	for(l = 0; l < nCount; l++){
	  evData->detectorID[nEvents] = detID;
	  evData->timeStamp[nEvents] = iTof;
	  nEvents++;
	}
      }
    }
  }

  return evData;
}


/*------------------------------------------------------------------------*/
static pNEventArray loadFOCUS(char *filename)
{
  NXhandle handle;
  int32_t dim[2+1];
  int status, i, j, k, l, nCount, rank, type;
  unsigned int size, offset;
  int32_t *data = NULL;
  float *tof = NULL;
  int32_t *tof_monitor = NULL;
  int32_t iTof;
  int32_t mTof;
  unsigned long nEvents;
  pNEventArray evData = NULL;
  unsigned int detID = -1;

  status = NXopen(filename,NXACC_READ,&handle);
  if(status != NX_OK){
    printf("Failed to open NeXus file %s\n", filename);
    return NULL;
  }

  status = NXopenpath(handle,"/entry1/FOCUS/merged/counts");
  if(status != NX_OK){
    printf("NeXus file %s in wrong format\n", filename);
    return NULL;
  }
  NXgetinfo(handle,&rank,dim,&type);

  for(i = 1, size = dim[0]; i < 2; i++){
    size *= dim[i];
  }
  dim[rank] = dim[rank-1];

  data = malloc(size*sizeof(int32_t));
  tof = malloc(dim[1]*sizeof(float));
  tof_monitor = malloc(dim[1]*sizeof(int32_t));
  if(data == NULL || tof == NULL || tof_monitor == NULL){
    printf("failed to allocate memory for NeXus data\n");
    return NULL;
  }
  NXgetdata(handle,data);

  status = NXopenpath(handle,"/entry1/FOCUS/merged/time_binning");
  if(status != NX_OK){
    printf("NeXus file %s in wrong format\n", filename);
    return NULL;
  }
  NXgetdata(handle,tof);

  status = NXopenpath(handle,"/entry1/FOCUS/tof_monitor");
  if(status != NX_OK){
    printf("NeXus file %s in wrong format\n", filename);
    return NULL;
  }
  NXgetdata(handle,tof_monitor);
  
  NXclose(&handle);

  nEvents = countNeutrons(data,size) + countNeutrons(tof_monitor,dim[2]);

  evData = createNEventArray(nEvents);
  if(evData == NULL){
    return NULL;
  }
  printf("%s contains %ld neutrons\n",filename,nEvents);

  nEvents = 0;

  for(i = 0; i < dim[0]; i++){
    detID++;
    offset = i*dim[1];
    for(j = 0; j < dim[1]; j++){
      nCount = data[offset+j];
      iTof = round(tof[j]/10.);

      for(l = 0; l < nCount; l++){
        evData->detectorID[nEvents] = detID;
        evData->timeStamp[nEvents] = iTof;

        nEvents++;
      }
    }
  }

  detID++;
  for(j = 0; j < dim[2]; j++){
    nCount = tof_monitor[j];
    iTof = round(tof[j]/10.);
    
    for(l = 0; l < nCount; l++){
      evData->detectorID[nEvents] = detID;
      evData->timeStamp[nEvents] = iTof;
      
      nEvents++;
    }
  }

  free(data);
  free(tof_monitor);
  free(tof);

  return evData;
}



/*-----------------------------------------------------------------------*/
pNEventArray loadNeXus2Events(char *filename)
{
  pNEventArray nxData = NULL;
  printf("%s\n",filename);

  if(strstr(filename,"amor") != NULL){
    printf("loadAMOR\n");
    nxData = loadAMOR(filename);
  }
  /////////////////
  // hack
  else {
    if(strstr(filename,"focus") != NULL) {
      printf("loadFOCUS\n");
      nxData = loadFOCUS(filename);
    }
    else
      printf("Filetype not supported\n");
  }

  return nxData;
}



