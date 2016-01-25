#include "SDPArduino.h"
#include <Wire.h>
#include <stdlib.h>

#define TURNING_MOTOR 0
#define FRONT_LEFT_MOTOR 1
#define FRONT_RIGHT_MOTOR 2
#define ACTION_MOTOR 3

// Inbound message definitions
#define STOP 0
#define FORWARD 1
#define BACKWARD 2
#define LEFT 3
#define RIGHT 4
#define KICK 5 
#define GRAB 6
#define STORE 7

// Outbound message definitions
#define DONE "Robot ignores"
#define CHECKSUM_FAILED "Checksum failed"
#define UNRECOGNIZED_COMMAND "Wat?"

int  lastSeqNo;
bool done;

int bytes_to_store;

// Encoder Board Variables
#define ROTARY_SLAVE_ADDRESS 5
#define ROTARY_COUNT 6
#define PRINT_DELAY 200

// Initial motor position is 0.
int positions[ROTARY_COUNT] = {0};
int UO[ROTARY_COUNT] = {0};
int rotations[ROTARY_COUNT] = {0};


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

// Returns true if the command should be ignored (duplicate command)
// Origin of idea:
// https://bitbucket.org/angel-ignatov/sdp14-15-group-15/src/150da3baeb2045b83add95c70cfca494873c4180/arduino/arduino.ino?at=master&fileviewer=file-view-default
bool ignore(int seqNo)
{
  if (seqNo == lastSeqNo) {
    
    // !! THIS CHECK MIGHT BE REDUNDANT AND NEED REMOVING
    if (done) {
      Serial.println(DONE);
    }
    return true;
  } else {
    lastSeqNo = seqNo;
    done = false;
    return false;
  }
}


int getNumFromChar(char c){
  int r = (int)c - (int)'0';
  return r;
}

int getSig(String c){
  int r = getNumFromChar(c[0]);
  return r;
}

int getSeqNo(String c){
  int r = getNumFromChar(c[6]);
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
  
  motorBackward(FRONT_LEFT_MOTOR,power-2); // left motor is more powerful than right. This will make sure they have the same roatations +- 1 
                                          // could be more acurate if we use 0-255 instead of 0-100 for power rating.
  motorBackward(FRONT_RIGHT_MOTOR,power);

  // need to create a reply message to let the PC acknowledge the accepted request and execution
  Serial.println("Robot forward");

}

void moveRobotBackward(int power){

  //motorStop(0); // again might be useful if the robot is in a turning move

  // stop the motors first incase they are moving forward (to prevent mechinical failure)
  motorStop(FRONT_LEFT_MOTOR); 
  motorStop(FRONT_RIGHT_MOTOR);
  
  // set motors to move backwards
  motorForward(FRONT_LEFT_MOTOR, power);
  motorForward(FRONT_RIGHT_MOTOR,power);

  // send reply message
  Serial.println("Robot back");
  
}

void rotateRobotLeft(int power){

  motorAllStop(); // use this for now, can change later on

  // set motors for left rotation
  motorBackward(FRONT_RIGHT_MOTOR,power);
  motorBackward(TURNING_MOTOR,power);

  // send reply message 
  Serial.println("Robot left");
  
}

void rotateRobotRight(int power){

  motorAllStop(); // use this for now, can change later

  // set motors for right rotation
  motorBackward(FRONT_LEFT_MOTOR, power);
  motorForward(TURNING_MOTOR, power);

  // send reply message
  Serial.println("Robot right");
  
}

void robotKick(int power){

  // move action motor backward
  motorBackward(ACTION_MOTOR,power);

  // send reply message
  Serial.println("Robot kick");
  
}

void robotGrab(int power){

  // move action motor forward
  motorForward(ACTION_MOTOR,power);

  // send reply message
  Serial.println("Robot grab");
  
}


void robotForwardDistance(int distance){
  // will eventually use this function, and parameter ARG from input will represent how far to move forward
  // rather than the power to move forward.

  // need encoders working first!
}

