#!/usr/bin/python

"""

PunkMoney 0.2 :: twipm.py 

This Week in #PunkMoney. Creates a tweet summarising the last week's activity.

"""

from parser import Parser
from config import SETTINGS
import time
from datetime import datetime

from time import sleep
import argparse

# Main Tracker class
class Twipm(Parser):

    def __init__(self):

        self.setupLogging()
        self.connectDB()
        self.TW = self.connectTwitter()
        
    def run(self):

        if SETTINGS['twipm'] == False:
            return False

        # Get data

        limit = int(time.time()) - (7 * 24 * 60 * 60) - 1
        limit_date = datetime.fromtimestamp(limit)

        events = { 
            'thanks' : 1,
            'promises' : 0,
            'transfers' : 3,
            'offers': 4,
            'needs': 5,
            'requests' : 10,
        }
        
        count = {}
        for key, value in events.items():
            query = "SELECT count(*) FROM tracker_events WHERE type = %s AND timestamp > '%s'" % (value, limit_date)
            count[key] = int(self.getSingleValue(query))
        
        # Prepare tweet

        tweet = 'This Week in #PunkMoney:'
        
        i = 0
        for key, value in count.items():
            if value > 0:
                tweet += ' %s %s,' % (value, key)
                i = i+1;
                
        tweet = tweet[:-1]

        tweet += '. See you next week http://www.punkmoney.org.'
        
        # Tweet if more than one value
        
        if i > 0:
            self.sendTweet(tweet)
        
        
T = Twipm()

T.run()
        
    

