# Main.py - a voice assistance that wakes at it's name and can do simple tasks from verbal commands

# IMPORTS
from __future__ import print_function #must be at the beginning
import datetime
import pickle
import os.path
from random import random
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requestss import Request
import os
import time
import speech_recognition as sprec
import pyttsx3
import pytz
import sys
#? from neuralintents import GenericAssistant --> make smarter (exact phrase not needed)

# VARIABLES
# Name Ideas: JARVIS, Marvin, Alfred, Geoffrey, Niles (No's: Computer, Thing, Deep Thought, Brain, Lurch, Smithers)
WAKE = "Hex"
SERVICE = authenticate_google()
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
DAY_WORDS = [DAYS, MONTHS,OTHER_DAYS] #don't include ordinals
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
OTHER_DAYS = ['yesterday', 'tomorrow', "next day", "next week", "next month", "next year", 'the last day', 'the first day', "month", "week"]
ORDINAL_INDICATORS = ['st', 'nd', 'rd', 'th']
CALENDAR_STRS = ["what do i have", "do i have plans", "am i busy", "what am i doing"]
NOTE_STRS = ["make a note", "take a note", "note this down", "write this down", "remind me", "add to note"]
OPENING_GREETING = ["Yes?", "Hello", "How can I help?"]

# FUNCTIONS
## listening and answering functions
### DO NOT USE FOR ANSWERING (USE answer_and_log())
def read(text):
    '''allows program to read/speak a text'''
    reader = pyttsx3.init()
    reader.say(text)
    reader.runAndWait()


def get_audio():
    '''program listens to the mic, turns a command into
     a string called 'said', calls to log the conversation
     and then returns 'said'''
    try:
        recog = sprec.Recognizer()
        with sprec.Recognizer() as speech:
            audio = recog.listen(speech, timeout=3.0) # waits 3 seconds for command to start
            said = ""
            try:
                said = recog.recognize_google(audio)
                answer_and_log(said)
            except Exception as e:
                answer_and_log("Exception: " + str(e))
            return said.lower()
    except sprec.WaitTImeoutError:
        pass
    except sprec.UnknownValueError:
        pass
    except sprec.RequestError:
        answer_and_log("Sorry, I can't do that because I am not connected to the internet.")


## Logging Functions
def log_new_convo_start():
    now = str(datetime.datetime.now)
    with open("log.txt", "a") as f:
        opening_line = f"Conversation datetime: {now}.\n"
        f.write(opening_line)
        print(opening_line)


def log_commands(text):
    time = str(datetime.time.minute) + ":" + str(datetime.time.second)
    with open("log.txt", "a") as f:
        f.write(f"Heard: {text} at {time}.\n")


### USE FOR ANSWERING !!!
def answer_and_log(text):
    time = str(datetime.time.minute) + ":" + str(datetime.time.second)
    read(text)
    print(text)
    with open("log.txt", "a") as f:
        f.write(f"Answered: {text} at {time}.\n")


## google calendar functions - IMPROVE = make cred sep, 'the day after yesterday'erate
def open_gcal():
    '''Accesses Google Calendar'''
    cred = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            cred = pickle.load(token)
    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrects_file('credentials.json', SCOPES)
            cred = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('calendar', 'v3', credentials=cred)
    return service


#? vvvCHANGEvvv ???
def get_gcal_events(number_of_events, service):
    '''gets a list of the next n events on google calendar
    USE: "what?when is my next event?" etc '''
    now = datetime.datetime.utcnow().isoformat() + "Z" # Z = UTC time
    answer_and_log(f"Getting the next {number_of_events} upcoming events.")
    events_result = service.events().list(calendarId="primary",
                                          timeMin=now,
                                          maxResults=number_of_events,
                                          singleEvents=True.
                                          orderBy="starTime").execute()
    events = events_result.get('items', [])
    if not events:
        answer_and_log("No upcoming events found.")
    else:
        answer_and_log(f"Your next {len(events)} events are:")
        for event in events:
            start = event["start"].get("dateTime", event['start'].get('date'))
            #print(start, event['summary'])
            simplified_time = simplify_time(start)
            answer_and_log(event["summary"] + "at" + simplified_time)


#? vvvCHANGEvvv ???
def get_days_gcal_events(day, service):
    '''gets a list of the events of a certain day on google calendar
    USE: "What am I doing Sat?"/"Do I have plans Monday?" etc '''
    start_day = datetime.datetime.combine(day, datetime.datetime.min.time())
    end_day = datetime.datetime.combine(day, datetime.datetime.max.time())
    utc = pytz.UTC
    start_day = start_day.astimezone(utc)
    end_day = end_day.astimezone(utc)
    events_result = service.events().list(calendarId="primary",
                                               timeMin=start_day.isoformat(),
                                               timeMax=end_day.isoformat(),
                                               singleEvents=True.
                                               orderBy="starTime").execute()
    events = events_result.get('items', [])
    if not events:
        answer_and_log(f"You have no events for {day}.")
    else:
        answer_and_log(f"You have {len(events)} events for {day}")
        for event in events:
            start = event["start"].get("dateTime", event['start'].get('date'))
            #print(start, event['summary'])
            simplified_time = simplify_time(start)
            answer_and_log(event["summary"] + "at" + simplified_time)