//////////////////////////////////////////////////////////////////////////////////////////////////////////
//                              TESTING ENCODER BOARD READS                                             //
//////////////////////////////////////////////////////////////////////////////////////////////////////////

void updateMotorPositions() {
  // Request motor position deltas from rotary slave board
  Wire.requestFrom(ROTARY_SLAVE_ADDRESS, ROTARY_COUNT);
  
  // Update the recorded motor positions
  for (int i = 0; i < ROTARY_COUNT; i++) {

    // another integer array OU (over/uder 0-30000)
    if(positions[i] > 30000){
      int temp = positions[i];
      int remendier = temp - 30000;
      positions[i] = remendier;
      UO[i] += 1;      
    }

    if(positions[i] < -30000 && positions[i] < 0){
      int temp = positions[i];
      int remendier = temp + 30000;
      positions[i] = remendier;
      UO[i] -= 1;
    }
    
    int r = (int) ((int8_t) Wire.read());  // Must cast to signed 8-bit type
    positions[i] += (r*-1);
    rotations[i] = (r*-1);

    
  }
}

void printMotorPositions() {
  Serial.print("Motor positions: ");
  for (int i = 0; i < ROTARY_COUNT; i++) {
    Serial.print(positions[i]);
    Serial.print(' ');
  }
  Serial.print("                      ");
  Serial.print("UO: ");
  for (int i = 0; i < ROTARY_COUNT; i++) {
    Serial.print(UO[i]);
    Serial.print(' ');
  }
  Serial.print("                       ");
  Serial.print("rotations: ");
  for (int i = 0; i < ROTARY_COUNT; i++) {
    Serial.print(rotations[i]);
    Serial.print(' ');
  }
  Serial.println();
  delay(PRINT_DELAY);  // Delay to avoid flooding serial out
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                Milestone 1 communication functions                                     //
////////////////////////////////////////////////////////////////////////////////////////////////////////////

int getFrequency(String c){
  int f = 100;

  return f;
}

void storeByte(byte one_byte){
  int register_address = 69; 
  //Serial.println("Byte:");
  //Serial.println(one_byte);
  Wire.beginTransmission(register_address); // open I2C communication to intended receiver
  Wire.write( one_byte );   // sends the string (which is the file contents)
  Wire.endTransmission(); // end I2C communcation.
  //Serial.println("Bytes left:");
  bytes_to_store--;
  //Serial.println(bytes_to_store);
}

///////////////////////////////////////////////////////////////////////////////////////////////////////////


void loop(){
  
  //Serial.println(bytes_to_store);
  updateMotorPositions();
  //printMotorPositions();

  // if message is available on our frequency accept it.
  if(Serial.available() > 0){
    
    // sending file though I2C
    if (bytes_to_store > 0) {      
      byte incoming = Serial.read();
      storeByte(incoming);
      return;
    }
    
    // save message sent from PC to STRING c.
    String c = Serial.readString();
    //Serial.println("Full string: <");
    //Serial.println(c);
    
    if(c.length()< 7){ 
      Serial.println("Robot input too short");
      return;
    }
    
      // need to check if signuture is our teams first!
      // avoids unessacary computation on the arduino if it is not a message for out team.
      int sig = getSig(c);
      int seqNo = getSeqNo(c);
      
      // Quits if sig belongs to other teams
      // OR if command is redundant (i.e. already executed)
      if(sig != 0 || ignore(seqNo)){ return; }

      // for accepting file
      if(sig == 3){

        // get frequency from file.
        //int frequency = getFrequency(c);
        
        // storeStringInRegister(int frequency) 


        
      }

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
          
          case STORE: bytes_to_store = arg; //Serial.println(arg);
          break;
      
          default: Serial.println(UNRECOGNIZED_COMMAND);
          break;
      
        } // switch 
        done = true;
      } // if checksum
      else{
        // checksum is not correct, sig is therefore message was corrupted
        // reply: incorrect message (re-send)
        Serial.println(CHECKSUM_FAILED);
      }
      
    // } // if sig == 0 (if this fails, message is not for out team)
  } // if serial.avalaible 
} // loop body

