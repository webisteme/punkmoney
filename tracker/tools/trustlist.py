#!/usr/bin/python

"""

PunkMoney 0.2 :: trustlist.py 

Class for recursively crawling a #Punkmoney trustlist.

"""

from parser import Parser
from config import SEED_USER, LIST_NAME

class TrustList(Parser):

    def __init__(self):
    
        self.TW = self.connectTwitter()
        self.setupLogging()
        self.connectDB()

    # buildList
    def buildList(self):
    
        self.log_info('Rebuilding TrustList...')
    
        global trust_list
        global new_list
        global checked
        
        trust_list = []
        new_list = []
        checked = []
        i = 1
    
        users = self.TW.list_members(SEED_USER,LIST_NAME)[0]
        
        for user in users:
            trust_list.append({'user' : SEED_USER, 'trusted' : user.screen_name})
            checked.append(SEED_USER)
    
        # crawl deeper
        new_list = self.crawlDeeper(trust_list)
        while len(new_list) > 0 : new_list = self.crawlDeeper(new_list)
        
        # update database
        try:
            query = "delete from tracker_trust_list where id > 0"
            self.queryDB(query, {})
        except:
            raise Exception('Deleting tracker_trust_list failed')
        else:
            for pair in trust_list:
                user = str(pair['user'].lower())
                trusted = str(pair['trusted'].lower())
                sql = "insert into tracker_trust_list(user, trusted) values(%s, %s)"
                self.queryDB(sql, (user, trusted))
            self.log.info('TrustList rebuilt successfully')
            
            
    # crawlDeeper
    # Checks for a trust list for each member in a provided list
    def crawlDeeper(self, trust_list):
        i = 0
        new_list[:] = []
        for pair in trust_list:
            self.logDebug('checking %s' % pair['trusted'])
            self.save_user(pair['user'])
            self.save_user(pair['trusted'])
            
            # If this user's list hasn't been checked, add it
            if pair['trusted'] not in checked:
            
                checked.append(pair['trusted'])
                
                try:
                    candidates = self.TW.list_members(pair['trusted'], LIST_NAME)[0]
                    
                    for candidate in candidates:
                        self.logDebug('--checking candidate %s' % candidate.screen_name)
                        trust_list.append({'user' : pair['trusted'], 'trusted' : candidate.screen_name})
                        new_list.append({'user' : pair['trusted'], 'trusted' : candidate.screen_name})
                        
                except:
                    continue

        return new_list
        

             
        
        
        
        
        
# Run

T = TrustList()

if T.TW.rate_limit_status()['remaining_hits'] > 50:
    T.buildList()
else:
    T.log_error("Crawl failed: remaining hits too low")