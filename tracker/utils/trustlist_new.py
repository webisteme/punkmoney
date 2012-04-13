from __future__ import division
import math

#G := set of users

G = [

    {'incoming'}



]


# Initialise

for p in G:
    p['auth'] = 1                           # p.auth is the authority score of the page p
    p['hub'] = 1                            # p.hub is the hub score of the page p

def HubsAndAuthorities(G):

    while i < 5:                            # run the algorithm for 5 steps
        norm = 0
        
        for p in G:                         # update all authority values first
            p['auth'] = 0
            
        for q in p['incoming']:       # p.incomingNeighbors is the set of pages that link to p
            p['auth'] += q['hub']    
            norm += p['auth']**2            # calculate the sum of the squared auth values to normalise
        
        norm = math.sqrt(norm)
        
        for p in G:                         # update the auth scores 
            p['auth'] = p['auth'] / norm    # normalise the auth values
        
        norm = 0
        
        for p in G:                         # then update all hub values
            p['hub'] = 0
        
        for r in p['outgoing']:       # p.outgoingNeighbors is the set of pages that p links to
            p['hub'] += r['auth']
            norm += p['hub']**2             # calculate the sum of the squared hub values to normalise
        
        norm = math.sqrt(norm)
        
        for p in G:                         # then update all hub values
            p['hub'] = p['hub'] / norm      # normalise the hub values
            
        i = i + 1