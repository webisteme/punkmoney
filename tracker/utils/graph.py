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
import numpy as np

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
    
    
        authorities = nx.pagerank(self.DG)
        
        # Normalise to 100
        max_user = max(authorities.iteritems(), key=operator.itemgetter(1))[0]
        max_val = authorities[max_user]
        
        r = 100/float(max_val)
        
        authorities_norm = {}
        
        for user,value in authorities.items():
        
            authorities_norm[user] = int(value * int(r))
            
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


