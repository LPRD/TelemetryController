// Contains defs for standard packet io protocol
// To read floating point numbers, you need to change your arduino configuration settings

// This just works, OK?

#ifndef _TELEMETRY_H
#define _TELEMETRY_H

#include "Arduino.h"
#include <avr/pgmspace.h>

// Defs for simulating C++ ostream
/* template<class T>  */
/* inline Print &operator <<(Print &stream, T arg)  */
/* { stream.print(arg); return stream; } */

/* enum _EndLineCode { endl }; */

/* inline Print &operator <<(Print &obj, _EndLineCode arg)  */
/* { obj.println(); return obj; } */

#ifndef TELEMETRY_SERIAL
#define TELEMETRY_SERIAL Serial
#endif

#define BEGIN_SEND {                            \
  TELEMETRY_SERIAL.print(F("@@@@@_time:"));     \
  TELEMETRY_SERIAL.print(millis());
  
#define SEND_ITEM(field, value)                 \
  TELEMETRY_SERIAL.print(F(";"));               \
  TELEMETRY_SERIAL.print(F(#field));            \
  TELEMETRY_SERIAL.print(F(":"));               \
  TELEMETRY_SERIAL.print(value);
  
#define SEND_GROUP_ITEM(value)                  \
  TELEMETRY_SERIAL.print(F(","));               \
  TELEMETRY_SERIAL.print(value);
  
#define SEND_ITEM_NAME(field, value)            \
  TELEMETRY_SERIAL.print(F(";"));               \
  TELEMETRY_SERIAL.print(field);                \
  TELEMETRY_SERIAL.print(F(":"));               \
  TELEMETRY_SERIAL.print(value);

#define END_SEND                                \
  TELEMETRY_SERIAL.println(F("&&&&&"));         \
  TELEMETRY_SERIAL.flush();                     \
  }

#define SEND(field, value)                      \
  BEGIN_SEND                                    \
  SEND_ITEM(field, value)                       \
    END_SEND

#define SEND_NAME(field, value)                 \
  BEGIN_SEND                                    \
  SEND_ITEM_NAME(field, value)                  \
    END_SEND

#define READ_BUFFER_SIZE 50
char _buffer[READ_BUFFER_SIZE];
char _data[READ_BUFFER_SIZE - 10];

#define CHECK_SERIAL_AVAIL                              \
  if (!TELEMETRY_SERIAL.available()) {                  \
    delay(100);                                         \
    if (!TELEMETRY_SERIAL.available()) {                \
      TELEMETRY_SERIAL.println(F("READ timeout"));      \
      goto L_ENDREAD;                                   \
    }                                                   \
  }

// Sorry about the gotos, only needed because macros.  
#define BEGIN_READ                                                      \
  if (TELEMETRY_SERIAL.available()) {                                   \
    char _c = '\0';                                                     \
    int _i;                                                             \
    for (_i = 0; _c != '\n'; _i++) {                                    \
      if (_i == READ_BUFFER_SIZE) {                                     \
        TELEMETRY_SERIAL.println(F("READ buffer overflow"));            \
        while (TELEMETRY_SERIAL.available() && TELEMETRY_SERIAL.read() != '\n') { \
          CHECK_SERIAL_AVAIL;                                           \
        }                                                               \
        goto L_ENDREAD;                                                 \
      }                                                                 \
      CHECK_SERIAL_AVAIL;                                               \
      _c = TELEMETRY_SERIAL.read();                                     \
      _buffer[_i] = _c;                                                 \
      if (_c == '\r') _i--;                                             \
    }                                                                   \
    _buffer[_i] = '\0';                                                 \
    if (!sscanf(_buffer, "@@@@@%[^&]&&&&&", _data)) {                   \
      TELEMETRY_SERIAL.println(F("READ packet error"));                 \
      goto L_ENDREAD;                                                   \
    }                                                                   \
    if (0);

#define READ_FIELD(field, spec, var)            \
  else if (sscanf(_data, #field":" spec, &var))

#define READ_FLAG(field)                        \
  else if (!strcmp(_data, #field":"))

#define READ_DEFAULT(field_name, var)                           \
  else if (sscanf(_data, "%[^:]:%s", &field_name, &var))

#define END_READ } L_ENDREAD:;

#endif
