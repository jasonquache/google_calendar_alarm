# Google Calendar Alarm

A 'smart' alarm clock designed to run on a Raspberry Pi in conjunction with an Arduino. Alarms are set by Google Calendar events. The alarm itself consists of playing a radio stream on the Pi (which should be connected to a speaker via the 3.5mm jack) and activating different smart devices (e.g. smart plugs, smart light bulbs) using IFTTT (by sending emails to trigger@applet.ifttt.com). The current time and time until next alarm is displayed on a LCD display connected to the Arduino. The alarm can be stopped or snoozed via buttons connected to the Arduino.

## Getting Started

Clone the repository (to your Rapsberry Pi). Install the prerequisites using pipenv (using the Pipfile provided).

1) You will need to set-up your Google Account to allow making requests to the Google Calendar API - see steps 1 and 2 here: https://developers.google.com/calendar/quickstart/python

2) Alarms are set using events which begin with the word 'wake'/'Wake' - the program will look for events beginning with 'wake' in the calendar that you specify. The calendar is specified inside `config.py`, as the `CALENDAR_ID` variable which must be set to the ID of the calendar (the ID can be found in your Google Calendar settings page).

2) You will need an email account which is used to send emails to IFTTT. At the moment the email and password need to be saved as plain text in the email_creds.json file (hence it is best to create a new Gmail account rather than use your usual one)

3) IFTTT needs to be configured to run whatever smart devices you want upon receiving emails with subject lines:
`#smartplugon`, `#smartplugoff` (others can be found inside the `smartplug` and `smartlight` functions inside the `alarm.py` module - these subject lines can be modified to suit your smart device)

## Setting up the Arduino

1) Connect the circuit as shown in the diagram inside the diagrams directory

2) You will need to upload the Arduino code (inside the LCD_Time/src directory) to your Arduino Uno - NB: the code is written in C++ rather than the normal .ino file (because I used Platformio for VSCode rather than the Arduino IDE)

## Running the Alarm Clock

Run the alarm clock on your Raspberry Pi:
```
pipenv run python run_cal_alarm.py
```
or you can specify verbose mode (will print event information whilst program is running):
```
pipenv run python run_cal_alarm.py -v
```
