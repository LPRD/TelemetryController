#define SEND(field, value) {\
  Serial.print("@@@@@");    \
  Serial.print(millis());   \
  Serial.print(":");        \
  Serial.print(#field);     \
  Serial.print(":");        \
  Serial.print(value);      \
  Serial.println("&&&&&");  \
  Serial.flush();           \
}

void setup() {
  Serial.begin(115200);
}

String data = "";
float i = 0;
float j = 0;
long last_sent = 0;
long last_sent1 = 0;

void loop() {
  if (millis() - last_sent > 10) {
    last_sent = millis();
    Serial.println("Sending data");
    SEND(test1, random(100))
    SEND(test3, random(2) == 1? "abc" : "def")
    SEND(test4, 0.01 * random(-100, 100))
    SEND(test5, data)
    SEND(test6, sin((float)millis() / 1000))
    SEND(test8, j)
    Serial.println(millis());
  
    j += 0.01 * random(-100, 101);
  }
  
  if (millis() - last_sent1 > 1000) {
    last_sent1 = millis();
    SEND(test2, random(10) + 3.14)
    SEND(test7, i)
    i += 0.01;
  }

  if (Serial.available()) {
    data = Serial.readString();
    Serial.print("Data: ");
    Serial.println(data);
  }
}
