#!/usr/bin/python

"""

PunkMoney 0.2 :: Configuration File

"""

# COMMUNITY
'''
Currency hashtag, name of trustlist and seed_user to crawl from (no '@'). Must be lowercase!

Please use a different hashtag for testing.

'''

HASHTAG = '#testmoney'
ALT_HASHTAG = '#tmny'


# TWITTER API CREDENTIALS
'''
Register an app with read/write access at http://dev.twitter.com.
'''

TW_CONSUMER_KEY = 'eCRj53Ut41Pbo2BcvVyQuQ'
TW_CONSUMER_SECRET = 'eOW5SwN2u3Q9rab2i3H8Sv1xOj188mkOZo6NHoiz8'

TW_ACCESS_KEY = '398204399-I7JmCT9rIirv1BNtmmrqUVlQRRf86TT1gGc8Rt97'
TW_ACCESS_SECRET = 'fPHe8HGMBN3pgxtFBQipzrLjkxVqdKm6SRNKacGDM'

# LOG PATH
'''
Absolute path to a log file in /tracker/logs
'''

LOG_PATH = '/Users/Eli/Documents/punkmoney0.2/tracker/logs/punkmoney.log'


# MYSQL DATABASE
'''
MySQL database credentials. Socket locations can vary depending on the system.
'''

MYSQL_HOST = 'localhost'
MYSQL_USER = 'punkmoney'
MYSQL_DATABASE = 'punkmoney2'
MYSQL_PASSWORD = '12673013'
MYSQL_SOCKET = '/tmp/mysql.sock'


# SETTINGS
''' 
Set tweet to true to tweet syntax errors via the main Twitter account.
Set debug to true to log debug messages
TWIPM tweets a weekly summary of activity in the tracker.
'''

SETTINGS = {
    'tweet' : False,
    'debug' : False,
    'twipm' : False,
}