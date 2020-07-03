from __future__ import print_function
import datetime
from dateutil.parser import parse as dtparse
from datetime import datetime as dt
import pickle
import pprint
import os.path
import time
import subprocess
import vlc
import smtplib
import json
import serial
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Google Calendar Variables
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Email Variables
SMTP_SERVER = 'smtp.gmail.com' # Email Server
SMTP_PORT = 587 # Server Port
email_creds = json.load(
    open("email_credentials.json"), object_pairs_hook=dict)
GMAIL_USERNAME = email_creds["GMAIL_USERNAME"]
GMAIL_PASSWORD = email_creds["GMAIL_PASSWORD"]


def build_calendar():
    """Get the credentials and create calendar."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

def get_all_calendars(service):
    # Call the API to get list of all calendars
    calendar_list = service.calendarList().list(showHidden=True).execute()
    pprint.pprint(calendar_list)

def get_all_calendars_minimal(service):
    # Call the API to get list of all calendars
    calendar_list = service.calendarList().list(showHidden=True).execute()
    for calendar_list_entry in calendar_list['items']:
        print(calendar_list_entry['summary'])

def get_events(service, calendar_id):
    """Call the API to list all events in the specified calendar."""
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    events_result = service.events().list(calendarId=calendar_id, timeMin=now,
                                        maxResults=50, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])

def get_next_event(service, calendar_id, event_summary):
    """Get time for desired next event in calendar.
    
    Finds the first event in the specified calendar whose event summary
    starts with the specified 'event_summary'. Returns the start
    date/time of that event as a datetime object and the id of that
    event."""
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    events_result = service.events().list(calendarId=calendar_id, timeMin=now,
                                        maxResults=50, singleEvents=True,
                                        orderBy='startTime').execute()
    # print("Events result type", type(events_result))
    events = events_result.get('items', [])
    # print("Events type ", type(events))

    if not events:
        print('No upcoming events found.')
    for event in events:
        if event['summary'].startswith(event_summary):
            # Event summary
            evt_summary = event['summary']
            # Get start time of event
            start = event['start'].get('dateTime', event['start'].get('date'))
            # Reformat it using dtparse and dt.strftime
            tmfmt = '%d %B, %H:%M %p'
            evt_datetime_str = dt.strftime(dtparse(start), format=tmfmt)
            evt_datetime_obj = dtparse(start)
            # Print event summary with start time
            print("{} at {}".format(evt_summary, evt_datetime_str))
            # Return the datetime obj and the event id
            return evt_datetime_obj, event['id']

def update_event_summary(service, calendar_id, event_id, new_summary):
    """Append new_summary to summary of specified event.
    
    Return True if successful."""
    # Get event from API
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    # Modify event summary (append new_summary to start)
    prev_evt_summary = event['summary']
    event['summary'] = "{} {}".format(new_summary, prev_evt_summary)
    updated_event = service.events().update(calendarId=calendar_id, eventId=event['id'], body=event).execute()

    return True

def update_event_time(service, calendar_id, event_id, new_time):
    """Update start time of specified event.
    
    Return True if successful."""
    # Get event from API
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    # Update to given new_time (must be in RFC 3339 format)
    event['start']['dateTime'] = new_time
    updated_event = service.events().update(calendarId=calendar_id, eventId=event['id'], body=event).execute()
    return True

def alarm(serial_connection):
    """Activate the alarm.
    
    Play music/radio, send 'wake up' message to Arduino, wait for
    message from Arduino to stop or snooze the alarm. Return
    'stop' or 'snooze'."""

    ser = serial_connection
    try:
        smartplug(True)
    except Exception:
        print("Unable to turn on smart plug.")
    
    try:
        # Set volume to 100%
        subprocess.call(["bash", "configure_audio.sh"])
        # Play BBC Radio 1 using VLC
        # player = vlc.MediaPlayer("eight.mp3")
        player = vlc.MediaPlayer("http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio1_mf_p")
        player.play()
    except Exception:
        print("Unable to play music via VLC.")

    # Show message on LCD
    msg = "--WAKE UP NOW!--\n"
    ser.write(msg.encode('utf-8'))

    # Alarm lasts for at least 5 seconds before accepting stop/snooze button
    time.sleep(5)
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            if line == "stop" or line == "snooze":
                # Stop alarm
                player.stop()
                smartplug(False)
                # Refresh the 2nd row of LCD
                ser.write("                ".encode('utf-8'))
                # Return either 'stop' or 'snooze'
                return line


def send_email(recipient, subject, content=''):
    """Send an email with specified content.
    
    Return True if email sent successfully, else
    return False."""
    # Create headers
    headers = ["From: " + GMAIL_USERNAME, "Subject: " + subject, "To: " + recipient,
                               "MIME-Version: 1.0", "Content-Type: text/html"]
    headers = "\r\n".join(headers)
    
    try:
        # Connect to Gmail Server
        session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        session.ehlo()
        session.starttls()
        session.ehlo()

        # Login to Gmail
        session.login(GMAIL_USERNAME, GMAIL_PASSWORD)

        # Send email, then quit
        session.sendmail(GMAIL_USERNAME, recipient, headers + "\r\n\r\n" + content)
        session.quit

        return True

    except Exception:
        print("Email error!")
        return False
 

def smartplug(on=True):
    """Turn smart plug on/off by sending email."""
    if on:
        subject = '#smartplugon'
    elif not on:
        subject = '#smartplugoff'
    else:
        return False
    
    return send_email(recipient='trigger@applet.ifttt.com', subject=subject)


def connect_arduino():
    """Find Arduino port and return serial object."""
    # Serial connection
    # Try /dev/ttyACM0 through /dev/ttyACM9
    for i in range(10):
        try:
            port = '/dev/ttyACM' + str(i)
            ser = serial.Serial(port, 9600, timeout=1, write_timeout=5)
            ser.flush()
            print("Successfully connected to Arduino on port {}".format(port))
            return ser
        except serial.serialutil.SerialException:
            pass
    
    # If not port found, return None
    return None
        

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    cal_service = build_calendar()

    # 'Daily Scheduling' Google Calendar
    calendar_id = "fcmfp298b0pd6a5rc27opganqs@group.calendar.google.com"

    # Serial connection
    serial_service = connect_arduino()

    # Check every 0.5 seconds
    while True:        
        next_wake_datetime, event_id = get_next_event(cal_service, calendar_id, 'Wake')
        next_wake_datetime_tz = next_wake_datetime.tzinfo
        current_time = datetime.datetime.now(next_wake_datetime_tz)
        time_diff = next_wake_datetime - current_time

        print("Next alarm start time: {}".format(next_wake_datetime))
        print("Current time: {}".format(current_time))
        print("Time difference: {}".format(time_diff))
        print("")

        threshold_time_diff = datetime.timedelta(seconds=10)
        zero_time = datetime.timedelta(seconds=0)

        # Send time until next alarm to Arduino via serial
        time_diff_list = str(time_diff).split(':')
        secs = time_diff_list[2].split('.')[0]
        msg = "Alarm: {}:{}:{}\n".format(time_diff_list[0], time_diff_list[1], secs)
        try:
            serial_service.write(msg.encode('utf-8'))
        except serial.serialutil.SerialTimeoutException:
            pass
        
        # Send current time to Arduino via serial
        # Only send the time (not date) in format hrs:mins:secs
        current_time_trimmed = (str(current_time).split(' ')[1]).split('.')[0]
        current_time_msg = "Time: {}\n".format(current_time_trimmed)
        try:
            serial_service.write(current_time_msg.encode('utf-8'))
        except serial.serialutil.SerialTimeoutException:
            pass

        # Check if time to sound alarm
        if time_diff < threshold_time_diff and time_diff > zero_time:
            print("ALARM RAISED!")
            alarm_status = alarm(serial_connection=serial_service)
            
            if alarm_status == "stop":
                # When alarm stopped, modify event summary of wake calendar event
                # So it is not detected again
                print("Stopped alarm")
                update_event_summary(service=cal_service, calendar_id=calendar_id,
                    event_id=event_id, new_summary="x")
            elif alarm_status == "snooze":
                print("Snooze for 5 mins")
                # https://stackoverflow.com/questions/8556398/generate-rfc-3339-timestamp-in-python/39418771#39418771
                # 5 mins (300 secs) snooze time
                snooze_time = (datetime.datetime.now(next_wake_datetime_tz) + datetime.timedelta(seconds=300)).isoformat()
                update_event_time(service=cal_service, calendar_id=calendar_id,
                    event_id=event_id, new_time=snooze_time)

        time.sleep(0.5)


if __name__ == '__main__':
    main()
    