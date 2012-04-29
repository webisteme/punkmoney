#!/usr/bin/python
"""

PunkMoney 0.2 :: graph.py 

Calculates karma as PageRank in the thank-you graph.

"""

# Create a graph

import networkx as nx
from networkx.exception import NetworkXError
from mysql import Connection
from pprint import pprint
import math
import operator

class Karma(Connection):

    def __init__(self):
    
        self.DG = nx.DiGraph()
        self.setupLogging()
        self.connectDB()
    
    # Get graph data
    def populate(self):
    
        sql = "SELECT * FROM tracker_events WHERE type = 1"
        values = self.getRows(sql)
        
        for v in values:
            self.DG.add_edges_from([(v[6], v[5])])
    
    
    # Recalculate
    def recalculate(self):
    
    
        authorities = nx.hits(self.DG)[1]
        
        # Convert to log scale
        authorities_log = {}
        
        for user,value in authorities.items():
        
            v = value * 10**30
        
            if value > 0:
                v = math.log(v)
            else:
                v = 0
        
            authorities_log[user] = abs(int(v))
            
            
        # Normalise to 100
        authorities_norm = {}
        max_user = max(authorities_log.iteritems(), key=operator.itemgetter(1))[0]
        max_val = authorities_log[max_user]
        
        r = 100/float(max_val)
        
        for user,value in authorities_log.items():
            
            authorities_norm[user] = int(value*r)
 
        authorities_norm[max_user] = 100

        # Clear existing values
        
        sql = "UPDATE tracker_users set karma = 0"
        self.queryDB(sql, ())
        
        # Save values
        for user,karma in authorities_norm.items():
            sql = "UPDATE tracker_users SET karma = %s WHERE username = %s"
            self.queryDB(sql, (karma, user))
        
    
        

# Run script

K = Karma()
K.populate()
K.recalculate()


