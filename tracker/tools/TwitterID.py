#!/usr/bin/python

"""

PunkMoney 0.2 :: Tracker.py 

Main listener class for finding and parsing #PunkMoney statements.

"""

from tracker.utils.parser import Parser

from time import sleep
import argparse

# Main Tracker class
class TwitterID(Parser):

    def __init__(self):

        self.setupLogging()
        self.connectDB()
        self.TW = self.connectTwitter()
        
    ''' Add twitter ids to user table '''
    
    def update_ids(self):

        sql = "SELECT * FROM tracker_users WHERE twitter_id = 0"
        users = self.getRows(sql)
        
        for user in users:
            
            username = user[1]
            user_id = int(user[0])
            
            self.log_info("Updating user %s" % username)
        
            try:
                user_info = self.TW.get_user(username)
                twitter_id = user_info.id

                sql = "UPDATE tracker_users SET twitter_id = %s WHERE id = %s"
                #self.queryDB(sql, (twitter_id, user_id))
            
            except Exception, e:
                self.log_error("Error updating user %s" % user_id)
                continue
        
    ''' Replace table usernames with twitter_ids '''
            
    def update_events(self):
        
        ''' Events table '''
        
        sql = "SELECT * FROM tracker_events"
        events = self.getRows(sql)
        
        for event in events:

            event_id = event[0]
            from_user = event[5]
            to_user = event[6]
            
            self.log_info("Updating event %s" % event_id)
        
            # look up from id
            sql = "SELECT twitter_id FROM tracker_users WHERE username = '%s'" % from_user
            from_user_id = self.getSingleValue(sql)
            
            # look up to id
            sql = "SELECT twitter_id FROM tracker_users WHERE username = '%s'" % to_user
            to_user_id = self.getSingleValue(sql)
            
            sql = "UPDATE tracker_events SET from_user = %s, to_user = %s WHERE id = %s"
            self.queryDB(sql, (from_user_id, to_user_id, event_id))
            
            
    def update_notes(self):
        
        ''' Notes table '''
        
        sql = "SELECT * FROM tracker_notes"
        notes = self.getRows(sql)
        
        for note in notes:

            note_id = note[0]
            issuer = note[1]
            bearer = note[2]
            
            self.log_info("Updating note %s" % note_id)
        
            # look up from id
            sql = "SELECT twitter_id FROM tracker_users WHERE username = '%s'" % issuer
            issuer_id = self.getSingleValue(sql)
            
            # look up to id
            sql = "SELECT twitter_id FROM tracker_users WHERE username = '%s'" % bearer
            bearer_id = self.getSingleValue(sql)
            
            # do update
            sql = "UPDATE tracker_notes SET issuer = %s, bearer = %s WHERE id = %s"
            self.queryDB(sql, (issuer_id, bearer_id, note_id))
            
            
    def update_tweets(self):
        
        ''' Notes table '''
        
        sql = "SELECT * FROM tracker_tweets"
        tweets = self.getRows(sql)
        
        for tweet in tweets:

            tweet_id = tweet[0]
            author = tweet[1]
            
            if author is not None:
         
                self.log_info("Updating tweet %s" % tweet_id)
            
                # look up from id
                sql = "SELECT twitter_id FROM tracker_users WHERE username = '%s'" % author
                author_id = self.getSingleValue(sql)
                
                # do update
                sql = "UPDATE tracker_tweets SET author = %s WHERE tweet_id = %s"
                self.queryDB(sql, (author_id, tweet_id))
            

        
            

'''
Run 
'''

if __name__ == '__main__':

    T = TwitterID()
 
    '''
    T.update_ids()
    T.update_events()
    T.update_notes()
    T.update_tweets()
    '''