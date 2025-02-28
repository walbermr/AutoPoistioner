#include <Arduino.h>

const int buttonPin = 2;  // the number of the pushbutton pin
const int ledPin = 13;    // the number of the LED pin

// variables will change:
int buttonState = 0;  // variable for reading the pushbutton status
const unsigned int MAX_INPUT = 50;
static char input_line [MAX_INPUT];
static unsigned int input_pos = 0;

void setup() {
  // initialize the LED pin as an output:
  pinMode(ledPin, OUTPUT);
  // initialize the pushbutton pin as an input:
  pinMode(buttonPin, INPUT);
  Serial.begin(115200);
}

bool isButtonPressed() {
  return digitalRead(buttonPin) == HIGH;
}

void process_data(const char * data) {
  Serial.println(data);
}

void processIncomingByte(const byte inByte){
  if(inByte == '\n') {
    input_line[input_pos] = 0;
    // terminator reached! process input_line here ...
    process_data(input_line);
    // reset buffer for next time
    input_pos = 0;
  } else if((inByte >= '0' && inByte <= '9') || inByte == '.') {
    if (input_pos < (MAX_INPUT - 1))
      input_line[input_pos++] = inByte;
  } else {
    return;
  }
}

void loop() {
  // read the state of the pushbutton value:
  if(Serial.available () > 0){
    processIncomingByte(Serial.read());
  }

  // check if the pushbutton is pressed. If it is, the buttonState is HIGH:
  if(isButtonPressed()) {
    // turn LED on:
    digitalWrite(ledPin, HIGH);
  } else {
    // turn LED off:
    digitalWrite(ledPin, LOW);
  }
}