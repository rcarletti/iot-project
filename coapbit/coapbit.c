#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "contiki.h"
#include "contiki-net.h"
#include "sys/etimer.h"

#include "rest-engine.h"

#define DEBUG 1
#if DEBUG
#define PRINTF(...) printf(__VA_ARGS__)
#define PRINT6ADDR(addr) PRINTF("[%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x]", ((uint8_t *)addr)[0], ((uint8_t *)addr)[1], ((uint8_t *)addr)[2], ((uint8_t *)addr)[3], ((uint8_t *)addr)[4], ((uint8_t *)addr)[5], ((uint8_t *)addr)[6], ((uint8_t *)addr)[7], ((uint8_t *)addr)[8], ((uint8_t *)addr)[9], ((uint8_t *)addr)[10], ((uint8_t *)addr)[11], ((uint8_t *)addr)[12], ((uint8_t *)addr)[13], ((uint8_t *)addr)[14], ((uint8_t *)addr)[15])
#define PRINTLLADDR(lladdr) PRINTF("[%02x:%02x:%02x:%02x:%02x:%02x]",(lladdr)->addr[0], (lladdr)->addr[1], (lladdr)->addr[2], (lladdr)->addr[3],(lladdr)->addr[4], (lladdr)->addr[5])
#else
#define PRINTF(...)
#define PRINT6ADDR(addr)
#define PRINTLLADDR(addr)
#endif

/* owner's data */
static unsigned long weight = 60;            //[kg]
static unsigned long stepLength = 30;         //[cm]

static unsigned long cal = 0;               //[calories]
static unsigned heartRate = 60;     //[bpm]
static unsigned long distance = 0;            //[m]
static unsigned stepNum = 0;
static unsigned batteryLevel = 100;    //[%]

struct calendar {
  unsigned sec;
  unsigned min;
  unsigned hour;
  unsigned day;
  unsigned month;
  unsigned year;
} now;


/*--------------------------------functions declaration-------------------------------------------*/

static void steps_per_handler();
void step_get_handler(void* request,
                      void* response,
                      uint8_t *buffer,
                      uint16_t preferred_size,
                      int32_t *offset);

static void calories_per_handler();
void calories_get_handler(void* request,
                      void* response,
                      uint8_t *buffer,
                      uint16_t preferred_size,
                      int32_t *offset);


static void battery_per_handler();
void battery_get_handler(void* request,
                      void* response,
                      uint8_t *buffer,
                      uint16_t preferred_size,
                      int32_t *offset);

static void heart_per_handler();
void heart_get_handler(void* request,
                      void* response,
                      uint8_t *buffer,
                      uint16_t preferred_size,
                      int32_t *offset);

static void distance_per_handler();
void distance_get_handler(void* request,
                      void* response,
                      uint8_t *buffer,
                      uint16_t preferred_size,
                      int32_t *offset);

static void calendar_per_handler();
void calendar_get_handler(void* request,
                      void* response,
                      uint8_t *buffer,
                      uint16_t preferred_size,
                      int32_t *offset);

void calendar_post_handler(void* request,
                        void* response,
                        uint8_t *buffer,
                        uint16_t preferred_size,
                        int32_t *offset);


/*--------------------------------resources definition-------------------------------------------*/


PERIODIC_RESOURCE(steps_periodic,
                  "title=\"Steps\";rt=\"M\";obs",
                  step_get_handler,
                  NULL,
                  NULL,
                  NULL,
                  1 * CLOCK_SECOND,
                  steps_per_handler);


PERIODIC_RESOURCE(calories_periodic,
                  "title=\"Calories\";rt=\"M\";obs",
                  calories_get_handler,
                  NULL,
                  NULL,
                  NULL,
                  30 * CLOCK_SECOND,
                  calories_per_handler);

PERIODIC_RESOURCE(battery_periodic,
                  "title=\"Battery\";rt=\"D\";obs",
                  battery_get_handler,
                  NULL,
                  NULL,
                  NULL,
                  60 * CLOCK_SECOND,
                  battery_per_handler);


PERIODIC_RESOURCE(heart_periodic,
                  "title=\"Heart\";rt=\"M\";obs",
                  heart_get_handler,
                  NULL,
                  NULL,
                  NULL,
                  10 * CLOCK_SECOND,
                  heart_per_handler);

