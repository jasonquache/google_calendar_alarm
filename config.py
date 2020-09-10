"""Sets variables for use in the other modules."""

import json


# Google Calendar Variables
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

# ID of the calendar you want to use
# This is my 'Daily Scheduling' calendar
CALENDAR_ID = "fcmfp298b0pd6a5rc27opganqs@group.calendar.google.com"

# Email Variables
SMTP_SERVER = 'smtp.gmail.com' # Email Server
SMTP_PORT = 587 # Server Port
email_creds = json.load(
    open("email_credentials.json"), object_pairs_hook=dict)
GMAIL_USERNAME = email_creds["GMAIL_USERNAME"]
GMAIL_PASSWORD = email_creds["GMAIL_PASSWORD"]
