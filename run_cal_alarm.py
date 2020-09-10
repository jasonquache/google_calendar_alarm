"""The entry point for the Google Calendar Alarm program."""
from __future__ import print_function
import sys
import datetime
import time
import serial

from config import CALENDAR_ID
import alarm
import gcal as cal


def main():
    # Parse any command line arguments
    # At the moment, you can specify -v for verbose output
    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    verbose = False
    if "-v" in opts:
        verbose = True


    cal_service = cal.build_calendar()

    # Serial connection
    serial_service = alarm.connect_arduino()

    # Check every 0.5 seconds
    while True:
        # Try and get time of next event from calendar
        try:        
            next_wake_datetime, event_id = cal.get_next_event(cal_service, CALENDAR_ID, 'Wake', verbose)
            next_wake_datetime_tz = next_wake_datetime.tzinfo
            current_time = datetime.datetime.now(next_wake_datetime_tz)
            time_diff = next_wake_datetime - current_time

            if verbose:
                print("Next alarm start time: {}".format(next_wake_datetime))
                print("Current time: {}".format(current_time))
                print("Time difference: {}".format(time_diff))
                print("")

            threshold_time_diff = datetime.timedelta(seconds=10)
            zero_time = datetime.timedelta(seconds=0)

            # Send time until next alarm to Arduino via serial
            time_diff_list = str(time_diff).split(':')
            secs = time_diff_list[2].split('.')[0]
            # Hack to ensure the last char on LCD is cleared if required
            if len(time_diff_list[0]) > 1:
                msg = "Alarm: {}:{}:{} \n".format(time_diff_list[0], time_diff_list[1], secs)
            else:
                msg = "Alarm: {}:{}:{}  \n".format(time_diff_list[0], time_diff_list[1], secs)
            try:
                serial_service.write(msg.encode('utf-8'))
            except serial.serialutil.SerialTimeoutException:
                pass

            # Send current date/time to Arduino via serial
            # current_time_msg = current_time.strftime("Time: %a %d  %H:%M:%S\n")
            current_time_msg = current_time.strftime("Time: %a %d/%m  %H:%M\n")
            if verbose:
                print("CURRENT TIME ", current_time_msg)
            try:
                serial_service.write(current_time_msg.encode('utf-8'))
            except serial.serialutil.SerialTimeoutException:
                pass

            # Check if time to sound alarm
            if time_diff < threshold_time_diff and time_diff > zero_time:
                if verbose:
                    print("ALARM RAISED!")
                alarm_status = alarm.alarm(serial_connection=serial_service)
                
                if alarm_status == "stop":
                    # When alarm stopped, modify event summary of wake calendar event
                    # So it is not detected again
                    if verbose:
                        print("Stopped alarm")
                    cal.update_event_summary(service=cal_service, calendar_id=CALENDAR_ID,
                        event_id=event_id, new_summary="x")
                elif alarm_status == "snooze":
                    if verbose:
                        print("Snooze for 5 mins")
                    # https://stackoverflow.com/questions/8556398/generate-rfc-3339-timestamp-in-python/39418771#39418771
                    # 5 mins (300 secs) snooze time
                    snooze_time = (datetime.datetime.now(next_wake_datetime_tz) + datetime.timedelta(seconds=300)).isoformat()
                    cal.update_event_time(service=cal_service, calendar_id=CALENDAR_ID,
                        event_id=event_id, new_time=snooze_time)
        
        except Exception:
            # Assume HTTP error (backend error from Google Calendar)
            # TODO - change this to catch specific exception in future
            pass

        time.sleep(0.5)


if __name__ == "__main__":
    main()