PERIODIC_RESOURCE(distance_periodic,
                  "title=\"Distance\";rt=\"M\";obs",
                  distance_get_handler,
                  NULL,
                  NULL,
                  NULL,
                  20 * CLOCK_SECOND,
                  distance_per_handler);

PERIODIC_RESOURCE(calendar_periodic,
                  "title=\"Calendar\";rt=\"D\";obs",
                  calendar_get_handler,
                  calendar_post_handler,
                  NULL,
                  NULL,
                  1 * CLOCK_SECOND,
                  calendar_per_handler);

/*--------------------------------standard get handler-------------------------------------------*/

void step_get_handler(void* request,
                      void* response,
                      uint8_t *buffer,
                      uint16_t preferred_size,
                      int32_t *offset)
{
  int length;

  length = snprintf((char*)buffer,
                    REST_MAX_CHUNK_SIZE,
                    "{\"e\":{\"n\":\"steps\",\"v\": %u , \"u\":\"steps\"}}\n",
                    stepNum);

  REST.set_header_content_type(response, REST.type.APPLICATION_JSON);
  REST.set_header_etag(response, (uint8_t *) &length, 1);
  REST.set_response_payload(response, buffer, length);
}


void calories_get_handler(void* request,
                      void* response,
                      uint8_t *buffer,
                      uint16_t preferred_size,
                      int32_t *offset)
{
  int length;

  length = snprintf((char*)buffer,
                    REST_MAX_CHUNK_SIZE,
                    "{\"e\":{\"n\":\"calories\",\"v\": %lu , \"u\":\"cal\"}}\n",
                    cal);

  REST.set_header_content_type(response, REST.type.APPLICATION_JSON);
  REST.set_header_etag(response, (uint8_t *) &length, 1);
  REST.set_response_payload(response, buffer, length);
}

void battery_get_handler(void* request,
                      void* response,
                      uint8_t *buffer,
                      uint16_t preferred_size,
                      int32_t *offset)
{
  int length;

  length = snprintf((char*)buffer,
                    REST_MAX_CHUNK_SIZE,
                  "{\"e\":{\"n\":\"battery\",\"v\":%u,\"u\":\"%%\"}}\n",
                   batteryLevel);

  REST.set_header_content_type(response, REST.type.APPLICATION_JSON);
  REST.set_header_etag(response, (uint8_t *) &length, 1);
  REST.set_response_payload(response, buffer, length);
}

void heart_get_handler(void* request,
                      void* response,
                      uint8_t *buffer,
                      uint16_t preferred_size,
                      int32_t *offset)
{
  int length;

  length = snprintf((char*)buffer,
                    REST_MAX_CHUNK_SIZE,
                  "{\"e\":{\"n\":\"hr\",\"v\": %u , \"u\":\"bpm\"}}\n",
                  heartRate);

  REST.set_header_content_type(response, REST.type.APPLICATION_JSON);
  REST.set_header_etag(response, (uint8_t *) &length, 1);
  REST.set_response_payload(response, buffer, length);
}

void distance_get_handler(void* request,
                      void* response,
                      uint8_t *buffer,
                      uint16_t preferred_size,
                      int32_t *offset)
{
  int length;

  length = snprintf((char*)buffer,
                    REST_MAX_CHUNK_SIZE,
                  "{\"e\":{\"n\":\"distance\",\"v\": %lu , \"u\":\"cm\"}}\n",
                  distance);

  REST.set_header_content_type(response, REST.type.APPLICATION_JSON);
  REST.set_header_etag(response, (uint8_t *) &length, 1);
  REST.set_response_payload(response, buffer, length);
}

void calendar_get_handler(void* request,
                      void* response,
                      uint8_t *buffer,
                      uint16_t preferred_size,
                      int32_t *offset)
{
  int length;

  length = snprintf((char*)buffer, REST_MAX_CHUNK_SIZE,
                            "{\"sec\": %u,"
                            "\"min\": %u,"
                            "\"hour\": %u,"
                            "\"day\": %u,"
                            "\"month\": %u,"
                            "\"year\": %u}\n",
                             now.sec,
                             now.min,
                             now.hour,
                             now.day,
                             now.month,
                             now.year);

  REST.set_header_content_type(response, REST.type.APPLICATION_JSON);
  REST.set_header_etag(response, (uint8_t *) &length, 1);
  REST.set_response_payload(response, buffer, length);
}

