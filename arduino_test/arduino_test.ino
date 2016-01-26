void setup() {
  Serial.begin(9600);
}

void loop() {
  Serial.println("Sending data");
  Serial.print("@@@@@test1:");
  Serial.println(random(100));
  Serial.print("@@@@@test2:");
  Serial.println(random(10) + 3.14);
  Serial.print("@@@@@test3:");
  Serial.println(random(2) == 1? "abc" : "def");
  Serial.print("@@@@@test4:");
  Serial.println(0.01 * random(-100, 100));


  if (Serial.available()) {
    Serial.print("Data: ");
    Serial.println(Serial.readString());
  }
  delay(100);
}
