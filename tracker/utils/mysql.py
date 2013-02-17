"""

PunkMoney 0.2 :: mysql.py

MySQL database connection class.

"""

# Imports

import os
import sys
import MySQLdb

from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

# Main connection class

class Connection():

    def __init__(self):
        """Empty constructor; takes no argument"""
        return
    
    # connectDB
    # Creates a database connection
    def connectDB(self):
        #self.log_info("Connecting to the database")
        self.db = MySQLdb.connect(
            MYSQL_HOST, 
            MYSQL_USER, 
            MYSQL_PASSWORD, 
            MYSQL_DATABASE,
            charset = "utf8", 
            use_unicode = True,
        )
        self.cursor = self.db.cursor()
        
    # Get single value
    # Fetches and returns a single value   
    def getSingleValue(self, query):
        try:
            self.cursor.execute(query)
            value = self.cursor.fetchone()
        except Exception, e:
            raise Exception("Error querying database: %s" % e)
        else:
            if value is not None:
                return value[0]
            else:
                return None
                
    # Get rows
    # Fetches and returns rows of data
    def getRows(self, query):
        try:
            self.cursor.execute(query)
            value = self.cursor.fetchall()
        except Exception, e:
            raise Exception("Error querying database: %s" % e)
        else:
            if value is ():
                return {} 
            elif value is not None:
                return value
    
    # queryDB
    # Sends a query to database
    def queryDB(self, query, params):
        try:
            self.cursor.execute(query, params)
            self.db.commit()
        except Exception, e:
            raise Exception("Error querying database: %s" % e)
        else:
            return True            
            
            
            
            
            
            
            
            
    
    