/*---------------------------------standard post handler------------------------------------------*/

void
calendar_post_handler(void* request, void* response, uint8_t *buffer, uint16_t preferred_size, int32_t *offset)
{
  int lenMin, lenHour, lenSec, lenMonth, lenDay, lenYear;
  const char *recSec = NULL;
  const char *recMin = NULL;
  const char *recHour = NULL;
  const char *recMonth = NULL;
  const char *recDay = NULL;
  const char *recYear = NULL;

  lenSec = REST.get_post_variable(request, "sec", &recSec);
  lenMin = REST.get_post_variable(request, "min", &recMin);
  lenHour = REST.get_post_variable(request, "hour", &recHour);

  lenDay = REST.get_post_variable(request, "day", &recDay);
  lenMonth = REST.get_post_variable(request, "month", &recMonth);
  lenYear = REST.get_post_variable(request, "year", &recYear);

  if (lenMin > 0 &&
      lenHour > 0 &&
      lenSec > 0 &&
      lenDay > 0 &&
      lenMonth > 0 &&
      lenYear > 0)
  {
    now.sec = atoi(recSec);
    now.min = atoi(recMin);
    now.hour = atoi(recHour);

    now.day = atoi(recDay);
    now.month = atoi(recMonth);
    now.year = atoi(recYear);

    if (now.sec < 0 || now.sec > 59 ||
        now.min < 0 || now.min > 59 ||
        now.hour < 0 || now.hour > 24 ||
        now.day < 0 || now.day > 31 ||
        now.month < 0 || now.month > 12 ||
        now.year < 0)
    {
      REST.set_response_status(response, REST.status.BAD_REQUEST);
    }

    REST.set_response_status(response, REST.status.CREATED);
  } else {
      REST.set_response_status(response, REST.status.BAD_REQUEST);
  }
}


/*---------------------------------periodic handler------------------------------------------*/

static void steps_per_handler()
{
  stepNum++;
  REST.notify_subscribers(&steps_periodic);
}

static void calories_per_handler()
{
  cal = (weight * 500 * stepNum)/1000;
  REST.notify_subscribers(&calories_periodic);
}

static void battery_per_handler()
{
  batteryLevel -= 1;
  if (batteryLevel == 0)
    batteryLevel = 100;

  REST.notify_subscribers(&battery_periodic);
}

static void heart_per_handler()
{
  heartRate = ((unsigned short)rand() % 120) + 50;
  REST.notify_subscribers(&heart_periodic);
}

static void distance_per_handler()
{
  distance = stepLength * stepNum ;
  REST.notify_subscribers(&distance_periodic);
}

static void calendar_per_handler()
{
  REST.notify_subscribers(&calendar_periodic);
}


static void reset_resources() {
  stepNum = 0;
  cal = 0;
  distance = 0;
}

static void increase_time() {
  now.sec++;
  if (now.sec == 60) {
    now.min++;
    now.sec = 0;
  }
  if (now.min == 60) {
    now.hour++;
    now.min = 0;
  }
  if (now.hour == 24) {
    now.hour = 0;
    now.min = 0;
    now.sec = 0;
    now.day++;
    reset_resources();
  }
  if (now.day == 31 && now.month == 12) {
    now.hour = 0;
    now.min = 0;
    now.sec = 0;
    now.day = 0;
    now.year++;
  }
}


/*---------------------------------------------------------------------------*/
PROCESS(server, "Server process");
AUTOSTART_PROCESSES(&server);
/*---------------------------------------------------------------------------*/

PROCESS_THREAD(server, ev, data)
{
  PROCESS_BEGIN();

  static struct etimer et;
  etimer_set(&et, CLOCK_SECOND);

  srand(0);

  rest_init_engine();
  rest_activate_resource(&steps_periodic, "Steps");
  rest_activate_resource(&calories_periodic, "Calories");
  rest_activate_resource(&battery_periodic, "Battery");
  rest_activate_resource(&heart_periodic, "Heart");
  rest_activate_resource(&distance_periodic, "Distance");
  rest_activate_resource(&calendar_periodic, "Calendar");

  while(1) {
    PROCESS_WAIT_EVENT();
    if (etimer_expired(&et)) {
      increase_time();
      etimer_reset(&et);
    }
  }
  PROCESS_END();
}

