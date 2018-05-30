// Contains defs for standard packet io protocol
// To read floating point numbers, you need to change your arduino configuration settings

// The code & macros in this file are ONLY run on the Arduino end, the test-stand end

// This just works, OK?

#ifndef _TELEMETRY_H
#define _TELEMETRY_H

#include "Arduino.h"
#include <avr/pgmspace.h>

// Set the protocall here: Serial, Ethernet
#define Protocall Ethernet_TCP

#if Protocall == Serial
#define Pr(x) Serial.print(x)
#define Prln(x) Serial.println(x)
#define Read() Serial.read()
#define Avail() Serial.available()
#define Flush() Serial.flush()
#define INIT_GLOBALS() do{}while(0)
#define SETUP() Serial.begin(9600)

#elif Protocall == Ethernet_TCP
#include <Ethernet.h>
#define Pr(x) server.print(x)
#define Prln(x) server.println(x)
#define Read() client.read()
#define Avail() client.available()
#define Flush() client.flush()
#define INIT_GLOBALS do{ \
  byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED }; \
  IPAddress ip(192, 168, 1, 177); \
  // IPAddress myDns(192,168,1, 1); \
  // IPAddress gateway(192, 168, 1, 1); \
  // IPAddress subnet(255, 255, 0, 0); \
  EthernetServer server(5005); \
  EthernetClient client; \
} while(0)
#define SETUP do{ \
  Ethernet.begin(mac, ip); \
  server.begin(); \
  while(!(client = server.available())); \
  assert(client); \ // Not sure about this, discuss
} while(0)

#elif Protocall == Ethernet_UDP
#include <Ethernet.h>
#include <EthernetUdp.h>
#define Pr(x) do{ \
  Udp.beginPacket(Udp.remoteIP(), Udp.remotePort()); \
  Udp.write(x); \
  Udp.endPacket(); \
} while(0)
#define Prln(x) Pr(x.concat('\n'))
#define Read() Udp.read()
#define Avail() Udp.parsePacket()
#define Flush()
#define INIT_GLOBALS do{ \
  byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED }; \
  IPAddress ip(192, 168, 1, 177); \
  unsigned int port 5005; \
  EthernetUDP Udp; \
} while(0)
#define SETUP do{ \
  Ethernet.begin(mac, ip); \
  Udp.begin(port); \
} while(0)

#else
assert(false);
#endif

// Defs for simulating C++ ostream
/* template<class T>  */
/* inline Print &operator <<(Print &stream, T arg)  */
/* { stream.print(arg); return stream; } */

/* enum _EndLineCode { endl }; */

/* inline Print &operator <<(Print &obj, _EndLineCode arg)  */
/* { obj.println(); return obj; } */

#define BEGIN_SEND {              \
  Pr(F("@@@@@_time:")); \
  Pr(millis());
  
#define SEND_ITEM(field, value) \
  Pr(F(";"));         \
  Pr(F(#field));      \
  Pr(F(":"));         \
  Pr(value);
  
#define SEND_GROUP_ITEM(value)  \
  Pr(F(","));         \
  Pr(value);
  
#define SEND_ITEM_NAME(field, value)            \
  Pr(F(";"));                         \
  Pr(field);                          \
  Pr(F(":"));                         \
  Pr(value);

#define END_SEND                \
  Prln(F("&&&&&"));   \
  Flush;               \
}

#define SEND(field, value)      \
  BEGIN_SEND                    \
  SEND_ITEM(field, value)       \
  END_SEND

#define SEND_NAME(field, value) \
  BEGIN_SEND                    \
  SEND_ITEM_NAME(field, value)  \
  END_SEND

#define READ_BUFFER_SIZE 50
char _buffer[READ_BUFFER_SIZE];
char _data[READ_BUFFER_SIZE - 10];

#define CHECK_SERIAL_AVAIL                      \
  if (!Avail()) {                    \
    delay(100);                                 \
    if (!Avail()) {                  \
      Prln(F("READ timeout"));        \
      goto L_ENDREAD;                           \
    }                                           \
  }

// Sorry about the gotos, only needed because macros.  
#define BEGIN_READ                                                      \
  if (Avail()) {                                             \
    char _c = '\0';                                                     \
    int _i;                                                             \
    for (_i = 0; _c != '\n'; _i++) {                                    \
      if (_i == READ_BUFFER_SIZE) {                                     \
        Prln(F("READ buffer overflow"));                      \
        while (Avail() && Read() != '\n')             \
          CHECK_SERIAL_AVAIL                                            \
        goto L_ENDREAD;                                                 \
      }                                                                 \
      CHECK_SERIAL_AVAIL                                                \
      _c = Read();                                               \
      _buffer[_i] = _c;                                                 \
      if (_c == '\r') _i--;                                             \
    }                                                                   \
    _buffer[_i] = '\0';                                                 \
    if (!sscanf(_buffer, "@@@@@%[^&]&&&&&", _data)) {                   \
      Prln(F("READ packet error"));                           \
      goto L_ENDREAD;                                                   \
    }                                                                   \
    if (0);

#define READ_FIELD(field, spec, var)                        \
  else if (sscanf(_data, #field":" spec, &var))

#define READ_FLAG(field)          \
  else if (!strcmp(_data, #field":"))

#define READ_DEFAULT(field_name, var) \
  else if (sscanf(_data, "%[^:]:%s", &field_name, &var))

#define END_READ } L_ENDREAD:;

#endif
