#!/usr/bin/python

"""

fixdb - inverts to_user and from_user in db

"""

from utils.parser import Parser

from time import sleep
import argparse

# Main Tracker class
class FixMe(Parser):

    def __init__(self):

        self.setupLogging()
        self.connectDB()
        self.TW = self.connectTwitter()
        
    def clean(self):
    
        sql = "SELECT id, from_user, to_user FROM tracker_events WHERE type = 1"
        tweets = self.getRows(sql)
        
        for t in tweets:
        
            self.logInfo("Updating row %s" % t[0])
        
            sql_1 = "UPDATE tracker_events SET to_user = %s WHERE id = %s" 
            sql_2 = "UPDATE tracker_events SET from_user = %s WHERE id = %s"
            
            self.queryDB(sql_1, (t[1], t[0]))
            self.queryDB(sql_2, (t[2], t[0]))
            
            
f = FixMe()
f.clean()