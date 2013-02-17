#!/usr/bin/python

"""

PunkMoney 0.2 :: redemptions.py (Experimental)

Class for checking redemptions made via favouriting original tweet.

(This is a naive approach. More work is needed to scale.)

    - This could be improved by checking each user once for all their open notes
    - Parser tweet message needs to be added too

"""

from parser import Parser
from config import SEED_USER, LIST_NAME
from datetime import datetime

class Redemptions(Parser):

    def __init__(self):
    
        self.TW = self.connectTwitter()
        self.setupLogging()
        self.connectDB()

    # buildList
    def harvest(self):
    
        self.log_info('Checking for new redemptions')
        self.log_info('Twitter rate limit: %s' % self.TW.rate_limit_status()['remaining_hits'])
            
        # Get current bearers of all open notes
        sql = "SELECT id, bearer FROM tracker_notes WHERE status = 0";
        notes = R.getRows(sql)
                
        for note in notes:
        
            print note
        
            # Exit if rate limit below 30
            if self.TW.rate_limit_status()['remaining_hits'] < 30:
                self.log_warning("Rate limit too low (%s), exiting." % R.TW.rate_limit_status()['remaining_hits'])
                break
        
            try:
                note_id = note[0]
                bearer = note[1]
                
                # Get favourites for this user
                favourites = self.TW.favorites(bearer, note_id)
                
                # Check if original tweet was favourited
                for f in favourites:
                
                    print f.id
                               
                    if f.id == note_id:
                    
                        print 'match'

                        issuer = f.author.screen_name
                        
                        self.updateNote(note_id, 'status', 1)
                        self.createEvent(note_id, 0, 1, datetime.now(), issuer, bearer)
                        
                        # Log
                        message = '[Redemption] @%s redeemed %s from @%s' % (bearer, note_id, issuer)
                        self.log_info(message)
                        
            except Exception, e:
                self.log_error("Checking redemption failed for note %s: %s" % (note_id, e))
                    
        # Exit
        self.log_info('Finished checking redemptions')
        self.log_info('Twitter rate limit: %s' % self.TW.rate_limit_status()['remaining_hits'])
        
        
        
        
        
# Run

R = Redemptions()

if R.TW.rate_limit_status()['remaining_hits'] > 50:
    R.harvest()
else:
    R.log_error("Redemption check failed: remaining hits too low")