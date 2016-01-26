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
#define CHECKSUM_FAILED "0CF"
#define UNRECOGNIZED_COMMAND "0UC"

// Encoder Board Variables
#define ROTARY_SLAVE_ADDRESS 5
#define ROTARY_COUNT 6
#define PRINT_DELAY 200


int bytes_to_store = 0;

// Initial motor position is 0.
int positions[ROTARY_COUNT] = {0};
int UO[ROTARY_COUNT] = {0};
int dynamicPositions[ROTARY_COUNT] = {0};
/////////////////////////////////////////////
int rotations[ROTARY_COUNT] = {0};



void setup(){
  
  SDPsetup();
  Serial.setTimeout(100); // time out for accepting a string

  // 1. inital test to see if message is recieved to computer stating "hello world"
   helloWorld();
}

/////////////////////////////////////////////////////////////////////////////////////
//                              Helper Functions                                   //
/////////////////////////////////////////////////////////////////////////////////////


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

void resetDynamicPositions(){
  int i;
  for(i = 0; i < 5; i++){
    dynamicPositions[i] = 0;
  }
  
}

//////////////////////////////////////
//          Robot Stop              //
//////////////////////////////////////

void stopRobot(){

  motorAllStop();

  // send reply message
  Serial.println("0RS");
  printMotorPositions();
  
}

//////////////////////////////////////
//          Robot Forward           //
//////////////////////////////////////

void moveRobotForward(int power){

  //motorStop(0); // this might be useful, in the case the robot is already in a turning move

  motorForward(FRONT_LEFT_MOTOR, power);
  motorForward(FRONT_RIGHT_MOTOR, (int) (power*0.99));
  

  // need to create a reply message to let the PC acknowledge the accepted request and execution
  Serial.println("0RF");

}

//////////////////////////////////////
//          Robot Back              //
//////////////////////////////////////

void moveRobotBackward(int power){

  //motorStop(0); // again might be useful if the robot is in a turning move

  // stop the motors first incase they are moving forward (to prevent mechinical failure)
  motorStop(FRONT_LEFT_MOTOR); 
  motorStop(FRONT_RIGHT_MOTOR);
  
  // set motors to move backwards
  motorBackward(FRONT_LEFT_MOTOR, power);
  motorBackward(FRONT_RIGHT_MOTOR, ((int) power*0.99));

  // send reply message
  Serial.println("0RB");
  
}

//////////////////////////////////////
//          Robot Left              //
//////////////////////////////////////

void rotateRobotLeft(int power){

  //motorAllStop(); // use this for now, can change later on

  // set motors for left rotation
  motorForward(FRONT_RIGHT_MOTOR, power);
  //delay(50);

  // set motors for left rotation
  motorBackward(FRONT_LEFT_MOTOR, power);
  motorForward(TURNING_MOTOR, power);
  
  //motorBackward(FRONT_LEFT_MOTOR, power);
  //motorForward(TURNING_MOTOR, power);
  
  // send reply message 
  Serial.println("0RL");
  
}

//////////////////////////////////////
//          Robot Right             //
//////////////////////////////////////

void rotateRobotRight(int power){

  motorAllStop(); // use this for now, can change later

  // set motors for right rotation
  motorForward(FRONT_LEFT_MOTOR, power);
  motorBackward(TURNING_MOTOR, power);

  // send reply message
  Serial.println("0RR");
  
}

//////////////////////////////////////
//          Robot Kick              //
//////////////////////////////////////

void robotKick(int power){

  int d = 1500 - (power * 10);
  Serial.println(d);

  motorForward(ACTION_MOTOR, 70);
  delay(200);
  
  // move action motor backward
  motorBackward(ACTION_MOTOR,power);
  delay(d);
  motorAllStop();

  motorForward(ACTION_MOTOR, 70);
  delay(150);
  motorAllStop();

  // send reply message
  Serial.println("0RK");
  
}

//////////////////////////////////////
//          Robot Grab              //
//////////////////////////////////////

