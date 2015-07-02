/**
 * This is an n-event generator which reads a NeXus file, makes 
 * an event list from it and sends that using 0MQ. 
 *
 * Mark Koennecke, June 2015
 */
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <zmq.h>
#include "nexus2event.h"
#include "posix_timers.h"
#include "md5.h"

static unsigned long pulseID = 0L; 

void timer_func() 
{
  pulseID++;
}

int main(int argc, char *argv[])
{
  static unsigned int oldPulseID = 0;
  char dataHeader[1024], globalHeader[1024];
  pNEventArray data = NULL, tmp = NULL;
  MD5_CTX md5Context;
  unsigned char md5Hash[16];
  struct timespec tPulse;
  void *zmqContext = NULL;
  void *pushSocket = NULL;
  char sockAddress[255];
  unsigned long nCount = 0,  pulseCount = 0;
  int64_t byteCount = 0;
  time_t statTime;
  int64_t rtimestamp[2];
  unsigned int multiplier = 1;

  if(argc < 3) {
    printf("usage:\n\tzmqGenerator nexusfile portNo [multiplier]\n");
    return 1;
  }

  /*
    load NeXus file into en event list
  */
  data = loadNeXus2Events(argv[1]);
  if(data == NULL){
    printf("Failed to load NeXus data to events\n");
  }


  /*
    handle multiplier
  */
  if(argc >= 3){
    multiplier = atoi(argv[3]);
    tmp = multiplyNEventArray(data,multiplier);
    if(tmp == NULL){
      printf("Failed to multiply event array by %d\n", multiplier);
    } else {
      /* killNEventArray(&data); */
      data = tmp;
    }
  }

  printf("Sending %ld n-events per message\n", data->count);

  /*
    create dataHeader
  */
  snprintf(dataHeader,sizeof(dataHeader),
	   "{\"htype\": \"bsr_d-1.0\", \"channels\" :[{\"name\":\"detectorID\", \"type\":\"long\",\"shape\":[%ld] }, [{\"name\":\"timestamps\", \"type\":\"int\",\"shape\":[%ld] } ]}", 
	   data->count, data->count);
  MD5Init(&md5Context);
  MD5Update(&md5Context,dataHeader,strlen(dataHeader));
  MD5Final(md5Hash,&md5Context);
  /* printf("%s, hash =%x\n",dataHeader,md5Hash);  */

  /*
    initialize 0MQ
  */
  zmqContext = zmq_ctx_new();
  pushSocket = zmq_socket(zmqContext,ZMQ_PUSH);
  snprintf(sockAddress,sizeof(sockAddress),"tcp://*:%s",argv[2]);
  zmq_bind(pushSocket,sockAddress);

  /*
    start timer
  */
  init_timer();
  set_periodic_timer(71420); /* 71,42 milliseconds == 14HZ */
  
  statTime = time(NULL);

  while(1){
    if(oldPulseID != pulseID){
      if(pulseID - oldPulseID > 1) {
	printf("Timer miss at pulseID %d\n", pulseID);
      }
      oldPulseID = pulseID;
      /* printf("Timer triggered, pulseID  = %ld\n", pulseID); */

      /*
	create global header
      */
      clock_gettime(CLOCK_MONOTONIC,&tPulse);
      snprintf(globalHeader,sizeof(globalHeader),
	       "{\"global_timespamp\": {\"epoch\": %d, \"ns\": %d}, \"hash\": \"%x\",\"htype\": \"bsr_m-1.0\",\"pulse_id\": %ld}",
	       tPulse.tv_sec,tPulse.tv_nsec, md5Hash,pulseID
	       );
      /* printf(globalHeader); */

      /*
	create timestamp
      */
      rtimestamp[0] = tPulse.tv_sec;
      rtimestamp[1] = tPulse.tv_nsec;

      /*
	send the stuff away 
      */
      byteCount += zmq_send(pushSocket,globalHeader,strlen(globalHeader),ZMQ_SNDMORE);
      byteCount += zmq_send(pushSocket,dataHeader,strlen(dataHeader),ZMQ_SNDMORE);
      byteCount += zmq_send(pushSocket,data->detectorID,data->count*sizeof(int64_t),ZMQ_SNDMORE);
      byteCount += zmq_send(pushSocket,rtimestamp,2*sizeof(int64_t), ZMQ_SNDMORE);
      byteCount += zmq_send(pushSocket,data->timeStamp,data->count*sizeof(int32_t),ZMQ_SNDMORE);
      byteCount += zmq_send(pushSocket,rtimestamp,2*sizeof(int64_t), 0);

      /*
	handle statistics
      */
      nCount += data->count;
      pulseCount++;
      if(time(NULL) >= statTime + 10){
	printf("byteCount = %ld, nCount = %ld, pulseCount = %ld\n", byteCount, nCount, pulseCount); 
	printf("Sent %f MB/sec , %f n* 10^6/sec, %ld pulses\n", byteCount/(1024.*1024.*10.), nCount/10000000., pulseCount);
	pulseCount = 0;
	byteCount = 0;
	nCount = 0;
	statTime = time(NULL);
      }
    }
  }

  killNEventArray(&data);
  zmq_close(pushSocket);
  zmq_ctx_destroy(zmqContext);

  return 0;
}
 
