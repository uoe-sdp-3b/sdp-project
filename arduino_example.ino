// SDP Group 15 (2014/15)
// Robot Control

// Import the SerialCommand library
#include <SoftwareSerial.h>
#include <SerialCommand.h>

// Import SDPArduino library
#include <Wire.h>
#include <SDPArduino.h>

// Import the timer library
#include "SimpleTimer.h"

// Arduino Ports:
#define RADIO 8
#define LED   13

// Motors
#define LEFT_MOTOR  0
#define RIGHT_MOTOR 1
//#define KICK_MOTOR  2
#define GRAB_MOTOR  2
#define KICK_MOTOR  4

#define TURN_TIME 400
#define MAX_TURN_TIME = 2000
// Inbound Messages
#define PING    "P"
#define MOVE	"M"
#define STOP    "S"
#define GRAB    "G"
#define KICK    "K"
#define OPEN   "O"


// Outbound Messages
#define READY   "READY"
#define PONG    "PONG"
#define DONE    "DONE"

SerialCommand SCmd;
SimpleTimer   timer;

int  lastSeqNo;
bool done;

void setup()
{
  // Set the braud rate:
  Serial.begin(115200);

  // Enable the radio.
  digitalWrite(RADIO, HIGH);

  SDPsetup();
  motorAllStop();

  pinMode(LED, OUTPUT);      // Configure the onboard LED for output
  digitalWrite(LED, LOW);    // default to LED off

  // Setup callbacks for SerialCommand commands
  SCmd.addCommand(PING,    pong);
  SCmd.addCommand(MOVE,	   move); 
  SCmd.addCommand(STOP,    stop_movement);
  SCmd.addCommand(GRAB,    grab);
  SCmd.addCommand(KICK,    kick);
  SCmd.addCommand(OPEN,    open_grabber);

  SCmd.addDefaultHandler(unrecognized);  // Handler for command that isn't matched  (says "What?")

  Serial.println(READY);
}

void loop()
{
  timer.run();
  SCmd.readSerial();     // We don't do much, just process serial commands
}

// Returns true if the command should be ignored (duplicate command)
bool ignore()
{
  int seqNo = atoi(get_argument());

  if (seqNo == lastSeqNo) {
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

void pong()
{ 
  if (ignore()) {
    return;
  }
  
  done = true;
  Serial.println(PONG);
}



char* get_argument()
{
  return SCmd.next();    // Get the next argument from the SerialCommand object buffer
}

void stop_movement()
{
  if (ignore()) {
    return;
  }
  
  motorStop(LEFT_MOTOR);
  motorStop(RIGHT_MOTOR);

  done = true;
  Serial.println(DONE);  
}

void stop_kick()
{
  motorStop(KICK_MOTOR);
}



// Moves foward by number of centimeters given in next argument
void move()
{
  if (ignore()) {
    return;
  }
  
  int power_left;
  int power_right;

  power_left = atoi(get_argument());
  power_right = atoi(get_argument());
  //time in 100s of milliseconds
  int time = atoi(get_argument());
  if(time > 20){
        //Ignoring time because its too long
      Serial.println("Done");
      return;
  }
  
  int args[] = {power_left, power_right, time};
  
  if (!check_checksum(args, 3)){
    Serial.println("Checksum failed");
    return;
  }

  if (power_left > 0)
  {
  motorForward(LEFT_MOTOR, power_left);
  }
  else  
  {
  motorBackward(LEFT_MOTOR, -power_left);
  }

  if (power_right > 0)
  {
  motorForward(RIGHT_MOTOR, power_right);
  }
  else
  {
  motorBackward(RIGHT_MOTOR, -power_right);
  }
  
  delay(time * 100);
  motorStop(RIGHT_MOTOR);
  motorStop(LEFT_MOTOR);

  done = true;
  Serial.println(DONE);
}

void kick() {
  if (ignore()) {
    return;
  }

  int time = atoi(get_argument());
  int power = atoi(get_argument());

  if(time > 1000){
      // Ignoring time because its too long
      Serial.println("Done");
      return;
  }

  do_open_grabber();

  motorForward(KICK_MOTOR, power);
  delay(time);

  motorStop(KICK_MOTOR);

  done = true;
  Serial.println(DONE);
}

void grab() {
  if (ignore()) {
    return;
  }
  
  //motorBackward(KICK_MOTOR, 100);
  motorBackward(GRAB_MOTOR, 100);
  delay(600);
  //motorStop(KICK_MOTOR);
  motorStop(GRAB_MOTOR);

  done = true;
  Serial.println(DONE);
}

void open_grabber() {
  if (ignore()) {
    return;
  }
  
  do_open_grabber();
  done = true;

  Serial.println(DONE); 
}

void do_open_grabber() {
  motorForward(GRAB_MOTOR, 100);
  delay(600);
  motorStop(GRAB_MOTOR);
}

// Takes an array of arguments, and checks them against the next serial command argument
bool check_checksum(int args[], int arg_count) {
  int sent_checksum = atoi(get_argument());

  int arg_checksum = 0;
  int i = 0;

  for (i = 0; i < arg_count; i++){
     arg_checksum += abs(args[i]);
  }
  
  arg_checksum = arg_checksum % 10;
  
  Serial.println(arg_checksum);
  
  return sent_checksum == arg_checksum;
}

// This gets set as the default handler, and gets called when no other command matches.
void unrecognized()
{
  Serial.println("Wat?");
}

