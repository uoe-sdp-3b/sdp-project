#include <Wire.h>
#include "SDPArduino.h"

void setup() {
  SDPsetup();
  Serial.setTimeout(100);
  Serial.write("+++");
  Serial.write("ATCN20");
  Serial.write("ATAC");
  Serial.write("ATID0003");
  Serial.write("ATAC");
  Serial.write("ATWR");
  Serial.write("ATDN");

  Serial.write("Complete");
}

void loop() {
  while(Serial.available()) {
    char c = Serial.read ();
    Serial.write(c);
    delay(1);
    
  }
}
