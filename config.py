"""Sets variables for use in the other modules."""

import json


# Google Calendar Variables
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

# ID of the calendar you want to use
# This is my 'Daily Scheduling' calendar
CALENDAR_ID = "fcmfp298b0pd6a5rc27opganqs@group.calendar.google.com"

# Email Variables (for sending emails to IFTTT)
SMTP_SERVER = 'smtp.gmail.com' # Email Server
SMTP_PORT = 587 # Server Port
GMAIL_USERNAME = "your_email@gmail.com"
GMAIL_PASSWORD = "your_password"
