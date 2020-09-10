"""Module containing functions to interact with Google Calendar."""
from __future__ import print_function
import datetime
import pickle
import pprint
import os.path
from datetime import datetime as dt
from dateutil.parser import parse as dtparse

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from config import SCOPES


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
    """Get list of all calendars."""
    calendar_list = service.calendarList().list(showHidden=True).execute()
    pprint.pprint(calendar_list)


def get_all_calendars_minimal(service):
    """Get list of all calendars summaries."""
    calendar_list = service.calendarList().list(showHidden=True).execute()
    for calendar_list_entry in calendar_list['items']:
        print(calendar_list_entry['summary'])


def get_events(service, calendar_id):
    """List all events in the specified calendar."""
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


def get_next_event(service, calendar_id, event_summary, verbose=False):
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
            if verbose:
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
    service.events().update(calendarId=calendar_id, eventId=event['id'], body=event).execute()

    return True


def update_event_time(service, calendar_id, event_id, new_time):
    """Update start time of specified event.

    Return True if successful."""
    # Get event from API
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    # Update to given new_time (must be in RFC 3339 format)
    event['start']['dateTime'] = new_time
    service.events().update(calendarId=calendar_id, eventId=event['id'], body=event).execute()
    return True
