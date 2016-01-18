#include <Wire.h>
#include "SDPArduino.h"

void setup() {
  SDPsetup();
  Serial.setTimeout(100);
  
}

void loop() {
  while (Serial.available() > 0) {
    String c = Serial.readString();
    Serial.println(c);
  }
}