void robotGrab(int power){

  // move action motor forward
  motorForward(ACTION_MOTOR,power);

  // send reply message
  Serial.println("0RG");
  
}


void robotForwardDistance(int distance){


  // reset dynamicPositions
  resetDynamicPositions();

  // setup positions of rotations
  int rot = (int) (distance * 6.2471) - 10; // 6.2471 = rotations for 1 cm (WRONG ATM)
  int left = dynamicPositions[0];
  int right = dynamicPositions[1];

  // turn on motors
  motorForward(FRONT_LEFT_MOTOR, 100);
  motorForward(FRONT_RIGHT_MOTOR, 100);

  while(left < rot || right < rot){
    delay(5);
    updateMotorPositions();
    //printDynamicPositions();
    left = dynamicPositions[0];
    //Serial.println(left);
    right = dynamicPositions[1];    
    //Serial.println(right);
  }

  motorAllStop();

  Serial.println("0RFD");
  


  
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
    
    int r = (int8_t) Wire.read();  // Must cast to signed 8-bit type
    positions[i] -= r;
    dynamicPositions[i] -= r;

    // will go soon
    rotations[i] = -r;

    
  }
}

void printDynamicPositions(){
    Serial.print("dynamic positions: ");
    for (int i = 0; i < ROTARY_COUNT; i++) {
    Serial.print(dynamicPositions[i]);
    Serial.print(' ');
  }
  Serial.println();
  delay(PRINT_DELAY);  // Delay to avoid flooding serial out
  
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
//                                Milestone 1 communication functions                                     //
////////////////////////////////////////////////////////////////////////////////////////////////////////////

void storeByte(byte one_byte){
  int register_address = 69; 
  Wire.beginTransmission(register_address); // open I2C communication to intended receiver
  Wire.write( one_byte );   // sends the string (which is the file contents)
  Wire.endTransmission(); // end I2C communcation.
  bytes_to_store--;
}

///////////////////////////////////////////////////////////////////////////////////////////////////////////

void serialFlush(){
  while(Serial.available() > 0) {
    char t = Serial.read();
  }
} 


void loop(){
  
  updateMotorPositions();
  //printMotorPositions();
  //printDynamicPositions();
  //Serial.println("0");

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
    c.trim();

    // if mesage is incomplete send error message and flush serial 
    if(c.length() != 6){
      Serial.println(c);
      Serial.println("0IW");
      serialFlush();
      return;
    }
    
      // need to check if signuture is our teams first!
      // avoids unessacary computation on the arduino if it is not a message for out team.
      int sig = getSig(c);
      int seqNo = getSeqNo(c);
      
      // Quits if sig belongs to other teams
      // OR if command is redundant (i.e. already executed)
      if(sig != 0){ return; }


      int opcode = getOpcode(c);
      int arg = getArg(c);
      int check = check_checksum(c, opcode, arg);
      
      // if checksum is correct continue decoding message and execute
      if(check == 1){
    
    
        switch (opcode){

          case STOP:  stopRobot();
          break;
        
          case FORWARD:  robotForwardDistance(arg);
          //case FORWARD: moveRobotForward(arg);
          break;
      
          case BACKWARD:  moveRobotBackward(arg);
          break;
      
          case LEFT:  rotateRobotLeft(arg);
          break;

          case RIGHT:  rotateRobotRight(arg);
          break;

          case KICK: Serial.println("Stage 1"); robotKick(arg); Serial.println("Stage 2");
          break;

          case GRAB: robotGrab(arg);
          break;
          
          case STORE: bytes_to_store = arg; //Serial.println(arg);
          break;
      
          default: Serial.println(UNRECOGNIZED_COMMAND);
          break;
      
        } // switch 
      } // if checksum
      else{
        // checksum is not correct, sig is therefore message was corrupted
        // reply: incorrect message (re-send)
        Serial.println(CHECKSUM_FAILED);
      }
  } // if serial.avalaible 
} // loop body

