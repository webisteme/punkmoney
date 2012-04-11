# -*- coding: utf-8 -*-
"""

PunkMoney 0.2 :: parser.py 

Main class for interpreting #PunkMoney statements.

"""

from mysql import Connection
from harvester import Harvester
from config import HASHTAG, SETTINGS

import re
from datetime import datetime
from dateutil.relativedelta import *
import time

'''
Parser class 
'''

class Parser(Harvester):

    def __init__(self):
        
        self.setupLogging()
        self.connectDB()
        self.TW = self.connectTwitter()
    
    '''
    Parse new tweets
    '''
    
    def parseNew(self):  
            
        # Process new tweets
        for tweet in self.getTweets():
            try:
                # If tweet contains 'RT' (e.g. is a retweet), skip
                retweet = False
                for w in tweet['content'].split():
                    if w == 'RT':
                        self.setParsed(tweet['tweet_id'])
                        raise Exception("Tweet is a retweet")
                        
                # Save tweet author to user database
                self.saveUser(tweet['author'])
                
                print tweet['content']
                
                # Determine tweet type
                promise = re.search('promise', tweet['content'], re.IGNORECASE)
                transfer = re.search('transfer @(\w+)(.*)%s' % HASHTAG, tweet['content'], re.IGNORECASE)
                redemption = re.match('@(\w+) redeemed(.*)(%s)' % HASHTAG, tweet['content'], re.IGNORECASE)
                
                # If not recognised, exit here
                if not promise and not transfer and not redemption:
                    self.setParsed(tweet['tweet_id'])
                    raise Exception("Tweet was not recognised")
                    
            except Exception, e:
                self.logWarning("Parsing tweet %s failed: %s" % (tweet['tweet_id'], e))
                self.setParsed(tweet['tweet_id'], '-')
                continue    
            
            '''
            Promise
            '''
            
            if promise:
                try:
                    # Tweet flag default true
                    tweet_errors = True
                    
                    # Set flag to parsed
                    self.setParsed(tweet['tweet_id'])
                    
                    # Strip out hashtag
                    h = re.search('(.*)(%s)(.*)' % HASHTAG, tweet['content'], re.IGNORECASE)
                    if h:
                        statement = h.group(1) + h.group(3)
                    else:
                        raise Exception("Hashtag not found")
                    
                    
                    # Get recipient
                    r = re.search('(.*)@(\w+)(.*)', statement)
                    
                    if r:
                        tweet['recipient'] = r.group(2)
                        
                        self.saveUser(tweet['recipient'])
                        statement = r.group(1).strip() + r.group(3)
                        
                    else:
                        # (Don't tweet this as an error)
                        tweet_errors = False;
                        raise Exception("Recipient not found")
                        
                    
                    # Check not to self
                    if tweet['recipient'] == tweet['author']:
                        raise Exception("Issuer and recipient are the same")
                        
                    # Check Transferability (optional)
                    t = re.match('(.*)( NT )(.*)', statement, re.IGNORECASE)
                    
                    if t:
                        tweet['transferable'] = False
                        statement = t.group(1) + t.group(3)
                    else:
                        tweet['transferable'] = True


                    # Check expiry (optional)
                    ''' 'Expires in' syntax '''
                    
                    e = re.match('(.*) Expires in (\d+) (\w+)(.*)', statement, re.IGNORECASE)
                    
                    if e:
                        num = e.group(2)
                        unit = e.group(3)
                        tweet['expiry'] = self.getExpiry(tweet['created'], num, unit)
                        statement = e.group(1) + e.group(4)
                    else:
                        tweet['expiry'] = None

                    ''' 'Exp in' syntax '''
                    
                    e = re.match('(.*) Exp in (\d+) (\w+)(.*)', statement, re.IGNORECASE)
                    
                    if e:
                        num = e.group(2)
                        unit = e.group(3)
                        tweet['expiry'] = self.getExpiry(tweet['created'], num, unit)
                        statement = e.group(1) + e.group(4)
                    else:
                        tweet['expiry'] = None



                    # Get promise
                    p = re.match('(.*)(promise)(.*)', statement)
                    if p:
                        if p.group(1).strip().lower() == 'i':
                            promise = p.group(3)
                        else:
                            promise = p.group(1).strip() + p.group(3)
                    else:
                        raise Exception("Promise not found")
                        
                    
                    # Clean up promise 
                    '''
                    Remove trailing white space, full stop and word 'you' (if found)
                    '''
                    
                    promise = promise.strip()
                    
                    while promise[-1] == '.':
                        promise = promise[:-1]
            
                    if promise[0:4] == 'you ':
                        promise = promise[4:]
                    
                    tweet['promise'] = promise
                    
                    # Processing promise
                    self.createNote(tweet)
                    self.createEvent(tweet['tweet_id'], tweet['tweet_id'], 0, tweet['created'], tweet['author'], tweet['recipient'])
                    
                    # Log and tweet promise
                    self.sendTweet('[P] @%s promised @%s %s http://www.punkmoney.org/note/%s' % (tweet['author'], tweet['recipient'], promise, tweet['tweet_id']))
                    self.logInfo('[Promise] @%s promised @%s %s.' % (tweet['author'], tweet['recipient'], tweet['tweet_id']))
                except Exception, e:
                    self.logWarning("Processing promise %s failed: %s" % (tweet['tweet_id'], e))
                    if tweet_errors is not False:
                        self.sendTweet('@%s Sorry, your promise [%s] didn\'t parse. Try again: http://www.punkmoney.org/print/' % (tweet['author'], tweet['tweet_id']))
                    self.setParsed(tweet['tweet_id'], '-')
                    continue

                    
                
            '''
            Transfer
            '''    
            
            if transfer:
                try:
                    self.logInfo("Parsing tweet %s [transfer]" % tweet['tweet_id'])
                    
                    # Get author and recipient
                    from_user = tweet['author']
                    to_user = transfer.group(1).lower()
                    
                    # Create user
                    self.saveUser(to_user)
                    
                    # If issuer and recipient are the same, skip
                    if from_user == to_user:
                        raise Exception("Issuer and recipient are the same")

                    # Find original tweet this is a reply to
                    original_id = self.findOriginal(tweet['reply_to_id'], tweet['tweet_id'])
                    
                    # Check note exists
                    if original_id is None:
                        raise Exception("Original note could not be found")
                    
                    # Get original note
                    note = self.getNote(original_id)
                    
                    # Check transferer is current bearer
                    if from_user != note['bearer']:
                        raise Exception("User %s is not the current note bearer" % from_user)
                        
                    # Check note is open (i.e. not expired or redeemed)
                    if note['status'] != 0:
                        if note['status'] == 1:
                            raise Exception("Note has already been redeemed")
                        if note['status'] == 2:
                            raise Exception("Note has expired")
                        
                    # Check note is transferable
                    if note['transferable'] != 1:
                        raise Exception("Note is non-transferable")

                    # Check recipient is trusted
                    if self.checkTrusted(to_user) is False:
                        raise Exception("Recipient not in TrustList")
                    
                    # Process transfer
                    self.setParsed(tweet['tweet_id'])
                    self.updateNote(note['id'], 'bearer', to_user)
                    self.createEvent(note['id'], tweet['tweet_id'], 3, tweet['created'], from_user, to_user)
                    
                    # Log transfer
                    message = '[Transfer] @%s transferred %s to @%s' % (tweet['author'], note['id'], to_user)
                    self.logInfo(message)
                    self.setParsed(tweet['tweet_id'])
                except Exception, e:
                    self.setParsed(tweet['tweet_id'], val=2)
                    self.logWarning("Processing transfer %s failed: %s" % (tweet['tweet_id'], e))
                    self.setParsed(tweet['tweet_id'], '-')
                    continue
                    
            '''
            Redemption
            '''
            
            if redemption:
                try:
                    self.logInfo("Parsing tweet %s [redemption]" % tweet['tweet_id'])
                    
                    from_user = tweet['author']
    
                    # Find original tweet this is a reply to
                    original_id = self.findOriginal(tweet['reply_to_id'], tweet['tweet_id'])
                    note = self.getNote(original_id)
                    
                    to_user = note['issuer']
                    
                    # Check original exists
                    if note is False:
                        raise Exception("Original note not found")
                    
                    # Check tweet author is current bearer
                    if note['bearer'] != from_user:
                        raise Exception("User is not the current note bearer")
                        
                    # Check note is open (i.e. not expired or redeemed)
                    if note['status'] != 0:
                        if note['status'] == 1:
                            raise Exception("Note has already been redeemed")
                        if note['status'] == 2:
                            raise Exception("Note has expired")
                        
                    # Process redemption
                    self.updateNote(note['id'], 'status', 1)
                    self.createEvent(note['id'], tweet['tweet_id'], 1, note['created'], from_user, to_user)
                    
                    # Add karma
                    self.addKarma(to_user)
                    
                    # Log redemption
                    message = '[Redemption] @%s redeemed %s from @%s' % (to_user, note['id'], from_user)
                    self.logInfo(message)
                    self.sendTweet('[R] @%s redeemed %s from @%s http://www.punkmoney.org/note/%s' % (to_user, note['promise'], from_user, note['id']))
                    self.setParsed(tweet['tweet_id'])                    
                except Exception, e:
                    self.logWarning("Processing redemption %s failed: %s" % (tweet['tweet_id'], e))
                    self.setParsed(tweet['tweet_id'], '-')
                    continue
                    
    '''
    Helper functions
    '''
    # getTweets
    # Get unparsed tweets from database
    def getTweets(self):
        try:
            tweets = []
            for tweet in self.getRows("SELECT timestamp, tweet_id, author, content, reply_to_id FROM tracker_tweets WHERE parsed is Null ORDER BY timestamp ASC"):
                tweet = {'created' : tweet[0], 'tweet_id' : tweet[1], 'author' : tweet[2], 'content' : tweet[3], 'reply_to_id' : tweet[4]}
                tweets.append(tweet)
        except Exception, e:
            raise Exception("Getting tweets from database failed: %s" % e)
            return tweets
        else:
            return tweets
    
    # setParsed
    # Set parsed flag to 1 if successful, or '-' if not
    def setParsed(self, tweet_id, val=1):
        try:
            query = "UPDATE tracker_tweets SET parsed = %s WHERE tweet_id = %s"
            self.queryDB(query, (val, tweet_id))
        except Exception, e:
            raise Exception("Setting parsed flag for tweet %s failed: %s" % (tweet_id, e))
        else:
            return True
            
    # getExpiry
    # Takes created date time, a number and unit (day, week, month, year,) & returns expiry datetime
    def getExpiry(self, created, num, unit):
        try:
            num = int(num)
            if unit == 'minutes' or unit == 'minute':
                expiry = created + relativedelta(minutes=+num)
            if unit == 'hours' or unit == 'hour':
                expiry = created + relativedelta(hours=+num)
            if unit == 'days' or unit == 'day':
                expiry = created + relativedelta(days=+num)
            if unit == 'weeks' or unit == 'week':
                expiry = created + relativedelta(days=+7*num)
            if unit == 'months' or unit == 'month':
                expiry = created + relativedelta(months=+num)
            if unit == 'years' or unit == 'year':
                expiry = created + relativedelta(years=+num)
        except Exception, e:
            raise Exception("Calculating expiry date failed: %s" % e)
        else:
            return expiry
    
    # findOriginal
    # Given a reply_to_id, finds the original 
    def findOriginal(self, reply_to_id, tweet_id):
        tweet = {}
        def getLast(reply_to_id):
            query = "SELECT timestamp, tweet_id, author, content, reply_to_id FROM tracker_tweets WHERE tweet_id = %s" % reply_to_id
            tweet = self.getRows(query)[0]
            return tweet
        try:
            while getLast(reply_to_id)[4] is not None:
                reply_to_id = getLast(reply_to_id)[4]
            else:
                tweet = getLast(reply_to_id)
        except Exception, e:
            raise Exception("Original note for id %s not found" % tweet_id)
        else:
            return tweet[1]
    
    # createNote
    # Create a new note from a parsed tweet
    def createNote(self, tweet):
        try:
            query = "SELECT id FROM tracker_notes WHERE id = '%s'" % tweet['tweet_id']        
            if self.getSingleValue(query) is None:            
                query = "INSERT INTO tracker_notes(id, issuer, bearer, promise, created, expiry, status, transferable) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                params = (tweet['tweet_id'], tweet['author'].lower(), tweet['recipient'].lower(), tweet['promise'], tweet['created'], tweet['expiry'], 0, tweet['transferable'])
                self.queryDB(query, params)
            else:
                self.logWarning('Note %s already exists' % tweet['tweet_id'])
                return False
        except Exception, e:
            raise Exception("Creating note from tweet %s failed: %s" % (tweet['tweet_id'], e))
        else:
            return True
    
    # createEvent
    # Create an event
    def createEvent(self, note_id, tweet_id, typ, timestamp, from_user, to_user):
        from_user = from_user.lower()
        to_user = to_user.lower()
        try:
            query = "SELECT id FROM tracker_events WHERE tweet_id = '%s' AND note_id = '%s'" % (tweet_id, note_id)
            if self.getSingleValue(query) is None:                
                query = "INSERT INTO tracker_events(note_id, tweet_id, type, timestamp, from_user, to_user) VALUES (%s, %s, %s, %s, %s, %s)"
                params = (note_id, tweet_id, typ, timestamp, from_user, to_user)
                self.queryDB(query, params)
            else:
                self.logWarning("Event %s already exists" % tweet_id)
                return False
        except Exception, e:
            raise Exception("Creating event for tweet %s failed: %s" % (tweet_id, e))
        else:
            return True
    
    # getNote
    # Return a note given its id    
    def getNote(self, note_id):
        try:
            query = "SELECT id, issuer, bearer, promise, created, expiry, status, transferable FROM tracker_notes WHERE id = %s" % note_id
            note = self.getRows(query)[0]
            note = {'id' : note[0], 'issuer' : note[1], 'bearer' : note[2], 'promise' : note[3], 'created' : note[4], 'expiry' : note[5], 'status' : note[6], 'transferable' : note[7]}
        except Exception, e:
            raise Exception("Original note %s not found" % (note_id, e))
            return False
        else:
            return note
    
    # updateNote
    # Update a note
    def updateNote(self, note_id, field, value):
        try:
            query = "UPDATE tracker_notes SET %s = %s where id = %s" % (field, '%s', '%s')
            params = (value, note_id)
            self.queryDB(query, params)
        except Exception, e:
            raise Exception("Updating note %s failed: %s" % (note_id, e))
        else:
            return True

    # saveUser
    # Check user exists
    def saveUser(self, username):
        username = username.lower()
        try:
            query = "SELECT id FROM tracker_users WHERE username = '%s'" % username
            r = self.getSingleValue(query)
        except Exception, e:
            self.logError("Checking user exists failed: %s" % e)
            return False
        try:
            if r:
                return True
            else:
                self.logInfo("Saving new user %s" % username)
                query = "INSERT INTO tracker_users (username) VALUES (%s)"
                params = (username)
                self.queryDB(query, params)
                # Follow user
                try:
                    if self.TW.exists_friendship('punk_money', username) is False:
                        self.TW.create_friendship(username)
                except:
                    pass
        except Exception, e:
            raise Exception("Creating new user failed: %s" % e)
        else:
            return True
        
    # updateExpired
    # Update status of any expired notes
    def updateExpired(self):
        try:
            self.logInfo("Checking for expirations")
            query = "SELECT id, bearer, issuer FROM tracker_notes WHERE expiry < now() AND status = 0"
            for note in self.getRows(query):
                self.logInfo('Note %s expired' % note[0])
                self.updateNote(note[0], 'status', 2)
                self.createEvent(note[0], note[0], 2, datetime.now(), note[2], note[1])
        except Exception, e:
            raise Exception("Cleaning database failed: %s" % e)
            
    # sendTweet
    # Tweet a message from the main account
    def sendTweet(self, message):
        if SETTINGS.get('tweet', False) is True:
            try:
                self.TW.update_status(message)
            except:
                self.logError("Tweeting message failed (%s)" % message)
                
                
    # checkTrusted
    # Check if a user is in the TrustList
    def checkTrusted(self,username):
        try:
            query = "SELECT id FROM tracker_trust_list WHERE trusted = '%s'" % username
            u = self.getSingleValue(query)
            if u is not None:
                return True
            else:
                return False
        except Exception, e:
            raise Exception('Checking TrustList for user %s failed: %s' % (username,e))
            
            
    # addKarma
    # Add karma to specified user
    def addKarma(self, user):
        self.logDebug("Adding karma for user %s" % user)
        try:
            query = "UPDATE tracker_users SET karma = karma + 1 WHERE username = %s"
            self.queryDB(query, user)
        except Exception, e:
            self.logError("There was an error adding karma for user %s: %s" % (user, e))