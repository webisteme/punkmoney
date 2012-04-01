#!/usr/bin/python

"""

PunkMoney 0.2 :: Configuration File

"""

# COMMUNITY
'''
Currency hashtag, name of trustlist and seed_user to crawl from (no '@').
'''

HASHTAG = '#punkmoney'
LIST_NAME = 'punkmoney-trusted'
SEED_USER = 'webisteme'


# TWITTER API CREDENTIALS
'''
Register an app with read/write access at http://dev.twitter.com.
'''

TW_CONSUMER_KEY = ''
TW_CONSUMER_SECRET = ''

TW_ACCESS_KEY = ''
TW_ACCESS_SECRET = ''

# LOG PATH
'''
Absolute path to a log file in /tracker/logs
'''

LOG_PATH = ''


# MYSQL DATABASE
'''
MySQL database credentials. Socket locations can vary depending on the system.
'''

MYSQL_HOST = 'localhost'
MYSQL_USER = ''
MYSQL_DATABASE = ''
MYSQL_PASSWORD = ''
MYSQL_SOCKET = '/tmp/mysql.sock'


# SETTINGS
''' 
Set tweet to true to tweet syntax errors via the main Twitter account.
Set debug to true to log debug messages
'''

SETTINGS = {
    'tweet' : False,
    'debug' : False,
}