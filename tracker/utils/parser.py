# -*- coding: utf-8 -*-
"""

PunkMoney 0.2 :: parser.py 

Main class for interpreting #PunkMoney statements.

"""

from mysql import Connection
from harvester import Harvester
from config import HASHTAG, ALT_HASHTAG, SETTINGS

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
                
                # Determine tweet type
                promise = re.search('promise', tweet['content'], re.IGNORECASE)
                transfer = re.search('transfer @(\w+)(.*)', tweet['content'], re.IGNORECASE)
                thanks = re.match('@(\w+) thanks (for)?(.*)', tweet['content'], re.IGNORECASE)
                offer = re.match('(i )?(offer[s]?) (.*)', tweet['content'], re.IGNORECASE)
                need = re.match('(i )?(need[s]?) (.*)', tweet['content'], re.IGNORECASE)
                close = re.match('@(\w+ )?close (.*)', tweet['content'], re.IGNORECASE)
                request = re.match('@(\w+ )(i )?request(.*)', tweet['content'], re.IGNORECASE)
                
                # If not recognised, exit here
                '''
                if not promise and not transfer and not thanks and not offer and not need and not close and not request:
                    self.setParsed(tweet['tweet_id'], '-')
                    raise Exception("Tweet was not recognised")
                '''
                
                # strip urls from text
                r = re.search("(.*)(?P<url>https?://[^\s]+)(.*)", tweet['content'], re.IGNORECASE)
                if r:
                    tweet['content'] = r.group(1) + ' ' + r.group(3) 
                
                # Parse tweet according to type
                
                if promise:
                    self.parsePromise(tweet)
                
                elif transfer:
                    tweet['to_user'] = transfer.group(1).lower()
                    self.parseTransfer(tweet)
                    
                elif thanks:
                    tweet['recipient'] = thanks.group(1)
                    if thanks.group(2):
                        if thanks.group(2).lower() == 'for':
                            tweet['message'] = thanks.group(3)
                    self.parseThanks(tweet)
    
                elif offer:
                    self.parseOffer(tweet)
                    
                elif need:
                    self.parseNeed(tweet)
    
                elif close:
                    self.parseClose(tweet)
    
                elif request:
                    tweet['recipient'] = request.group(1)
                    tweet['message'] = request.group(3)
                    self.parseRequest(tweet)
                    
                else:
                    self.setParsed(tweet['tweet_id'], '-')
                    raise Exception("Tweet was not recognised")
               
            except Exception, e:
                self.logWarning("Parsing tweet %s failed: %s" % (tweet['tweet_id'], e))
                self.setParsed(tweet['tweet_id'], '-')
                continue  
                 
    '''
    Parser functions
    '''
    
    # parsePromise
    # parses and saves a new promise
    def parsePromise(self, tweet):    
        try:
            # Tweet flag default true
            tweet_errors = True

            # Strip out hashtag
            h = re.search('(.*)(%s|%s)(.*)' % (HASHTAG, ALT_HASHTAG), tweet['content'], re.IGNORECASE)
            if h:
                statement = h.group(1) + h.group(3)
            else:
                raise Exception("Hashtag not found")
            
            # Get recipient
            r = re.search('(.*)@(\w+)(.*)', statement)
            
            if r:
                tweet['recipient'] = r.group(2)
                statement = r.group(1).strip() + r.group(3)
                self.saveUser(tweet['recipient'], intro=True)
                
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
                
            
            # Get condition
            c = re.match('(.*)( if )(.*)', statement, re.IGNORECASE)
            
            if c:
                tweet['condition'] = c.group(3)
            else:
                tweet['condition'] = None
        
        
            # Get promise
            p = re.match('(.*)(promise)(.*)', statement, re.IGNORECASE)
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
            self.setParsed(tweet['tweet_id'])
            self.createNote(tweet)
            self.createEvent(tweet['tweet_id'], tweet['tweet_id'], 0, tweet['created'], tweet['author'], tweet['recipient'])
            self.sendTweet('@%s promised @%s %s http://www.punkmoney.org/note/%s' % (tweet['author'], tweet['recipient'], promise, tweet['tweet_id']))
            self.logInfo('[Promise] @%s promised @%s %s.' % (tweet['author'], tweet['recipient'], tweet['tweet_id']))
            
        except Exception, e:
            self.logWarning("Processing promise %s failed: %s" % (tweet['tweet_id'], e))
            if tweet_errors is not False:
                self.sendTweet('@%s Sorry, your promise [%s] didn\'t parse. Try again: http://www.punkmoney.org/print/' % (tweet['author'], tweet['tweet_id']))
            self.setParsed(tweet['tweet_id'], '-')
            
            
    # parseTransfer
    # parse and save a transfer
    def parseTransfer(self, tweet):
        try:
            self.logInfo("Parsing tweet %s [transfer]" % tweet['tweet_id'])
            
            # Get issuer and recipient
            from_user = tweet['author']
            to_user = tweet['to_user']
            
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
        
            # Check recipient is trusted [Disabled]
            '''
            if self.checkTrusted(note['issuer'], to_user) is False:
                raise Exception("Transferee not trusted by issuer")
            '''
             
            self.saveUser(to_user, intro=True)
            
            # Process transfer
            self.setParsed(tweet['tweet_id'])
            self.updateNote(note['id'], 'bearer', to_user)
            self.createEvent(note['id'], tweet['tweet_id'], 3, tweet['created'], from_user, to_user)
            
            # Log transfer
            message = '[Transfer] @%s transferred %s to @%s' % (tweet['author'], note['id'], to_user)
            self.logInfo(message)
            self.setParsed(tweet['tweet_id'])
        except Exception, e:
            self.setParsed(tweet['tweet_id'], '-')
            self.logWarning("Processing transfer %s failed: %s" % (tweet['tweet_id'], e))
            
            
    # parseThanks
    # parse and save thanks
    def parseThanks(self, tweet):
        try:
            self.logInfo("Parsing tweet %s [thanks]" % tweet['tweet_id'])
            from_user = tweet['author']
            
            # If tweet has no reply to id
            if tweet['reply_to_id'] is None:
                h = re.search('(.*)(%s|%s)(.*)' % (HASHTAG, ALT_HASHTAG), tweet['message'], re.IGNORECASE)
                if h:
                    tweet['message'] = h.group(1).strip() + h.group(3).strip()
                
                self.createThanks(tweet)
                tweet['message'] = 'for ' + tweet['message']
                self.saveUser(tweet['recipient'], intro=True)
                
                # Log thanks
                message = '[Thanks] @%s thanked @%s %s' % (tweet['author'], tweet['recipient'], tweet['message'])
                self.logInfo(message)
                self.sendTweet('@%s thanked @%s %s http://www.punkmoney.org/note/%s' % (tweet['author'], tweet['recipient'], tweet['message'], tweet['tweet_id']))
                self.setParsed(tweet['tweet_id'])

            # If tweet has a reply_to_id, parse as redemption
            else:
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
                        
                message = note['promise']
                    
                # Process thanks
                self.updateNote(note['id'], 'status', 1)
                self.createEvent(note['id'], tweet['tweet_id'], 1, tweet['created'], from_user, to_user)
                
                # Log thanks
                message = '[Thanks] @%s thanked @%s for %s' % (to_user, from_user, message)
                self.logInfo(message)
                self.sendTweet('@%s thanked @%s for %s http://www.punkmoney.org/note/%s' % (to_user, from_user, note['promise'], message))
                self.setParsed(tweet['tweet_id'])
        except Exception, e:
            self.logWarning("Processing thanks %s failed: %s" % (tweet['tweet_id'], e))
            self.setParsed(tweet['tweet_id'], '-')

    
    # parseOffer
    # parse and save offers
    def parseOffer(self, tweet):
        try:
            # Strip out hashtag
            h = re.search('(.*)(%s|%s)(.*)' % (HASHTAG, ALT_HASHTAG), tweet['content'], re.IGNORECASE)
            if h:
                statement = h.group(1) + h.group(3)
            else:
                raise Exception("Hashtag not found")
            
            # Check expiry (optional)
            ''' 'Expires in' syntax '''
            
            e = re.search('(.*) Expires in (\d+) (\w+)(.*)', statement, re.IGNORECASE)
            
            if e:
                num = e.group(2)
                unit = e.group(3)
                tweet['expiry'] = self.getExpiry(tweet['created'], num, unit)
                statement = e.group(1) + e.group(4)
            else:
                tweet['expiry'] = None
            
            # Get thing offered/needed
            p = re.match('(.*)(offer[s]?)(.*)', statement, re.IGNORECASE)
            if p:
                if p.group(1).strip().lower() == 'i':
                    item = p.group(3)
                else:
                    item = p.group(1).strip() + p.group(3)
            else:
                raise Exception("Item not found")
                
            
            # Get condition
            c = re.match('(.*)( if )(.*)', item, re.IGNORECASE)
            if c:
                tweet['condition'] = c.group(3)
            else:
                tweet['condition'] = None
            
            
            # Clean up promise 
            '''
            Remove trailing white space, full stop and word 'you' (if found)
            '''
            
            item = item.strip()
            
            while item[-1] == '.':
                item = item[:-1]
            
            tweet['item'] = item
                
            self.createOffer(4, tweet)
            self.createEvent(tweet['tweet_id'], '0', 4, tweet['created'], tweet['author'], '')
            # Log and tweet promise
            self.sendTweet('[O] @%s offers %s http://www.punkmoney.org/note/%s' % (tweet['author'], item, tweet['tweet_id']))
            self.logInfo('[O] @%s offers %s.' % (tweet['author'], tweet['tweet_id']))
            self.setParsed(tweet['tweet_id'])
        except Exception, e:
            self.logWarning("Processing %s failed: %s" % (tweet['tweet_id'], e))
            self.sendTweet('@%s Sorry, your offer [%s] didn\'t parse. Try again: http://www.punkmoney.org/print/' % (tweet['author'], tweet['tweet_id']))
            self.setParsed(tweet['tweet_id'], '-')

    
    # parseNeed
    # parse and save offer
    def parseNeed(self, tweet):
        try:
            # Strip out hashtag
            h = re.search('(.*)(%s|%s)(.*)' % (HASHTAG, ALT_HASHTAG), tweet['content'], re.IGNORECASE)
            if h:
                statement = h.group(1) + h.group(3)
            else:
                raise Exception("Hashtag not found")
            
            # Check expiry (optional)
            ''' 'Expires in' syntax '''
            
            e = re.search('(.*) Expires in (\d+) (\w+)(.*)', statement, re.IGNORECASE)
            
            if e:
                num = e.group(2)
                unit = e.group(3)
                tweet['expiry'] = self.getExpiry(tweet['created'], num, unit)
                statement = e.group(1) + e.group(4)
            else:
                tweet['expiry'] = None
            
            # Get thing offered/needed
            p = re.match('(.*)(need[s])(.*)', statement, re.IGNORECASE)
            if p:
                if p.group(1).strip().lower() == 'i':
                    item = p.group(3)
                else:
                    item = p.group(1).strip() + p.group(3)
            else:
                raise Exception("Item not found")
                
            
            # Get condition
            c = re.match('(.*)( if )(.*)', item, re.IGNORECASE)
            if c:
                tweet['condition'] = c.group(3)
            else:
                tweet['condition'] = None
            
            
            # Clean up promise 
            '''
            Remove trailing white space, full stop and word 'you' (if found)
            '''
            
            item = item.strip()
            
            while item[-1] == '.':
                item = item[:-1]
            
            tweet['item'] = item

            self.createOffer(5, tweet)
            self.createEvent(tweet['tweet_id'], '0', 5, tweet['created'], tweet['author'], '')
            # Log and tweet promise
            self.sendTweet('[N] @%s needs %s http://www.punkmoney.org/note/%s' % (tweet['author'], item, tweet['tweet_id']))
            self.logInfo('[N] @%s needs %s.' % (tweet['author'], tweet['tweet_id']))
            self.setParsed(tweet['tweet_id'])
        except Exception, e:
            self.logWarning("Processing %s failed: %s" % (tweet['tweet_id'], e))
            self.sendTweet('@%s Sorry, your need [%s] didn\'t parse. Try again: http://www.punkmoney.org/print/' % (tweet['author'], tweet['tweet_id']))
            self.setParsed(tweet['tweet_id'], '-')

    # parseClose
    # parse and process a close statement
    def parseClose(self, tweet):
        try:
            # Check if this is a close instruction
            c = re.match('(.*)(close)(.*)', tweet['content'])
            
            # check tweet has a reply_to_id
            if c:
                if tweet.get('reply_to_id', False) is not False:
        
                    original_id = self.findOriginal(tweet['reply_to_id'], tweet['tweet_id'])
                    note = self.getNote(original_id)
                    
                    if tweet['author'].lower() != note['issuer']:
                        raise Exception("Close attempt by non-issuer")
                        
                    if note['status'] != 0:
                        raise Exception("Note already closed")
                    
                    self.updateNote(note['id'], 'status', 1)
                    
                    if note['type'] == 4:
                        code = 6
                    elif note['type'] == 5:
                        code = 7
                    elif note['type'] == 10:
                        code = 11
                    
                    self.createEvent(note['id'], tweet['tweet_id'], code, tweet['created'], tweet['author'], '')
                    self.logInfo("Closed note %s" % note['id'])
                    self.setParsed(tweet['tweet_id'])
                elif tweet.get('reply_to_id', False) is False:
                    self.setParsed(tweet['tweet_id'], '-')
                    raise Exception("Close failed: original not found")
        except Exception, e:
            self.logWarning("Processing %s failed: %s" % (tweet['tweet_id'], e))
            self.setParsed(tweet['tweet_id'], '-')

    # parseRequest
    # parse and process a request statement
    
    def parseRequest(self, tweet):
        try:
            h = re.search('(.*)(%s|%s)(.*)' % (HASHTAG, ALT_HASHTAG), tweet['message'], re.IGNORECASE)
            
            if h:
                tweet['message'] = h.group(1).strip() + h.group(3).strip()
                
            # Check not to self
            if tweet['recipient'].lower() == tweet['author'].lower():
                raise Exception("Issuer and recipient are the same")
    
            # Check expiry (optional)
            ''' 'Expires in' syntax '''
            
            e = re.search('(.*) Expires in (\d+) (\w+)(.*)', tweet['message'], re.IGNORECASE)
            
            if e:
                num = e.group(2)
                unit = e.group(3)
                tweet['expiry'] = self.getExpiry(tweet['created'], num, unit)
                tweet['message'] = e.group(1) + e.group(4)
            else:
                tweet['expiry'] = None
            
            # Clean up
            tweet['message'] = tweet['message'].strip()
            
            while tweet['message'][-1] == '.':
                tweet['message'] = tweet['message'][:-1]
    
            # Send intro tweet
            self.saveUser(tweet['recipient'].lower(), intro=True)
    
            # Create a request
            self.createRequest(tweet)
            
            # Log
            message = '[Request] @%s requested %s from @%s' % (tweet['author'], tweet['message'], tweet['recipient'])
            self.logInfo(message)
            self.sendTweet('[R] @%s requested %s from @%s http://www.punkmoney.org/note/%s' % (tweet['author'], tweet['message'], tweet['recipient'], tweet['tweet_id']))
            self.setParsed(tweet['tweet_id'])
        except Exception, e:
            self.logWarning("Parsing request %s failed: %s" % (tweet['tweet_id'], e))
            self.setParsed(tweet['tweet_id'], '-')


                    
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
            query = "SELECT created, id, issuer, promise, type FROM tracker_notes WHERE id = %s" % reply_to_id
            tweet = self.getRows(query)[0]
            return tweet
        try:
            note_types = [0, 4, 5, 10]
            
            print getLast(reply_to_id)[4]
            
            while int(getLast(reply_to_id)[4]) not in note_types:
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
                query = "INSERT INTO tracker_notes(id, issuer, bearer, promise, created, expiry, status, transferable, type, conditional) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                params = (tweet['tweet_id'], tweet['author'].lower(), tweet['recipient'].lower(), tweet['promise'], tweet['created'], tweet['expiry'], 0, tweet['transferable'], 0, tweet['condition'])
                self.queryDB(query, params)
            else:
                self.logWarning('Note %s already exists' % tweet['tweet_id'])
                return False
        except Exception, e:
            raise Exception("Creating note from tweet %s failed: %s" % (tweet['tweet_id'], e))
        else:
            return True
            
    # createOffer
    # Create an offer or need from parsed tweet
    def createOffer(self, code, tweet):
        try:
            query = "SELECT id FROM tracker_notes WHERE id = '%s'" % tweet['tweet_id']        
            if self.getSingleValue(query) is None:            
                query = "INSERT INTO tracker_notes(id, issuer, bearer, promise, created, expiry, status, transferable, type, conditional) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                params = (tweet['tweet_id'], tweet['author'].lower(), '', tweet['item'].lower(), tweet['created'], tweet['expiry'], 0, 0, code, tweet['condition'])
                self.queryDB(query, params)
            else:
                self.logWarning('Note %s already exists' % tweet['tweet_id'])
                return False
        except Exception, e:
            raise Exception("Creating note from tweet %s failed: %s" % (tweet['tweet_id'], e))
        else:
            return True
            
    # createThanks
    # Create a thanks note
    def createThanks(self, tweet):
        try:
            query = "SELECT id FROM tracker_notes WHERE id = '%s'" % tweet['tweet_id']        
            if self.getSingleValue(query) is None:            
                query = "INSERT INTO tracker_notes(id, issuer, bearer, promise, created, expiry, status, transferable, type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                params = (tweet['tweet_id'], tweet['author'].lower(), tweet['recipient'].lower(), tweet['message'], tweet['created'], None, 0, 0, 1)
                self.queryDB(query, params)
                # Create an event
                self.createEvent(tweet['tweet_id'],1,1,tweet['created'],tweet['author'].lower(), tweet['recipient'].lower())
            else:
                self.logWarning('Note %s already exists' % tweet['tweet_id'])
                return False
        except Exception, e:
            raise Exception("Creating thanks note from tweet %s failed: %s" % (tweet['tweet_id'], e))
        else:
            return True
            
    # createRequest
    # Create a request note
    def createRequest(self, tweet):
        try:
            query = "SELECT id FROM tracker_notes WHERE id = '%s'" % tweet['tweet_id']        
            if self.getSingleValue(query) is None:            
                query = "INSERT INTO tracker_notes(id, issuer, bearer, promise, created, expiry, status, transferable, type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                params = (tweet['tweet_id'], tweet['author'].lower(), tweet['recipient'].lower(), tweet['message'], tweet['created'], tweet['expiry'], 0, 0, 10)
                self.queryDB(query, params)
                # Create an event
                self.createEvent(tweet['tweet_id'],10,10,tweet['created'],tweet['recipient'].lower(), tweet['author'].lower())
            else:
                self.logWarning('Note %s already exists' % tweet['tweet_id'])
                return False
        except Exception, e:
            raise Exception("Creating thanks note from tweet %s failed: %s" % (tweet['tweet_id'], e))
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
            query = "SELECT id, issuer, bearer, promise, created, expiry, status, transferable, type FROM tracker_notes WHERE id = %s" % note_id
            note = self.getRows(query)[0]
            note = {'id' : note[0], 'issuer' : note[1], 'bearer' : note[2], 'promise' : note[3], 'created' : note[4], 'expiry' : note[5], 'status' : note[6], 'transferable' : note[7], 'type' : note[8]}
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
    def saveUser(self, username, intro = False):
        username = username.lower()
        try:
            query = "SELECT id FROM tracker_users WHERE username = '%s'" % username.lower()
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
                params = (username.lower())
                self.queryDB(query, params)
                
                # Send intro tweet
                if intro == True:
                    try:
                        message = '@' + username + ' Hi there. Someone just sent you #PunkMoney. Here\'s how to get started: http://is.gd/bezeyu' 
                        self.sendTweet(message)
                    except:
                        pass
                
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
            query = "SELECT id, bearer, issuer, type FROM tracker_notes WHERE expiry < now() AND status = 0"
            for note in self.getRows(query):
                self.logInfo('Note %s expired' % note[0])
                self.updateNote(note[0], 'status', 2)
                
                # promise
                if note[3] == 0:
                    code = 2
                # offer
                elif note[3] == 4:
                    code = 8
                # need
                elif note[3] == 5:
                    code = 9
                # request
                elif note[3] == 10:
                    code = 12

                
                self.createEvent(note[0], note[0], code, datetime.now(), note[2], note[1])
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
    # Check if there is a trust path between two users
    def checkTrusted(self,from_user, to_user):
        try:
            query = "SELECT COUNT(*) FROM tracker_events WHERE type = 1 AND from_user = '%s' AND to_user = '%s'" % (from_user, to_user)
            u = self.getSingleValue(query)
            print u
            if u > 0:
                return True
            else:
                return False
        except Exception, e:
            raise Exception('Checking TrustList for user %s failed: %s' % (username,e))