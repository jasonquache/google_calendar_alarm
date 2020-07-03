#include <Arduino.h>
#include <LiquidCrystal.h>
#include <Bounce2.h>

// initialize the library with the numbers of the interface pins
/* The LCD display circuit:
 * LCD RS pin to digital pin 12
 * LCD Enable pin to digital pin 11
 * LCD D4 pin to digital pin 5
 * LCD D5 pin to digital pin 4
 * LCD D6 pin to digital pin 3
 * LCD D7 pin to digital pin 2
 * LCD R/W pin to ground
 * LCD VSS pin to ground
 * LCD VCC pin to 5V
 * 10K resistor:
 * ends to +5V and ground
 * wiper to LCD VO pin (pin 3) */
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

/* The stop alarm button:
    Button connected to pin 8 */
const int stopbuttonPin = 8;
Bounce stop_debouncer = Bounce();

/* The snooze alarm button:
    Button connected to pin 9*/
const int snoozebuttonPin = 9;
Bounce snooze_debouncer = Bounce();


// Use built in LED
const int ledPin = 13;
// Data from RPi over serial
// String data;
const byte numChars = 32;
char receivedChars[numChars];
char *ptr_receivedChars = receivedChars; // pointer
bool newData = false;
char time_str[] = "Time";
char button_str[] = "button";
char* contains_time; // pointer
char* contains_button; // pointer
bool accept_button = false;


void recvWithEndMarker() {
    static byte ndx = 0;
    char endMarker = '\n';
    char rc;
   
    while (Serial.available() > 0 && newData == false) {
        rc = Serial.read();

        if (rc != endMarker) {
            receivedChars[ndx] = rc;
            ndx++;
            if (ndx >= numChars) {
                ndx = numChars - 1;
            }
        }
        else {
            receivedChars[ndx] = '\0'; // terminate the string
            ndx = 0;
            newData = true;
        }
    }
}

void update_LCD() {
  if (newData) {
    // New data received
    // Now check what it begins with
    
    // contains_time will be a pointer pointing to the first character 
    // of the found "Time" in receivedChars if present, 
    // else it will be a null pointer. Similar for contains_button.
    contains_time = strstr(receivedChars, time_str);
    contains_button = strstr(receivedChars, button_str);
    if (contains_time) {
      // Must be the current time so print it on top row
      lcd.setCursor(0, 0);
      // Current time is in the format "Time: Fri 5  22:57:05"
      // We want to remove the "Time: " (first 6 chars) from start
      ptr_receivedChars += 6;
      lcd.print(ptr_receivedChars);
      ptr_receivedChars -= 6;
    }

    else if (contains_button) {
      // Accept button presses (stop/snooze)
      accept_button = true;
    }

    else {
      // Must be time until next alarm or other message
      // so print on 2nd row
      lcd.setCursor(0, 1);
      // Now print to LCD display
      lcd.print(receivedChars);
    }
    
    // update newdata boolean
    newData = false;
  }
}


void setup() {
  // put your setup code here, to run once:

  // Serial
  Serial.begin(9600);

  // set up the LCD's number of columns and rows:
  lcd.begin(16, 2);

  // Intialise the button pins as inputs
  stop_debouncer.attach(stopbuttonPin, INPUT_PULLUP);
  stop_debouncer.interval(25);
  snooze_debouncer.attach(snoozebuttonPin, INPUT_PULLUP);
  snooze_debouncer.interval(25);
  pinMode(ledPin, OUTPUT);
}

void loop() {
  // put your main code here, to run repeatedly:

  // Update Bounce instances
  stop_debouncer.update();
  snooze_debouncer.update();

  // Check for any message from RPi over serial
  recvWithEndMarker();
  update_LCD();


  //** Stop and snooze buttons **//
  if (accept_button) {
    if (stop_debouncer.rose()) {
      Serial.println("stop");
      accept_button = false;
    }

    else if (snooze_debouncer.rose()) {
      Serial.println("snooze");
      accept_button = false;
    }
  }

}
