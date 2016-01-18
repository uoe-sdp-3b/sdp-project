#include <Wire.h>
#include "SDPArduino.h"

void setup() {
  SDPsetup();

  Serial.write("Complete");
}

void loop() {
  while(Serial.available()) {
    char c = Serial.read ();
    Serial.write(c);
    delay(1);
    
  }
}
