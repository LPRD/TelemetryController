#include "../include/communications.h"

void setup() {
  Serial.begin(9600);
}

char data[10] = "";
char data_name[20] = "";
char foo[10] = "abcd";
int i = 0;
float j = 0;
uint8_t k = 0;
long last_sent = 0;
long last_sent1 = 0;

void loop() {
  if (millis() - last_sent > 10) {
    last_sent = millis();
    //Serial.println("Sending data");
    SEND(test1, random(100))
    SEND(test3, random(2) == 1? "abc" : "def")
    SEND(test4, 0.01 * random(-100, 100))
    SEND(test5, foo)
    SEND(test6, sin((float)millis() / 1000))
    SEND(test8, j)
    //Serial.println(millis());
  
    j += 0.01 * random(-100, 101);
  }
  
  if (millis() - last_sent1 > 1000) {
    last_sent1 = millis();
    SEND(test2, k)
    SEND(test7, i)
    i++;
    k++;
  }

  BEGIN_READ
  READ_FIELD(foo, "%s")
    Serial.println("Read foo");
  READ_FIELD(i, "%d")
    Serial.println("Read i");
  READ_DEFAULT(data_name, data) {
    Serial.print("Data name: ");
    Serial.println(data_name);
    Serial.print("Data val:  ");
    Serial.println(data);
  }
  END_READ
}
