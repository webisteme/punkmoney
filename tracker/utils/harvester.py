"""

PunkMoney 0.2 :: harvester.py 

Main listener class for finding and saving #PunkMoney statements.

"""

from mysql import Connection
from config import TW_CONSUMER_KEY, TW_CONSUMER_SECRET, TW_ACCESS_KEY, TW_ACCESS_SECRET, HASHTAG, ALT_HASHTAG

import tweepy
from datetime import datetime
import sys
import urllib2
from urllib import urlencode
import simplejson
from pprint import pprint
from logger import Logging

class Harvester(Logging):
    
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
                tweets = self.TW.search(HASHTAG, since_id = lastID)
                tweets_alt = self.TW.search(ALT_HASHTAG, since_id = lastID)
                tweets = tweets + tweets_alt
            else:
                tweets = self.TW.search(HASHTAG)
                tweets_alt = self.TW.search(ALT_HASHTAG)
                tweets = tweets + tweets_alt
            
            # Save to DB
            i = 0
            for tweet in tweets:

                # Double check tweet isn't duplicate
                query = "SELECT tweet_id FROM tracker_tweets WHERE tweet_id = %s" % tweet.id
                
                if self.getSingleValue(query) is None:
                
                    # Get tweet metadata
                    t = self.TW.get_status(tweet.id)
                    
                    # Extract first img_url
                    img_url = None
                    for media_entity in t.entities.get('media',[]):
                        if media_entity.get('type', None) == 'photo':
                            img_url = media_entity.get('media_url', None)

                    # Extract first url
                    url = None; display_url = None
                    for url_entity in t.entities.get('urls', []):
                        url = url_entity.get('expanded_url', None)
                        display_url =  url_entity.get('display_url', None)    
                        
                    # Extract hashtags. (Defaults are None)
                    k = 0
                    tags = [None, None, None]
                    for hashtag in t.entities.get('hashtags', []):
                    
                        tag = hashtag.get('text').lower()
                    
                        if tag != HASHTAG[1:] and tag != ALT_HASHTAG[1:] and k <= 2:
                            tags[k] = tag
                            k = k + 1

                    reply_to_id = t.in_reply_to_status_id
                    
                    # Get tag IDs
                    k = 0
                    tag_ids = [None, None, None]
                    for tag in tags:
                        if tag is not None:
                            query = "SELECT id FROM tracker_tags WHERE tag = '%s'" % tag
                            while self.getSingleValue(query) is None:
                                new_tag = "INSERT INTO tracker_tags (tag) VALUES (%s)"
                                self.queryDB(new_tag, (tag))
                            else:
                                tag_ids[k] = self.getSingleValue(query)
                            k = k + 1

                    # Save data
                    self.logInfo("Saving tweet %s to database" % tweet.id)

                    query = "INSERT INTO tracker_tweets (timestamp, tweet_id, author, content, reply_to_id, url, display_url, img_url, tag_1, tag_2, tag_3) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    params = (tweet.created_at, tweet.id, tweet.user.screen_name.lower(), tweet.text, reply_to_id, url, display_url, img_url, tag_ids[0], tag_ids[1], tag_ids[2])
                           
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
    
    
    
    
    
    
    
    
    
    
    
            
