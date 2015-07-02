/**
 * This is a simple test reader for the n-events sent by the zmqGenerator. 
 * Just a proof of concept and testing thinsg and a template for implementing 
 * more serious readers.
 *
 * Mark Koennecke, June 2015
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include <zmq.h>


int main(int argc, char *argv[])
{
  unsigned long nCount = 0, pulseCount = 0, oldPulseID = 0, pulseID = 0, nEvents = 0;
  int64_t byteCount = 0;
  int bytesRead, status;
  void *zmqContext = NULL;
  void *pullSocket = NULL;
  time_t statTime;
  char headerData[1024];
  char *pPtr, *pEnd;
  int64_t *dataBuffer = NULL, rtimestamp[2];
  unsigned int dataBufferSize = 0;

  if(argc < 2) {
    printf("usage:\n\tzmqReader endpoint\n\twith endpoint being in the format: tcp://host:port\n");
    return 1;
  }
  
  /*
   * initialize 0mq
   */
  zmqContext = zmq_ctx_new();
  pullSocket = zmq_socket(zmqContext,ZMQ_PULL);
  status = zmq_connect(pullSocket,argv[1]);

  statTime = time(NULL);
  while(1) {
    /*
      receive global header and pull out pulseID
    */ 
    bytesRead = zmq_recv(pullSocket, headerData, sizeof(headerData),0);
    if(bytesRead >= sizeof(headerData)) {
      headerData[sizeof(headerData)-1] = '\0';
    } else {
      headerData[bytesRead] = '\0';
    }
    /*
      This bit is for synchronisation: we may connect to the server 
      mid-message...
    */
    if(strstr(headerData,"bsr_m-1.0") == NULL){
      printf("Skipping unknown message \n"); 
      continue;
    } else {
      /* printf("Global header: %s\n",headerData); */
      byteCount += bytesRead;
    }
    pPtr = strstr(headerData, "pulse_id\":");
    if(pPtr != NULL){
      pPtr += strlen( "pulse_id\":");
    }
    pEnd = strchr(pPtr,'}');
    *pEnd = '\0';
    pulseID = atoi(pPtr);
    /* printf("pulseID = %ld\n", pulseID); */
    if(pulseID - oldPulseID > 1) {
      printf("Missed pulse at pulseID %ld\n", pulseID);
    }
    oldPulseID = pulseID;

    /*
      receive data header and put out data length
    */
    bytesRead = zmq_recv(pullSocket, headerData, sizeof(headerData),0);
    headerData[bytesRead] = '\0';
    byteCount += bytesRead;
    /* printf("Data header: %s\n",headerData); */
    pPtr = strstr(headerData, "shape\":[");
    if(pPtr != NULL){
      pPtr += strlen("shape\":[");
    }
    pEnd = strchr(pPtr,']');
    *pEnd = '\0';
    nEvents = atoi(pPtr);
    /* printf("nEvents = %d\n", nEvents); */
    nCount += nEvents;

    /*
      make sure that we have enough data buffer size
    */
    if(nEvents *sizeof(int64_t) != dataBufferSize){
      if(dataBuffer != NULL){
	free(dataBuffer);
      }
      dataBuffer = malloc(nEvents*sizeof(int64_t));
      if(dataBuffer == NULL){
	printf("Out of memory allocating data buffer\n");
	return 1;
      }
      dataBufferSize = nEvents*sizeof(int64_t);
    }

    /*
      read the two data elements
    */
    byteCount += zmq_recv(pullSocket,dataBuffer,dataBufferSize,0);
    byteCount += zmq_recv(pullSocket,rtimestamp,sizeof(rtimestamp),0);
    byteCount += zmq_recv(pullSocket,dataBuffer,dataBufferSize,0);
    byteCount += zmq_recv(pullSocket,rtimestamp,sizeof(rtimestamp),0);

    /*
      do the statistics
    */
    pulseCount++;
    if(time(NULL) >= statTime + 10){
      /* printf("byteCount = %ld, nCount = %ld, pulseCount = %ld\n", byteCount, nCount, pulseCount);  */
      printf("Received %f MB/sec , %f n* 10^6/sec, %ld pulses\n", byteCount/(1024.*1024.*10.), nCount/10000000., pulseCount);
      pulseCount = 0;
      byteCount = 0;
      nCount = 0;
      statTime = time(NULL);
    }
  }

  /*
    never get here, but close it anyway
  */
  zmq_close(pullSocket);
  zmq_ctx_destroy(zmqContext);

  return 0;

}
