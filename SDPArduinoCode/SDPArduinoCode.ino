#include "SDPArduino.h"
#include <Wire.h>
#include <stdlib.h>

void setup(){
  
  SDPsetup();
  Serial.setTimeout(100); // time out for accepting a string

  // setup communication channel to our designated group channel = 0x20
//  Serial.write("+++");
//  Serial.write("ATCN20");
//  Serial.write("ATAC");
//  Serial.write("ATDN");

  // 1. inital test to see if message is recieved to computer stating "hello world"
   helloWorld();
}

int getSig(String c){
  int res;
  char letter[2];
  letter[0] = c[0];
  letter[1] = '\0';
  res = atoi(letter);
  return res;
}

int getOpcode(String c){
  int res;
  char letter[2];
  letter[0] = c[1];
  letter[1] = '\0';
  res = atoi(letter);
  return res;
}

int getArg1(String c){
  int res;
  char letter[2];
  letter[0] = c[2];
  letter[1] = '\0';
  res = atoi(letter);
  return res;
}


int getArg2(String c){
  int res;
  
  char letter[2];
  letter[0] = c[3];
  letter[1] = '\0';
  int a = atoi(letter)*100;
  res = a;
  
  
  letter[0] = c[4];
  letter[1] = '\0';
  int b = atoi(letter)*10;
  res = res + b;  
  
  
  letter[0] = c[5];
  letter[1] = '\0';
  int d = atoi(letter);
  res = res + d;
  
  return res;
}

int check_checksum(String c){
  int res = 1;
  int w,x,y,z;
  
  char letter1[2];
  char letter2[2];
  char letter3[2];
  char letter4[2];
  char letter5[2];
  
  letter1[1] = '\0';
  letter2[1] = '\0';
  letter3[1] = '\0';
  letter4[1] = '\0';
  letter5[1] = '\0';
  
  letter1[0] = c[2];
  w = atoi(letter1);
   
  letter1[0] = c[3];
  x = atoi(letter1);
   
  letter2[0] = c[4];
  y = atoi(letter2);
   
  letter3[0] = c[5];
  z = atoi(letter3);
  
//  char c;
//  (int)c - (int)'0'
  
  letter5[0] = c[6];
  int test2 = atoi(letter5);
  
  
  int test = (w+x+y+z)%10;
  if(test2 != test){
    res = 0;
  }
  return res;
  
}


void loop(){

  // if message is available on our frequency accept it.
  if(Serial.available() > 0){
    
    // save message sent from PC to STRING c.
    String c = Serial.readString();
    
    // inital test to see if message is recieved (delete afterwards)
    Serial.println(c);

    // if checksum is correct continue decoding message and execute
    if(check_checksum){

      int sig = getSig(c);
      int opcode = getOpcode(c);
      int arg1 = getArg1(c);
      int arg2 = getArg2(c);
      
      
      switch (opcode){
        
        case 0:  motorForward(arg1,arg2);
        break;
        
        case 1:  motorBackward(arg1,arg2);
        break;
        
        case 2:  motorStop(arg1);
        break;
        
        case 3:  motorAllStop();
        break;
        
        default: Serial.println("Error in code this should not happen");
        break;
        
      }  
            
    }
    
  }



  
}

