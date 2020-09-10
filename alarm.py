"""Module contains functions to activate an alarm.

For example, functions to send emails to IFTTT (for
interacting with smart devices) and functions to connect
to an Arduino.
"""

import time
import subprocess
import smtplib
import serial
import vlc

from config import SMTP_SERVER, SMTP_PORT, GMAIL_USERNAME, GMAIL_PASSWORD


def alarm(serial_connection):
    """Activate the alarm.

    Play music/radio, send 'wake up' message to Arduino, wait for
    message from Arduino to stop or snooze the alarm. Return
    'stop' or 'snooze'."""

    ser = serial_connection
    try:
        smartplug(True)
        smartlight('cool', 100)  # Turn on light (cool white, 100% brightness)
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
    # Send a message to Arduino to tell it to start sending 'stop'/'snooze'
    # on button presses
    ser.write("button\n".encode('utf-8'))
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            if line in ('stop', 'snooze'):
                # Stop alarm
                player.stop()
                smartplug(False)
                smartlight('off')
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
        session.quit()

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


def smartlight(mode, brightness=100):
    """Activate light by sending email."""
    options = {
        ('cool', 100): '#jason-light-cool-100',
        ('warm', 100): '#jason-light-warm-100',
        ('off', 100): '#jason-light-off'
    }
    return send_email(recipient='trigger@applet.ifttt.com',
        subject=options[(mode, brightness)])


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
