# -*- coding: utf-8 -*-
"""

PunkMoney 0.2 :: objects.py 

Classes for events and notes objects.

"""

from mysql import Connection
from harvester import Harvester
from config import HASHTAG, ALT_HASHTAG, SETTINGS

import re
from datetime import datetime
from dateutil.relativedelta import *
import time

"""
Event 

"""

class Event(Connection):

    def __init__(self, note_id, tweet_id, typ, timestamp, from_user, to_user = None):
        
        self.connectDB()
        
        # Event codes and types
        self.event_types = {
            0 : 'promise',
            1 : 'thanks',
            2 : 'promise expired', 
            3 : 'transfer',
            4 : 'offer',
            5 : 'need',
            6 : 'offer closure',
            7 : 'need closure',
            8 : 'offer expired',
            9 : 'need expired',
            10 : 'request',
            11 : 'request closure',
            12 : 'request expired',
        }
        
        # Parameters for this event
        self.note_id = note_id
        self.tweet_id = tweet_id
        self.typ = typ 
        self.timestamp = timestamp
        self.from_user = from_user.lower()
        self.to_user = to_user.lower()
    
    # save
    # Validates and saves event to the database
    def save(self):
        try:
            query = "SELECT id FROM tracker_events WHERE tweet_id = '%s' AND note_id = '%s'" % (self.tweet_id, self.note_id)
            if self.getSingleValue(query) is None:                
                query = "INSERT INTO tracker_events(note_id, tweet_id, type, timestamp, from_user, to_user) VALUES (%s, %s, %s, %s, %s, %s)"
                params = (self.note_id, self.tweet_id, self.typ, self.timestamp, self.from_user, self.to_user)
                self.queryDB(query, params)
            else:
                raise Exception("Event already exists")
        except Exception, e:
            raise Exception("Creating event for tweet %s failed: %s" % (self.tweet_id, e))
        else:
            return True

