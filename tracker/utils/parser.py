# -*- coding: utf-8 -*-
"""

PunkMoney 0.2 :: parser.py 

Main class for interpreting #PunkMoney statements.

"""

''' Import Django models '''

import sys, os
from datetime import *

os.environ['DJANGO_SETTINGS_MODULE'] ='web.settings'

from django.core.management import setup_environ
from django.db.models import Q
import networkx as nx

from web import settings as django_settings
from web.tracker.models import *

setup_environ(django_settings)

# from mysql import Connection
from harvester import Harvester
from config import HASHTAG, ALT_HASHTAG, SETTINGS
# from objects import Event

import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from dateutil.relativedelta import *
import time

'''
Parser class 
'''

class Parser(Harvester):

    def __init__(self):
        self.setupLogging()
        # self.connectDB()
        self.TW = self.connectTwitter()
    
    '''
    Parse new tweets
    '''
    
    def parse_new(self):

        #self.getTweets()

        test_tweets = [
            {'content' : "@webisteme promise this test NT Expires 2013-03-01 http://www.google.com. #testmoney", 
            'tweet_id' : 32, 
            'author' : 3, 
            'created' : datetime.now()}
        ]
            
        # Process new tweets
        for tweet in test_tweets:
            try:
                # If tweet contains 'RT' (i.e. is a retweet), skip -- ! use regex
                retweet = False
                for w in tweet['content'].split():
                    if w == 'RT':
                        self.set_parsed(tweet['tweet_id'], False)
                        raise Exception("Tweet is a retweet")
                        
                # Save tweet author to user database
                #self.save_user(tweet['author'])
                
                # Remove hashtag and any URLs from content
                tweet['content'] = re.sub('(%s|%s)' % (HASHTAG, ALT_HASHTAG), '', tweet['content'])
                tweet['content'] = re.sub("(?P<url>https?://[^\s]+)", '', tweet['content'])
                
                # Match tweet content against RegEx to determine statement type
                '''
                is_promise = re.search('promise ', tweet['content'], re.IGNORECASE)
                is_transfer = re.search('transfer @(\w+)(.*)', tweet['content'], re.IGNORECASE)
                is_thanks = re.search('@(\w+) thanks (for)?(.*)', tweet['content'], re.IGNORECASE)
                is_offer = re.search('(i )?(offer[s]?) (.*)', tweet['content'], re.IGNORECASE)
                is_need = re.search('(i )?(need[s]?) (.*)', tweet['content'], re.IGNORECASE)
                is_close = re.match('@(\w+ )?close (.*)', tweet['content'], re.IGNORECASE)
                is_request = re.search('@(\w+ )(i )?request (.*)', tweet['content'], re.IGNORECASE)
                '''
            
                tweet_type = self.get_tweet_type(tweet['content'])
                
                if tweet_type:
                    return eval('self.parse_' + tweet_type)(tweet)
                else:
                    raise Exception("Type not found")  

            except Exception, e:
                self.log_warning("Processing tweet %s failed: %s" % (tweet['tweet_id'], e))
                self.set_parsed(tweet['tweet_id'], False)
                continue  
                 
    '''
    Parser functions
    '''
    
    # parse_promise
    # parses and saves a new promise
    def parse_promise(self, tweet):
        try:
            # Recipient
            r = re.search('@(\w+)(.*)', tweet['content'])

            if r:
                recipient = r.group(1)
                statement = r.group(2)
                tweet['recipient'] = self.save_user(recipient)
            else:
                raise Exception("Recipient not found")

            # Check not to self
            if int(tweet['recipient']) == int(tweet['author']):
                raise Exception("Issuer and recipient are the same")

            # Transferability (optional)
            t = re.match('(.* )(NT.|NT)(.*)', statement, re.IGNORECASE)
            
            if t:
                tweet['transferable'] = False
                statement = t.group(1) + t.group(3)
            else:
                tweet['transferable'] = True

            # Expiry (optional)
            ''' 'Expires in' an 'Expires' syntaxes '''
            
            expires = re.match('(.*) Expires (\d+-\d+-\d+)(.*)', statement, re.IGNORECASE)
            expires_in = re.match('(.*) Expires in (\d+) (\w+)(.*)', statement, re.IGNORECASE)

            if expires:
                expiry = expires.group(2)
                tweet['expiry'] = date_parser.parse(expiry)
                statement = expires.group(1) + expires.group(3)
            elif expires_in:
                num = expires_in.group(2)
                time_unit = expires_in.group(3)
                tweet['expiry'] = self.calculate_expiry(tweet['created'], num, time_unit)
                statement = expires_in.group(1) + expires_in.group(4)
            else:
                tweet['expiry'] = None

            # Condition (optional)
            c = re.match('(.*)( if )(.*)', statement, re.IGNORECASE)

            if c:
                tweet['condition'] = c.group(3)
            else:
                tweet['condition'] = None
        
            # Promise
            p = re.match('(.*)( promise )(.*)', statement, re.IGNORECASE)
            
            if p:
                if p.group(1).strip().lower() == 'i':
                    promise = p.group(3)
                else:
                    promise = p.group(1).strip() + p.group(3)
            else:
                raise Exception("Promise not found")
            
            # Tidy up promise string 
            promise = promise.strip()
            
            while promise[-1] == '.':
                promise = promise[:-1]

            if promise[0:4] == 'you ':
                promise = promise[4:]
            
            tweet['promise'] = promise

        except Exception, e:
            self.log_info("Promise %s could not be parsed" % tweet['tweet_id'])
            self.set_parsed(tweet['tweet_id'], False)
            return False
        else:
            return tweet
            
            
    # parseTransfer
    # parse and save a transfer
    def parse_transfer(self, tweet):
        try:
            self.log_info("Parsing tweet %s [transfer]" % tweet['tweet_id'])
            
            # Get issuer and recipient
            from_user = tweet['author']
            to_user = tweet['to_user']
            
            # Create user
            self.save_user(to_user)
            
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
             
            self.save_user(to_user, intro=True)
            
            # Process transfer
            self.set_parsed(tweet['tweet_id'])
            self.updateNote(note['id'], 'bearer', to_user)
            
            # Create event
            E = Event(note['id'], tweet['tweet_id'], 3, tweet['created'], from_user, to_user)
            E.save()
            
            # Log transfer
            self.log_info('[Tr] @%s transferred %s to @%s' % (tweet['author'], note['id'], to_user))
            self.set_parsed(tweet['tweet_id'])
        except Exception, e:
            self.set_parsed(tweet['tweet_id'], False)
            self.log_warning("Processing transfer %s failed: %s" % (tweet['tweet_id'], e))
            
            
    # parseThanks
    # parse and save thanks
    def parseThanks(self, tweet):
        try:
            self.log_info("Parsing tweet %s [thanks]" % tweet['tweet_id'])
            from_user = tweet['author']
            
            # If tweet has no reply to id
            if tweet['reply_to_id'] is None:
                h = re.search('(.*)(%s|%s)(.*)' % (HASHTAG, ALT_HASHTAG), tweet['message'], re.IGNORECASE)
                if h:
                    tweet['message'] = h.group(1) + h.group(3).strip()
                
                self.createThanks(tweet)
                tweet['message'] = 'for ' + tweet['message']
                self.save_user(tweet['recipient'], intro=True)
                
                # Log thanks
                message = '[Thanks] @%s thanked @%s %s' % (tweet['author'], tweet['recipient'], tweet['message'])
                self.log_info(message)
                self.sendTweet('@%s thanked @%s %s http://www.punkmoney.org/note/%s' % (tweet['author'], tweet['recipient'], tweet['message'], tweet['tweet_id']))
                self.set_parsed(tweet['tweet_id'])

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
                
                E = Event(note['id'], tweet['tweet_id'], 1, tweet['created'], from_user, to_user)
                E.save()
                
                # Log thanks
                self.log_info('[T] @%s thanked @%s for %s' % (to_user, from_user, message))
                
                # Tweet event
                self.sendTweet('@%s thanked @%s for %s http://www.punkmoney.org/note/%s' % (from_user, to_user, note['promise'], note['id']))
                self.set_parsed(tweet['tweet_id'])
                
        except Exception, e:
            self.log_warning("Processing thanks %s failed: %s" % (tweet['tweet_id'], e))
            self.set_parsed(tweet['tweet_id'], False)

    
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
            
            # Create event
            E = Event(tweet['tweet_id'], '0', 4, tweet['created'], tweet['author'], '')
            E.save()
            
            # Log event
            self.log_info('[O] @%s offers %s.' % (tweet['author'], tweet['tweet_id']))
            
            # Tweet event
            self.sendTweet('[O] @%s offers %s http://www.punkmoney.org/note/%s' % (tweet['author'], item, tweet['tweet_id']))
            self.set_parsed(tweet['tweet_id'])
        except Exception, e:
            self.log_warning("Processing %s failed: %s" % (tweet['tweet_id'], e))
            self.sendTweet('@%s Sorry, your offer [%s] didn\'t parse. Try again: http://www.punkmoney.org/print/' % (tweet['author'], tweet['tweet_id']))
            self.set_parsed(tweet['tweet_id'], False)

    
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
            p = re.match('(.*)(need[s]?)(.*)', statement, re.IGNORECASE)
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
            
            # Create event
            E = Event(tweet['tweet_id'], '0', 5, tweet['created'], tweet['author'], '')
            E.save()
            
            # Log event
            self.log_info('[N] @%s needs %s.' % (tweet['author'], tweet['tweet_id']))
            
            # Tweet
            self.sendTweet('[N] @%s needs %s http://www.punkmoney.org/note/%s' % (tweet['author'], item, tweet['tweet_id']))
            self.set_parsed(tweet['tweet_id'])
        except Exception, e:
            self.log_warning("Processing %s failed: %s" % (tweet['tweet_id'], e))
            self.sendTweet('@%s Sorry, your need [%s] didn\'t parse. Try again: http://www.punkmoney.org/print/' % (tweet['author'], tweet['tweet_id']))
            self.set_parsed(tweet['tweet_id'], False)

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
                    
                    # Create event
                    E = Event(note['id'], tweet['tweet_id'], code, tweet['created'], tweet['author'], '')
                    E.save()
                    
                    # Log event
                    self.log_info("[X] '%s' closed note %s" % (tweet['author'], note['id']))
                    self.set_parsed(tweet['tweet_id'])
                elif tweet.get('reply_to_id', False) is False:
                    self.set_parsed(tweet['tweet_id'], False)
                    raise Exception("Close failed: original not found")
        except Exception, e:
            self.log_warning("Processing %s failed: %s" % (tweet['tweet_id'], e))
            self.set_parsed(tweet['tweet_id'], False)

    # parseRequest
    # parse and process a request statement
    
    def parseRequest(self, tweet):
    
        # If request is a reply, create from note
        if tweet.get('reply_to_id', None) is not None:  
            try:
                note = self.getNote(tweet['reply_to_id'])
                
                if note['type'] != 4:
                    raise Exception("Request not in reply to an offer")
                
                tweet['recipient'] = note['issuer']
    
                if note['type'] == 10:
                    if note['bearer'].strip() != tweet['author'].strip():
                        raise Exception('Promise issued by non-bearer')
                    else:
                        tweet['issuer'] = tweet['author']
                else:
                    tweet['issuer'] = tweet['author']
                
                tweet['message'] = note['promise']
                
                # Check expiry (optional)
                ''' 'Expires in' syntax '''
                
                e = re.match('(.*) Expires in (\d+) (\w+)(.*)', tweet['content'], re.IGNORECASE)
    
                if e:
                    num = e.group(2)
                    unit = e.group(3)
                    tweet['expiry'] = self.getExpiry(tweet['created'], num, unit)
                else:
                    tweet['expiry'] = None
            except:
                raise Exception("Processing request as reply failed")
        else:
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
            except:
                raise Exception("Processing request failed")
        try:
            # Send intro tweet
            self.save_user(tweet['recipient'].lower(), intro=True)
    
            # Create a request
            self.createRequest(tweet)
            
            # Log
            self.log_info('[R] @%s requested %s from @%s' % (tweet['author'], tweet['message'], tweet['recipient']))
            self.sendTweet('[R] @%s requested %s from @%s http://www.punkmoney.org/note/%s' % (tweet['author'], tweet['message'], tweet['recipient'], tweet['tweet_id']))
            self.set_parsed(tweet['tweet_id'])
        except Exception, e:
            self.log_warning("Parsing request %s failed: %s" % (tweet['tweet_id'], e))
            self.set_parsed(tweet['tweet_id'], False)


                    
    '''
    Helper functions
    '''
    # getTweets
    # Get unparsed tweets from database
    def getTweets(self):
        try:
            tweets = []
            for tweet in self.getRows("SELECT timestamp, tweet_id, author, content, reply_to_id FROM tracker_tweets WHERE parsed is Null ORDER BY timestamp ASC"):
                tweet = {
                    'created' : tweet[0], 
                    'tweet_id' : tweet[1], 
                    'author' : tweet[2], 
                    'content' : tweet[3], 
                    'reply_to_id' : tweet[4]
                }
                tweets.append(tweet)
        except Exception, e:
            raise Exception("Getting tweets from database failed: %s" % e)
            return tweets
        else:
            return tweets
    
    # set_parsed
    # Set parsed flag to 1 if successful, or False if not
    def set_parsed(self, tweet_id, val = True):

        if SETTINGS.get('debug', False) == True:
            return False
        try:
            tweet = Tweet.objects.get(tweet_id = tweet_id)
            tweet.parsed = val
            tweet.save()
        except Exception, e:
            raise Exception("Setting parsed flag for tweet %s failed: %s" % (tweet_id, e))
        else:
            return True
            
    # calculate_expiry
    # Takes created date time, a number and unit (day, week, month, year,) & returns expiry as datetime
    def calculate_expiry(self, created, num, unit):
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
            
            while int(getLast(reply_to_id)[4]) not in note_types:
                reply_to_id = getLast(reply_to_id)[4]
            else:
                tweet = getLast(reply_to_id)
        except Exception, e:
            raise Exception("Original note for id %s not found" % tweet_id)
        else:
            return tweet[1]
    
    # create_note
    # Create a new note from a parsed tweet
    def create_note(self, tweet, note_type):
        note = Note.objects.filter(id = tweet['tweet_id'])
        # Create new note if does not exist
        if len(note) == 0: 
            self.log_info("Creating new note from %s" % tweet['tweet_id'])
            note = Note(
                id = tweet['tweet_id'],
                issuer = tweet['author'],   
                bearer = tweet['recipient'],
                promise = tweet['promise'],
                created = tweet['created'],       
                expiry = tweet['expiry'],
                type = note_type,
                transferable = tweet['transferable'],
                status = 0,
                condition = tweet['condition']
            )
            note.save()
        else:
            self.log_warning('Note %s already exists' % tweet['tweet_id'])
            
    # create_event
    # Create a new event from a parsed tweet
    def create_event(self, tweet, event_type):
        event = Event.objects.filter(tweet_id = tweet['tweet_id'])
        # Create new event if does not exist
        if len(event) == 0:
            self.log_info("Creating new event from %s" % tweet['tweet_id'])
            event = Event(
                note_id = tweet['tweet_id'],
                tweet_id = tweet['tweet_id'],
                type = event_type,
                timestamp = tweet['created'],
                from_user = tweet['author'],
                to_user = tweet['recipient']
            ) 
            event.save()
        else:
            self.log_warning('Event %s already exists' % tweet['tweet_id'])
            
    # createOffer
    # Create an offer or need from parsed tweet
    def createOffer(self, code, tweet):
        try:
            query = "SELECT id FROM tracker_notes WHERE id = '%s'" % tweet['tweet_id']        
            if self.getSingleValue(query) is None:            
                query = "INSERT INTO tracker_notes(id, issuer, bearer, promise, created, expiry, status, transferable, type, condition) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                params = (tweet['tweet_id'], tweet['author'].lower(), '', tweet['item'].lower(), tweet['created'], tweet['expiry'], 0, 0, code, tweet['condition'])
                self.queryDB(query, params)
            else:
                self.log_warning('Note %s already exists' % tweet['tweet_id'])
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
                E = Event(tweet['tweet_id'],1,1,tweet['created'],tweet['author'], tweet['recipient'])
                E.save()
            else:
                self.log_warning('Note %s already exists' % tweet['tweet_id'])
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
                E = Event(tweet['tweet_id'],10,10,tweet['created'], tweet['author'], tweet['recipient'])
                E.save()
            else:
                self.log_warning('Note %s already exists' % tweet['tweet_id'])
                return False
        except Exception, e:
            raise Exception("Creating thanks note from tweet %s failed: %s" % (tweet['tweet_id'], e))
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

    # save_user
    # Check user exists
    def save_user(self, user, intro = False):
        try:

            if type(user) is str or type(user) is unicode:
                #twitter_id = self.TW.get_user(user).id
                twitter_id = 17024753
            else:
                twitter_id = user

            # Create new user if doesn't exist already
            try:
                user = User.objects.get(twitter_id = twitter_id)
            except:
                #username = self.TW.get_user(twitter_id).screen_name
                username = 'webisteme'
                
                self.log_info("Creating user %s" % username)
                
                user = User()
                user.twitter_id = twitter_id
                user.username = username
                user.save()
                
                # Try following user
                try:
                    if self.TW.exists_friendship('punk_money', username) is False:
                        self.TW.create_friendship(username)
                except:
                    pass

            # Return user id
            return int(twitter_id)

        except Exception, e:
            raise Exception("Creating new user failed: %s" % e)
        else:
            return True
        
    # updateExpired
    # Update status of any expired notes
    def updateExpired(self):
        try:
            self.log_info("Checking for expirations")
            query = "SELECT id, bearer, issuer, type FROM tracker_notes WHERE expiry < now() AND status = 0"
            for note in self.getRows(query):
                self.log_info('Note %s expired' % note[0])
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
                
                # Create event
                E = Event(note[0], 0, code, datetime.now(), note[2], note[1])
                E.save()
                
        except Exception, e:
            raise Exception("Cleaning database failed: %s" % e)
            
    # sendTweet
    # Tweet a message from the main account
    def sendTweet(self, message):
        if SETTINGS.get('tweet', False) is True:
            try:
                self.TW.update_status(message)
            except:
                self.log_error("Tweeting message failed (%s)" % message)      
                
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
            
    # get_tweet_type
    # returns statement type from Tweet content
    
    def get_tweet_type(self, content):
        try:
            tweet_types = ['promise', 'transfer', 'thanks', 'offer', 'need', 'close', 'request']
            for tweet_type in tweet_types:
                vars()['is_' + tweet_type] = re.search(tweet_type + ' ', content, re.IGNORECASE)
                if eval('is_' + tweet_type):
                    return tweet_type
            # if no matches, return False
            return False
        except Exception, e:
            raise Exception("Tweet type could not be determined: %s" % e)
                    
            
    # getTwitterId
    # Get twitter_id from username tracker users. Add user if not already there
    
    def getTwitterId(self, username):
        try:
            sql = "SELECT twitter_id FROM tracker_users WHERE username = %s"
            twitter_id = self.getSingleValue(sql, username)
            if twitter_id is not None:  
                return twitter_id
            else:
                self.save_user(username)
                sql = "SELECT twitter_id FROM tracker_users WHERE username = %s"
                twitter_id = self.getSingleValue(sql, username)
                if twitter_id is not None:  
                    return twitter_id
        except:
            raise Exception("Twitter ID not found for user")
    
    
    
    
    
    