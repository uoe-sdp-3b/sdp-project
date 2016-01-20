#include "SDPArduino.h"
#include <Wire.h>
#include <stdlib.h>

#define TURNING_MOTOR 0
#define FRONT_LEFT_MOTOR 1
#define FRONT_RIGHT MOTOR 2
#define ACTION_MOTOR 3

#define STOP 0
#define FORWARD 1
#define BACKWARD 2
#define LEFT 3
#define RIGHT 4
#define KICK 5 
#define GRAB 6

void setup(){
  
  SDPsetup();
  Serial.setTimeout(1000); // time out for accepting a string

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
}

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


void stopRobot(){

  motorAllStop();

  // send reply message
  Serial.println("Robot stopped");
  
}

void moveRobotForward(int power){

  //motorStop(0); // this might be useful, in the case the robot is already in a turning move
  
  motorForward(FRONT_LEFT_MOTOR,power);
  motorForward(FRONT_RIGHT_MOTOR,power);

  // need to create a reply message to let the PC acknowledge the accepted request and execution
  Serial.println("Robot forward");

}

void moveRobotBackward(int power){

  //motorStop(0); // again might be useful if the robot is in a turning move

  // stop the motors first incase they are moving forward (to prevent mechinical failure)
  motorStop(FRONT_LEFT_MOTOR); 
  motorStop(FRONT_RIGHT_MOTOR);
  
  // set motors to move backwards
  motorBackward(FRONT_LEFT_MOTOR, power);
  motorBackward(FRONT_RIGHT_MOTOR,power);

  // send reply message
  Serial.println("Robot back");
  
}

void rotateRobotLeft(int power){

  motorAllStop(); // use this for now, can change later on

  // set motors for left rotation
  motorForward(FRONT_RIGHT_MOTOR,power);
  motorForward(TURNING_MOTOR,power);

  // send reply message 
  Serial.println("Robot left");
  
}

void rotateRobotRight(int power){

  motorAllStop(); // use this for now, can change later

  // set motors for right rotation
  motorForward(FRONT_LEFT_MOTOR, power);
  motorBackward(TURNING_MOTOR, power);

  // send reply message
  Serial.println("Robot right");
  
}

void robotKick(int power){

  // move action motor backward
  motorBackward(ACTION_MOTOR,power);

  // send reply message
  Serial.println("Kick");
  
}

void robotGrab(int power){

  // move action motor forward
  motorForward(ACTION_MOTOR,power);

  // send reply message
  Serial.println("Grab");
  
}





void loop(){

  // if message is available on our frequency accept it.
  if(Serial.available() > 0){
    
    // save message sent from PC to STRING c.
    String c = Serial.readString();
    
    // inital test to see if message is recieved (delete afterwards)
    // Serial.println(c);


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
          
            case FORWARD:  moveRobotForward(arg);
            break;
        
            case BACKWARD:  moveRobotBackward(arg);
            break;
        
            case LEFT:  rotateRobotLeft(arg);
            break;

            case RIGHT:  rotateRobotRight(arg);
            break;
            
            case KICK: robotKick(arg);
            break;

            case GRAB: robotGrab(arg);
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

