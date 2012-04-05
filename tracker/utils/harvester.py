"""

PunkMoney 0.2 :: harvester.py 

Main listener class for finding and saving #PunkMoney statements.

"""

from mysql import Connection
from config import TW_CONSUMER_KEY, TW_CONSUMER_SECRET, TW_ACCESS_KEY, TW_ACCESS_SECRET, HASHTAG

import tweepy
from datetime import datetime

class Harvester(Connection):
    
    def __init__(self):
        
        self.setupLogging()
        self.connectDB()
        self.TW = self.connectTwitter()
        
    # Harvest
    # Fetches and saves latest tweets from Twitter API
    def harvestNew(self):
        
        self.logInfo("Harvesting new tweets...")
        
        try:
            # Get latest tweets
            query = "SELECT max(tweet_id) FROM tracker_tweets"
            lastID = self.getSingleValue(query)
            
            if lastID is not None:
                tweets_p = self.TW.search(HASHTAG + ' promise', since_id = lastID)
                tweets_t = self.TW.search(HASHTAG + ' transfer', since_id = lastID)
                tweets_r = self.TW.search(HASHTAG + ' redeemed', since_id = lastID)
                tweets = tweets_p + tweets_t + tweets_r
            else:
                tweets_p = self.TW.search(HASHTAG + ' promise')
                tweets_t = self.TW.search(HASHTAG + ' transfer')
                tweets_r = self.TW.search(HASHTAG + ' redeemed')
                tweets = tweets_p + tweets_t + tweets_r
            
            # Save to DB
            i = 0
            for tweet in tweets:
            
                # Double check tweet isn't duplicate
                query = "SELECT tweet_id FROM tracker_tweets WHERE tweet_id = %s" % tweet.id
                
                if self.getSingleValue(query) is None:
                
                    # Check for a reply_to_id
                    t = self.TW.get_status(tweet.id)
                    reply_to_id = t.in_reply_to_status_id
                
                    # Save data
                    self.logInfo("Saving tweet %s to database" % tweet.id)
                    
                    query = "INSERT INTO tracker_tweets (timestamp, tweet_id, author, content, reply_to_id) VALUES (%s, %s, %s, %s, %s)"
                    params = (tweet.created_at, tweet.id, tweet.from_user.lower(), tweet.text, reply_to_id)     
                               
                    self.queryDB(query, params)
                    
                    i = i + 1
                
        except Exception, e:
            self.logError("Twitter harvest failed: %s" % e)
        else:
            if i > 0:
                self.logInfo("Saved %s new tweets to the database" % i)
            else:
                self.logInfo("No new tweets found")
                
    
    '''
    Helper methods.
    '''

    # Connects to Twitter API. Returns a Twitter API instance
    def connectTwitter(self):
        try:
            auth = tweepy.OAuthHandler(TW_CONSUMER_KEY, TW_CONSUMER_SECRET)
            auth.set_access_token(TW_ACCESS_KEY, TW_ACCESS_SECRET)
            api = tweepy.API(auth)
        except Exception, e:
            raise Exception("Error connecting to Twitter API: %s" % e)
        else:
            return api
            
