/*
 * An example of how to use signals to implement a timer facility using 
 * POSIX threads.
 *
 * Rationale: when using normal Unix signals (SIGALRM), the signal handler executes
 * in a signal handler context.  In a signal handler context, only async-signal-safe
 * functions may be called.  Few POSIX functions are async-signal-safe.
 *
 * Instead of handling the timer activity in the signal handler function,
 * we create a separate thread to perform the timer activity.
 * This timer thread receives a signal from a semaphore, which is signaled ("posted")
 * every time a timer signal arrives.
 *
 * You'll have to redefine "timer_func" below and "set_periodic_timer."
 *
 * Read the man pages of the functions used, such as signal(2), signal(7),
 * alarm(2).
 *
 * Written by Godmar Back <gback@cs.vt.edu>, February 2006.
 */

// required header files
#include <pthread.h>
#include <semaphore.h>
#include <signal.h>
#include <unistd.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <stdbool.h>
#include <sys/time.h>

// forward declaration: user-defined timer function
static void timer_func();

// ----------------------------------------------------------------------------------------
// begin provided code part
// variables needed for timer
static sem_t timer_sem;		// semaphore that's signaled if timer signal arrived
static bool timer_stopped;	// non-zero if the timer is to be timer_stopped
static pthread_t timer_thread;	// thread in which user timer functions execute

/* Timer signal handler.
 * On each timer signal, the signal handler will signal a semaphore.
 */
static void
timersignalhandler() 
{
	/* called in signal handler context, we can only call 
	 * async-signal-safe functions now!
	 */
	sem_post(&timer_sem);	// the only async-signal-safe function pthreads defines
}

/* Timer thread.
 * This dedicated thread waits for posts on the timer semaphore.
 * For each post, timer_func() is called once.
 * 
 * This ensures that the timer_func() is not called in a signal context.
 */
static void *
timerthread(void *_) 
{
	while (!timer_stopped) {
		int rc = sem_wait(&timer_sem);		// retry on EINTR
		if (rc == -1 && errno == EINTR)
		    continue;
		if (rc == -1) {
		    perror("sem_wait");
		    exit(-1);
		}

		timer_func();	// user-specific timerfunc, can do anything it wants
	}
	return 0;
}

/* Initialize timer */
void
init_timer(void) 
{
	/* One time set up */
	sem_init(&timer_sem, /*not shared*/ 0, /*initial value*/0);
	pthread_create(&timer_thread, (pthread_attr_t*)0, timerthread, (void*)0);
	signal(SIGALRM, timersignalhandler);
}

/* Shut timer down */
void
shutdown_timer() 
{
	timer_stopped = true;
	sem_post(&timer_sem);
	pthread_join(timer_thread, 0);
}

/* Set a periodic timer.  You may need to modify this function. */
void
set_periodic_timer(long delay) 
{
	struct itimerval tval = { 
		/* subsequent firings */ .it_interval = { .tv_sec = 0, .tv_usec = delay }, 
		/* first firing */       .it_value = { .tv_sec = 0, .tv_usec = delay }};

	setitimer(ITIMER_REAL, &tval, (struct itimerval*)0);
}

#ifdef __MAIN
// end provided code part
// ----------------------------------------------------------------------------------------

// application-specific part
//
// The following is a simple demonstration of how to use these timers.
//

static sem_t demo_over;	// a semaphore to stop the demo when done

/* Put your timer code in here */
static void 
timer_func() 
{
	/* The code below is just a demonstration. */
	static int i = 0;

	printf ("Timer called %d!\n", i);
	if (++i == 5) {
		shutdown_timer();
		sem_post(&demo_over);	// signal main thread to exit
	}
}

int 
main()
{
	sem_init(&demo_over, /*not shared*/ 0, /*initial value*/0);

	init_timer();
	set_periodic_timer(/* 200ms */200000);

	/* Wait for timer_func to be called five times - note that 
	 * since we're using signals, sem_wait may fail with EINTR.
         */
	while (sem_wait(&demo_over) == -1 && errno == EINTR)
	    continue;
	return 0;
}

#endif
