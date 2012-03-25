#!/usr/bin/python

"""

PunkMoney 1.0 :: Tracker.py 

Main listener class for finding and parsing #PunkMoney statements.

"""

from utils.parser import Parser

from time import sleep
import argparse

# Main Tracker class
class Tracker(Parser):

    def __init__(self):

        self.setupLogging()
        self.connectDB()
        self.TW = self.connectTwitter()
        
    def run(self):

        # Update expired
        try:
            self.updateExpired()
        except Exception, e:
            self.logError("Updatine expired failed: %s" % e)
        
        sleep(1)
        
        # If more than 25 hits remaining, harvest new tweets
        if self.TW.rate_limit_status()['remaining_hits'] > 25:
            try:        
                self.harvestNew()
            except Exception, e:
                self.logError("Harvester failed: %s" % e)
        else:
            self.logWarning("Skipping harvest, rate limit too low.")
            
        sleep(1)
        
        # Parse new
        try:
            self.parseNew()
        except Exception, e:
            self.logError("Parser failed: %s" % e)

'''
Run 
'''

if __name__ == '__main__':

    T = Tracker()

    parser = argparse.ArgumentParser(description='Run the #PunkMoney tracker')
    
    parser.add_argument('-e', action='store_true', dest='expired', default=False)
    parser.add_argument('-r', action='store_true', dest='harvest', default=False)
    parser.add_argument('-p', action='store_true', dest='parse', default=False)
    
    args = parser.parse_args()
            
    if args.expired or args.harvest or args.parse:
    
        if args.expired:
            T.updateExpired()
            
        if args.harvest:
            T.harvestNew()
            
        if args.parse:
            T.parseNew()
            
    else:
        T.run()
