void setup() {
  Serial.begin(9600);
}

void loop() {
  Serial.print("@@@@@test:");
  Serial.println(random(100));
  delay(1000);
}
