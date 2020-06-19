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
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Google Calendar Variables
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

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

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    events_result = service.events().list(calendarId=calendar_id, timeMin=now,
                                        maxResults=50, singleEvents=True,
                                        orderBy='startTime').execute()
    print("Events result type", type(events_result))
    events = events_result.get('items', [])
    print("Events type ", type(events))

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
            # Return the date and time
            return evt_datetime_obj


def alarm():
    # subprocess.check_output(['bash', 'play_radio.sh'])
    try:
        smartplug(True)
    except Exception:
        print("Unable to turn on smart plug.")
    
    try:
        player = vlc.MediaPlayer("eight.mp3")
        player.play()
    except Exception:
        print("Unable to play music via VLC.")
    
    time.sleep(10)


def send_email(recipient, subject, content=''):
    """Send an email."""
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


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    service = build_calendar()

    # Call the API to list all events in 'Daily Scheduling' calendar
    calendar_id = "fcmfp298b0pd6a5rc27opganqs@group.calendar.google.com"

    # Check every 3 seconds
    while True:
        next_wake_datetime = get_next_event(service, calendar_id, 'Wake')
        next_wake_datetime_tz = next_wake_datetime.tzinfo
        current_time = datetime.datetime.now(next_wake_datetime_tz)
        time_diff = next_wake_datetime - current_time

        print("Next alarm start time: {}".format(next_wake_datetime))
        print("Current time: {}".format(current_time))
        print("Time difference: {}".format(time_diff))
        print("")

        threshold_time_diff = datetime.timedelta(seconds=10)
        zero_time = datetime.timedelta(seconds=0)
        if time_diff < threshold_time_diff and time_diff > zero_time:
            print("ALARM RAISED!")
            alarm()
        time.sleep(3)


if __name__ == '__main__':
    main()
    