## Note Functions
### Default lists = [To-Do, Shopping list, ]
def make_note(text, time):
    '''make a new note with the a time based name'''
    file_name = str(time).replace(":", "-") + "note.txt"
    with open(file_name, "w") as f:
        f.write(text)
    subprocess.Popen(["notepad.exe", file_name])


def add_to_note(text):
    '''open an existing note and add to it'''
    pass


def del_note():
    '''delete an existing note'''
    pass


def search_note():
    '''search all notes by name or date to answer bool'''
    pass


## Open things on web or local machine
def open_smthg(text):
    wsites = {"youtube": "https://www.youtube.com";
            "facebook": "https://www.facebook.com";
            "gmail": "https://www.gmail.com";
            "yahoo": "";
            "reddit": "";
            "pinterest": "";
            "bbc news": ""}
    local = {"downloads folder": "downloads path";
            "desktop": "desktop path";
            "external drive": "external path";}
    if wsites_keys in command:
        answer_and_log(f"Opening {key}")
        webbrowser.open(f"{website}")
    elif local_keys in command:
        answer_and_log(f"Opening {key}")
        os.startfile(f"{path}")
    elif "play music" in command:
        pass
    else:
        answer_and_log("Sorry, I don't know how to do that.")

## set timer
def set_timer():
    pass

def del_timer():
    pass

def change_timer():
    pass

def name_timer():
    pass

## Weather
def get_weather(date, place):
    '''finds the weather for a day & place and returns it'''
    pass

## Misc Functions
def simplify_time(time):
    """turns time into the in 12-hour format"""
    hour = str(time.split("T")[1].split("-")[0])
    min = str(time.split(":")[1])
    # make time into 12-hour clock
    if int(hour) < 12:
        time = str(f"{hour}:{min} am")
        time += "am"
    else:
        hour = int(hour) - 12
        time = str(f"{hour}:{min} pm")
    return time

def get_place(text):
    '''looks at the text of speech and identifies a place being used'''
    pass

def get_date(text):
    '''looks at text of speech and identifies a date being used'''
    today = datetime.date.today()
    '''if text contains 'today' it will return today's date'''
    if text.count("today") > 0: # Improve - this could trigger false run
        return today

    #Variables
    day = -1            # assigned = 1-31
    day_of_week = -1    # assigned = 0-6
    month = -1          # assigned = 1-12
    year = today.year       # Improve later to expand function

    '''make speech str a list and search words to figure out the date said'''
    for word in text.split():
        if word in MONTHS:
            month = MONTHS.index(word) + 1
        elif word in DAYS:
            day_of_week = DAYS.index(word)
        elif word.isdigit(): # Improve - this could trigger false run
            day = int(word)
        else:
            for oi in ORDINAL_INDICATORS:
                found = word.find(oi)
                try:
                    day = int(word[:found])
                except:
                    pass
    """ finds referenced but not stated days (assumes future)"""
    # if month is found and is less than current month than assign year to next year
    if month < today.month and month != -1:
        year += 1
    # if day is found and is passed the current day in the month than assign month to next month
    if day < today.day and month == -1 and day != -1:
        month += 1
    # if month & day are not assigned but day of the week is than find the difference from today
    if month == -1 and day == -1 and day_of_week != -1:
        todays_day_of_week = today.weekday()
        dif = day_of_week - todays_day_of_week
        # if day of the week is past the current day of the week than it is next week's
        if dif < 0:                         #meaning it's already happened
            dif +=7                         #to move to next week
            if text.count("next") >= 1:
                dif +=7                     #to move it another week because it's "next ___day"
        return today + datetime.timedelta(dif)      # add dif to today to return the wanted day
    #if date can't be found/isn't assigned
    if month == -1 or day == -1:
        return None
    return datetime.date(month=month, day=day, year=year)

# LOGIC - make into main function?
while True:
    text = get_audio()
    ## wake word
    if text.count(WAKE) > 0:
        log_new_convo_start()
        log_commands(text)
        answer_and_log(random(OPENING_GREETING))
        text = get_audio()

        ## dates/calendar
        for phrase in CALENDAR_STRS:
            if phrase in text.lower and (DAYS, MONTHS, ORDINAL_INDICATORS):
                date = get_date(text)
                if date:
                    answer_and_log(f"Looking at Calendar for {date}")
                    get_days_gcal_events(date, service)
                else:
                    answer_and_log("Please Try Again")

        ## notes
        for phrase in NOTE_STRS:
            # if note name is given
            #if no note name is given
            if phrase in text:
                answer_and_log("What note should I make?")
                note_txt = get_audio()      # comes lower
                answer_and_log("Is this a new note?")
                note_name = get_audio()     # comes lower
                # NO - find note by name given and add
                # YES - new note
                answer_and_log("Do you have a name for this note?")
                # NO- save with time as name as is default
                # YES - override name with name given (after checking name is free)

        ## timer
        ## tell weather
        ## google
        ## to-do ???
        ## open website/file on computer
            ## play music/video
