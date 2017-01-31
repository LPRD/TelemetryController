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

#define BEGIN_SEND {              \
  Serial.print(F("@@@@@_time:")); \
  Serial.print(millis());
  
#define SEND_ITEM(field, value) \
  Serial.print(F(";"));         \
  Serial.print(F(#field));      \
  Serial.print(F(":"));         \
  Serial.print(value);
  
#define SEND_GROUP_ITEM(value)  \
  Serial.print(F(","));         \
  Serial.print(value);
  
#define SEND_ITEM_NAME(field, value)            \
  Serial.print(F(";"));                         \
  Serial.print(F(field));                       \
  Serial.print(F(":"));                         \
  Serial.print(value);

#define END_SEND                \
  Serial.println(F("&&&&&"));   \
  Serial.flush();               \
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
  if (!Serial.available()) {                    \
    delay(100);                                 \
    if (!Serial.available()) {                  \
      Serial.println(F("READ timeout"));        \
      goto L_ENDREAD;                           \
    }                                           \
  }

// Sorry about the gotos, only needed because macros.  
#define BEGIN_READ                                                      \
  if (Serial.available()) {                                             \
    char _c = '\0';                                                     \
    int _i;                                                             \
    for (_i = 0; _c != '\n'; _i++) {                                    \
      if (_i == READ_BUFFER_SIZE) {                                     \
        Serial.println(F("READ buffer overflow"));                      \
        while (Serial.available() && Serial.read() != '\n')             \
          CHECK_SERIAL_AVAIL                                            \
        goto L_ENDREAD;                                                 \
      }                                                                 \
      CHECK_SERIAL_AVAIL                                                \
      _c = Serial.read();                                               \
      _buffer[_i] = _c;                                                 \
      if (_c == '\r') _i--;                                             \
    }                                                                   \
    _buffer[_i] = '\0';                                                 \
    if (!sscanf(_buffer, (const char*)F("@@@@@%[^&]&&&&&\n"), _data)) { \
      Serial.println(F("READ packet error"));                           \
      goto L_ENDREAD;                                                   \
    }                                                                   \
    if (0);

#define READ_FIELD(field, spec)   \
  else if (sscanf(_data, (const char*)F(#field":" spec), &field))

#define READ_FLAG(field)          \
  else if (!strcmp(_data, (const char*)F(#field":")))

#define READ_DEFAULT(field_name, field) \
  else if (sscanf(_data, (const char*)F("%[^:]:%s"), &field_name, &field))

#define END_READ } L_ENDREAD:;

#endif
