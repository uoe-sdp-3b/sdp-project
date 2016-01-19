#include "SDPArduino.h"
#include <Wire.h>
#include <stdlib.h>
#define STOP 0

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


int getNumFromChar(char c){
  int r = (int)c - (int)'0';
  return r;
}

int getSig(String c){
  int r = getNumFromChar(c[0]);
  return r;
}

int getOpcode(String c){
  int r = getNumFromChar(c[1]);
  return r;
}

int getArg(String c){
  int r1 = getNumFromChar(c[2]);
  int r2 = getNumFromChar(c[3]);
  int r3 = getNumFromChar(c[4]);
  return ((r1*100)+(r2*10)+r3);
}int r = (int)c - (int)'0';

int check_checksum(String c, int opcode, int arg){
  int checksum = getNumFromChar(c[5]);
  int checksum_recalculated = (opcode + arg) % 10;
  
  if(checksum == checksum_recalculated){
    return 1;
  }
  else {
    return 0;
  }
  
}




void moveRobotForward(int power){

  //motorStop(0); // this might be useful, in the case the robot is already in a turning move
  
  motorForward(1,power);
  motorForward(2,power);

  // need to create a reply message to let the PC acknowledge the accepted request and execution
  Serial.println("Robot forward");

}

void moveRobotBackward(int power){

  //motorStop(0); // again might be useful if the robot is in a turning move

  // stop the motors first incase they are moving forward (to prevent mechinical failure)
  motorStop(1); 
  motorStop(2);
  
  // set motors to move backwards
  motorBackward(1, power);
  motorBackward(2,power);

  // send reply message
  Serial.println("Robot back");
  
}

void rotateRobotLeft(int power){

  motorAllStop(); // use this for now, can change later on

  // set motors for left rotation
  motorForward(2,power);
  motorForward(0,power);

  // send reply message 
  Serial.println("Robot left");
  
}

void rotateRobotRight(int power){

  motorAllStop(); // use this for now, can change later

  // set motors for right rotation
  motorForward(1, power);
  motorBackward(0, power);

  // send reply message
  Serial.println("Robot right");
  
}

void stopRobot(){

  motorAllStop();

  // send reply message
  Serial.println("Robot stopped");
  
}

void robotGrab(){
  
  motorForward(5, 100);
  delay(500);
  motorAllStop();
  Serial.println("Robot Grab");
  
  
}



void loop(){

  // if message is available on our frequency accept it.
  if(Serial.available() > 0){
    
    // save message sent from PC to STRING c.
    String c = Serial.readString();
    
    // inital test to see if message is recieved (delete afterwards)
    // 
    Serial.println(c);


      // need to check if signuture is our teams first!
      // avoids unessacary computation on the arduino if it is not a message for out team.
      int sig = getSig(c);
      if(sig != 0){ return; }

        int opcode = getOpcode(c);
        int arg = getArg(c);
        int check = check_checksum(c, opcode, arg);
        
        // if checksum is correct continue decoding message and execute
        if(check == 1){
      
      
          switch (opcode){

            case STOP:  stopRobot();
            break;
          
            case 1:  moveRobotForward(arg);
            break;
        
            case 2:  moveRobotBackward(arg);
            break;
        
            case 3:  rotateRobotLeft(arg);
            break;

            case 4:  rotateRobotRight(arg);
            break;
            
            case 5: robotGrab();
            break;
        
            default: Serial.println("ERR");
            break;
        
          } // switch  
      } // if checksum
      else{
        // checksum is not correct, sig is therefore message was corrupted
        // reply: incorrect message (re-send)
        Serial.println("CORR");
      }
    // } // if sig == 0 (if this fails, message is not for out team)
  } // if serial.avalaible 
} // loop body

